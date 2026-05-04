from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from app.core.evaluators.llm_judge import LLMJudgeEvaluator
from app.core.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.core.models.registry import EvaluationRegistry
from tests.conftest import ErrorProvider


# Replaces duplicated evaluator registration that was copy-pasted in each test.
@pytest.fixture(autouse=True)
def _register_evaluators(
    registry: EvaluationRegistry,
    error_provider: Callable[[Exception], ErrorProvider],
) -> None:
    """Registers rule_based and a failing llm_judge before every test in this module."""
    failing = LLMJudgeEvaluator(error_provider(Exception("Mock provider failure")), 0.5, timeout=30)
    registry.register(failing.name, failing)

    rule = RuleBasedEvaluator(0.4, timeout=30)
    registry.register(rule.name, rule)


# Replaces duplicated request payloads — only the llm_judge weight varied between tests.
def _make_partial_failure_request(llm_judge_weight: int = 1) -> list[dict]:
    return [
        {
            "model_output": "Hello, World!",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": 1,
                    "threshold": 0.4,
                    "config": {
                        "rules": [
                            {
                                "name": "keyword",
                                "kind": "required",
                                "keyword": "World",
                                "weight": 1.0,
                            }
                        ]
                    },
                },
                {
                    "evaluator_id": "llm_judge",
                    "weight": llm_judge_weight,
                    "threshold": 0.5,
                    "config": {
                        "prompt": "How can I eat bananas most efficiently?",
                        "rubric": [
                            "correctness: is the advice factually correct?",
                            "clarity: is the explanation easy to understand?",
                            "politeness: is the tone appropriate and polite?",
                        ],
                    },
                },
            ],
        }
    ]


def test_evaluate_partial_failure_rule_based_and_llm_judge(
    client_with_registry: TestClient,
) -> None:
    response = client_with_registry.post("/evaluate", json=_make_partial_failure_request())

    assert response.status_code == 200
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is True
    assert eval_result["failure_count"] == 1
    assert eval_result["weighted_average_score"] == pytest.approx(1.0)

    rule_based_result = eval_result["results"][0]
    llm_judge_result = eval_result["results"][1]

    assert rule_based_result["passed"] is True
    assert rule_based_result["normalised_score"] == pytest.approx(1.0)
    assert rule_based_result["error"] is None

    assert llm_judge_result["passed"] is False
    assert llm_judge_result["normalised_score"] == 0
    assert llm_judge_result["error"] is not None


def test_evaluate_partial_failure_excludes_failed_evaluator_weight(
    client_with_registry: TestClient,
) -> None:
    response = client_with_registry.post("/evaluate", json=_make_partial_failure_request(llm_judge_weight=5))

    assert response.status_code == 200
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is True
    assert eval_result["failure_count"] == 1
    assert eval_result["weighted_average_score"] == pytest.approx(1.0)

    rule_based_result = eval_result["results"][0]
    llm_judge_result = eval_result["results"][1]

    assert rule_based_result["passed"] is True
    assert rule_based_result["normalised_score"] == pytest.approx(1.0)
    assert rule_based_result["error"] is None

    assert llm_judge_result["passed"] is False
    assert llm_judge_result["normalised_score"] == 0
    assert llm_judge_result["error"] is not None


# Previously expected 200 with error embedded in results. Now the validator
# catches unknown IDs before evaluation, returning 400 instead.
def test_evaluate_with_invalid_id_returns_400(
    client_with_registry: TestClient,
    registry: EvaluationRegistry,
) -> None:
    evaluator = RuleBasedEvaluator(0.4, timeout=30)
    registry.register(evaluator.name, evaluator)

    request = [
        {
            "model_output": "Hello, World!",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": 1,
                    "threshold": 0.4,
                    "config": {
                        "rules": [
                            {
                                "name": "keyword",
                                "kind": "required",
                                "keyword": "World",
                                "weight": 1.0,
                            }
                        ]
                    },
                },
                {
                    "evaluator_id": "non_existent_evaluator",
                    "weight": 1,
                    "threshold": 0.4,
                    "config": {},
                },
            ],
        }
    ]

    response = client_with_registry.post("/evaluate", json=request)

    assert response.status_code == 400
    assert "Unknown evaluators" in response.json()["detail"]


# Unchanged — invalid config is per-evaluator, so the validator can't catch it
# upfront. This remains a genuine partial failure at runtime.
def test_evaluate_partial_failure_with_invalid_config(
    client_with_registry: TestClient,
    registry: EvaluationRegistry,
) -> None:
    evaluator = RuleBasedEvaluator(0.4, timeout=30)
    registry.register(evaluator.name, evaluator)

    request = [
        {
            "model_output": "Hello, World!",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": 1,
                    "threshold": 0.4,
                    "config": {
                        "rules": [
                            {
                                "name": "keyword",
                                "kind": "required",
                                "keyword": "World",
                                "weight": 1.0,
                            }
                        ]
                    },
                },
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": 1,
                    "threshold": 0.4,
                    "config": {
                        "rules": [
                            {
                                "name": "keyword",
                                "kind": "required",
                                # missing keyword field on purpose
                                "weight": 1.0,
                            }
                        ]
                    },
                },
            ],
        }
    ]

    response = client_with_registry.post("/evaluate", json=request)

    assert response.status_code == 200
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is True
    assert eval_result["failure_count"] == 1
    assert eval_result["weighted_average_score"] == pytest.approx(1.0)

    valid_rule_based_result = eval_result["results"][0]
    invalid_rule_based_result = eval_result["results"][1]

    assert valid_rule_based_result["passed"] is True
    assert valid_rule_based_result["normalised_score"] == pytest.approx(1.0)
    assert valid_rule_based_result["error"] is None

    assert invalid_rule_based_result["passed"] is False
    assert invalid_rule_based_result["normalised_score"] == 0
    assert invalid_rule_based_result["error"] == "Invalid config"
    assert invalid_rule_based_result["reasoning"] is not None
