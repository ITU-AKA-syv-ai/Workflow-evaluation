import pytest
from fastapi.testclient import TestClient

from app.core.evaluators.cosine_evaluator import CosineEvaluator
from app.core.evaluators.llm_judge import LLMJudgeEvaluator
from app.core.evaluators.rouge_evaluator import RougeEvaluator
from app.core.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.core.models.embeddings import MockEmbeddingClient
from app.core.models.registry import EvaluationRegistry
from tests.conftest import MockProvider

# HTTP request -> FastAPI endpoint -> service layer -> evaluator -> result -> HTTP response


def test_rule_based_keyword(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    # Arrange
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
                    "config": {"rules": [{"name": "keyword", "kind": "required", "keyword": "World", "weight": 1.0}]},
                }
            ],
        }
    ]

    # Act
    response = client_with_registry.post("/evaluations", json=request)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    json_response = response.json()

    # The execution time can vary
    json_response[0]["result"]["results"][0]["execution_time"] = 0
    # The result_id can vary
    json_response[0]["result_id"] = 0
    assert json_response[0]["result"] == {
        "weighted_average_score": 1,
        "results": [
            {
                "evaluator_id": "rule_based_evaluator",
                "passed": True,
                "reasoning": "1/1 rules passed. keyword: pass (The required keyword 'World' is present in the output.)",
                "normalised_score": 1,
                "execution_time": 0,
                "error": None,
            }
        ],
        "is_partial": False,
        "failure_count": 0,
    }


def test_rule_based_regex(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    # Arrange
    evaluator = RuleBasedEvaluator(0.4, timeout=30)
    registry.register(evaluator.name, evaluator)

    request = [
        {
            "model_output": "2026-03-27",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": 1,
                    "threshold": 0.4,
                    "config": {
                        "rules": [
                            {
                                "name": "regex",
                                "kind": "required",
                                "pattern": r"^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$",  # Matches dates YYYY-MM-DD
                                "weight": 1.0,
                            }
                        ]
                    },
                }
            ],
        }
    ]

    # Regex source: https://regex101.com/library/oE3yO7

    # Act
    response = client_with_registry.post("/evaluations", json=request)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    eval_result = response.json()[0]["result"]

    assert eval_result["weighted_average_score"] == pytest.approx(1.0)
    assert eval_result["is_partial"] is False

    strat_result = eval_result["results"][0]
    assert strat_result["passed"] is True
    assert strat_result["normalised_score"] == pytest.approx(1.0)
    assert strat_result["error"] is None
    assert strat_result["reasoning"] == "1/1 rules passed. regex: pass (Pattern matched)"


def test_rule_based_format(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    # Arrange
    evaluator = RuleBasedEvaluator(0.4, timeout=30)
    registry.register(evaluator.name, evaluator)

    request = [
        {
            "model_output": "123456789",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": 1,
                    "threshold": 0.4,
                    "config": {"rules": [{"name": "format", "kind": "max_length", "max_length": "10", "weight": 1.0}]},
                }
            ],
        }
    ]

    # Act
    response = client_with_registry.post("/evaluations", json=request)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    eval_result = response.json()[0]["result"]

    assert eval_result["weighted_average_score"] == pytest.approx(1.0)
    assert eval_result["is_partial"] is False

    strat_result = eval_result["results"][0]
    assert strat_result["passed"] is True
    assert strat_result["normalised_score"] == pytest.approx(1.0)
    assert strat_result["error"] is None
    assert strat_result["reasoning"] == "1/1 rules passed. format: pass (Output length 9 is within max length 10.)"


def test_llm_judge(client_with_registry: TestClient, registry: EvaluationRegistry, mock_provider: MockProvider) -> None:
    # Arrange
    evaluator = LLMJudgeEvaluator(mock_provider, 0.5, timeout=30)
    registry.register(evaluator.name, evaluator)

    request = [
        {
            "model_output": "To eat a banana efficiently, peel it from the bottom, remove the peel in strips, and eat it in a few quick bites. This method minimizes mess and is commonly recommended.",
            "configs": [
                {
                    "evaluator_id": "llm_judge",
                    "weight": 1,
                    "threshold": 0.5,
                    "config": {
                        "prompt": "How can I eat bananas most efficiently?",
                        "rubric": [
                            "correctness: is the advice factually correct?",
                            "clarity: is the explanation easy to understand?",
                            "politeness: is the tone appropriate and polite?",
                        ],
                    },
                }
            ],
        }
    ]

    # Act
    response = client_with_registry.post("/evaluations", json=request)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is False
    assert eval_result["failure_count"] == 0

    strat_result = eval_result["results"][0]
    assert strat_result["passed"] is True
    assert strat_result["normalised_score"] == pytest.approx(2 / 3)


def test_rouge_n(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    # Arrange
    evaluator = RougeEvaluator(0.5, timeout=30)
    registry.register(evaluator.name, evaluator)

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
                }
            ],
        }
    ]

    # Act
    response = client_with_registry.post("/evaluations", json=request)

    # Assert (validate the HTTP response)
    assert response.status_code == 200
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is False
    assert eval_result["failure_count"] == 0
    assert eval_result["weighted_average_score"] is not None

    strat_result = eval_result["results"][0]
    assert strat_result["passed"] is True
    assert strat_result["normalised_score"] is not None


def test_rouge_l(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    # Arrange
    evaluator = RougeEvaluator(0.5, timeout=30)
    registry.register(evaluator.name, evaluator)

    # Request written by ChatGPT
    request = [
        {
            "model_output": "the cat sat on the mat",
            "configs": [
                {
                    "evaluator_id": "rouge_evaluator",
                    "weight": 1,
                    "threshold": 0.5,
                    "config": {"reference": "the cat is sitting on the mat"},
                }
            ],
        }
    ]

    # Act
    response = client_with_registry.post("/evaluations", json=request)

    # Assert (validate the HTTP response)
    assert response.status_code == 200
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is False
    assert eval_result["failure_count"] == 0
    assert eval_result["weighted_average_score"] is not None

    strat_result = eval_result["results"][0]
    assert strat_result["passed"] is True
    assert strat_result["normalised_score"] is not None


def test_cosine_similarity(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    mock_client = MockEmbeddingClient([[1.0, 0.0], [1.0, 0.0]])
    evaluator = CosineEvaluator(mock_client, 0.5, timeout=30)
    registry.register(evaluator.name, evaluator)

    request = [
        {
            "model_output": "test",
            "configs": [
                {
                    "evaluator_id": "cosine_similarity_evaluator",
                    "weight": 1,
                    "threshold": 0.5,
                    "config": {
                        "reference": "test",
                    },
                }
            ],
        }
    ]

    response = client_with_registry.post("/evaluations", json=request)

    assert response.status_code == 200
    eval_result = response.json()[0]["result"]

    assert eval_result["is_partial"] is False

    strat_result = eval_result["results"][0]
    assert strat_result["passed"] is True
    assert strat_result["normalised_score"] == pytest.approx(1)
