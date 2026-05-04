import pytest
from fastapi.testclient import TestClient

from app.core.evaluators.llm_judge import LLMJudgeEvaluator
from app.core.evaluators.rouge_evaluator import RougeEvaluator
from app.core.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.core.models.registry import EvaluationRegistry
from tests.conftest import MockProvider
from app.api.auth import create_token


def test_evaluate_rule_based_and_llm_judge_equal_weight(
    client_with_registry: TestClient, registry: EvaluationRegistry, mock_provider: MockProvider
) -> None:
    # Arrange
    evaluator = LLMJudgeEvaluator(mock_provider, 1.0)
    registry.register(evaluator.name, evaluator)
    evaluator = RuleBasedEvaluator(0.4)
    registry.register(evaluator.name, evaluator)
    token = create_token("test-user")

    headers = {"Authorization": f"Bearer {token}"}
    request = [
        {
            "model_output": "Hello, World!",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": "1",
                    "threshold": "0.4",
                    "config": {"rules": [{"name": "keyword", "kind": "required", "keyword": "World", "weight": "1.0"}]},
                },
                {
                    "evaluator_id": "llm_judge",
                    "weight": "1",
                    "threshold": "1.0",
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

    # Act
    response = client_with_registry.post("/evaluate", json=request,headers=headers)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is False
    assert eval_result["failure_count"] == 0
    assert eval_result["weighted_average_score"] == pytest.approx((((3 - 1) / 3) + 1) / 2)

    rule_based_result = eval_result["results"][0]
    llm_judge_result = eval_result["results"][1]

    assert rule_based_result["passed"] is True
    assert llm_judge_result["passed"] is False


def test_evaluate_rule_based_and_llm_judge_inequal_weight(
    client_with_registry: TestClient, registry: EvaluationRegistry, mock_provider: MockProvider
) -> None:
    # Arrange
    evaluator = LLMJudgeEvaluator(mock_provider, 1.0)
    registry.register(evaluator.name, evaluator)
    registry.register(RuleBasedEvaluator(0.4).name, RuleBasedEvaluator(0.4))
    token = create_token("test-user")

    headers = {"Authorization": f"Bearer {token}"}
    request = [
        {
            "model_output": "Hello, World!",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": "1",
                    "threshold": "0.4",
                    "config": {"rules": [{"name": "keyword", "kind": "required", "keyword": "World", "weight": "1.0"}]},
                },
                {
                    "evaluator_id": "llm_judge",
                    "weight": "2",
                    "threshold": "1.0",
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

    # Act
    response = client_with_registry.post("/evaluate", json=request,headers=headers)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is False
    assert eval_result["failure_count"] == 0
    assert eval_result["weighted_average_score"] == pytest.approx((1 * 1 + (2 / 3) * 2) / (1 + 2))

    rule_based_result = eval_result["results"][0]
    llm_judge_result = eval_result["results"][1]

    assert rule_based_result["passed"] is True
    assert llm_judge_result["passed"] is False


def test_evaluate_rule_based_and_llm_judge_zero_weight(
    client_with_registry: TestClient, registry: EvaluationRegistry, mock_provider: MockProvider
) -> None:
    # Arrange
    evaluator = LLMJudgeEvaluator(mock_provider, 1.0)
    registry.register(evaluator.name, evaluator)
    registry.register(RuleBasedEvaluator(0.4).name, RuleBasedEvaluator(0.4))
    token = create_token("test-user")

    headers = {"Authorization": f"Bearer {token}"}
    request = [
        {
            "model_output": "Hello, World!",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": "1",
                    "threshold": "0.4",
                    "config": {"rules": [{"name": "keyword", "kind": "required", "keyword": "World", "weight": "1.0"}]},
                },
                {
                    "evaluator_id": "llm_judge",
                    "weight": "0",
                    "threshold": "1.0",
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

    # Act
    response = client_with_registry.post("/evaluate", json=request,headers=headers)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is False
    assert eval_result["failure_count"] == 0
    assert eval_result["weighted_average_score"] == 1

    rule_based_result = eval_result["results"][0]
    llm_judge_result = eval_result["results"][1]

    assert rule_based_result["passed"] is True
    assert llm_judge_result["passed"] is False


def test_two_identical_evaluators(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    # Arrange
    evaluator = RougeEvaluator(0.5)
    registry.register(evaluator.name, evaluator)
    token = create_token("test-user")

    headers = {"Authorization": f"Bearer {token}"}

    # Request written by ChatGPT
    request = [
        {
            "model_output": "the cat sat on the mat",
            "configs": [
                {
                    "evaluator_id": "rouge_evaluator",
                    "weight": 1,
                    "threshold": 0.5,
                    "config": {"reference": "the cat sat on the mat", "n_grams": 2},
                },
                {
                    "evaluator_id": "rouge_evaluator",
                    "weight": 1,
                    "threshold": 0.5,
                    "config": {"reference": "the cat is sitting on the mat"},
                },
            ],
        }
    ]

    # Act
    response = client_with_registry.post("/evaluate", json=request,headers=headers)

    # Assert (validate the HTTP response)
    assert response.status_code == 200
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is False
    assert eval_result["failure_count"] == 0
    assert eval_result["weighted_average_score"] >= 0.5

    rouge_n_result = eval_result["results"][0]
    rouge_l_result = eval_result["results"][1]

    assert rouge_n_result["passed"] is True
    assert rouge_l_result["passed"] is True
