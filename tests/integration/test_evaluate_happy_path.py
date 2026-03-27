from fastapi.testclient import TestClient

from app.core.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.core.models.registry import EvaluationRegistry

# HTTP request -> FastAPI endpoint -> service layer -> evaluator -> result -> HTTP response

def test_rule_based_keyword(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    # Arrange
    registry.register(RuleBasedEvaluator().name, RuleBasedEvaluator())

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
                }
            ],
        }
    ]

    # Act
    response = client_with_registry.post("/evaluate", json=request)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    json = response.json()

    # The execution time can vary
    json[0]["results"][0]["execution_time"] = 0
    assert json == [
        {
            "results": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "passed": True,
                    "reasoning": "1/1 rules passed. keyword: pass (The required keyword 'World' is present in the output.)",
                    "normalised_score": 1.0,
                    "execution_time": 0,
                    "error": None,
                }
            ],
            "weighted_average_score": 1.0,
            "is_partial": False,
            "failure_count": 0,
        }
    ]


def test_rule_based_regex(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    # Arrange
    registry.register(RuleBasedEvaluator().name, RuleBasedEvaluator())

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
                                "pattern": "^(\d{4})-(0[1-9]|1[0-2]|[1-9])-([1-9]|0[1-9]|[1-2]\d|3[0-1])$", # Matches dates YYYY-MM-DD
                                "weight": 1.0
                            }
                        ]
                    }
                }
            ]
        }
    ]

    # Regex source: https://regex101.com/library/oE3yO7

    # Act
    response = client_with_registry.post("/evaluate", json=request)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    eval_result = response.json()[0]

    assert eval_result["weighted_average_score"] == 1.0
    assert eval_result["is_partial"] is False

    strat_result = eval_result["results"][0]
    assert strat_result["passed"] is True
    assert strat_result["normalised_score"] == 1.0
    assert strat_result["error"] is None
    assert strat_result["reasoning"] == "1/1 rules passed. regex: pass (Pattern matched)"

def test_rule_based_format(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    # Arrange
    registry.register(RuleBasedEvaluator().name, RuleBasedEvaluator())

    request = [
        {
            "model_output": "123456789",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": 1,
                    "threshold": 0.4,
                    "config": {
                        "rules": [
                            {
                                "name": "format",
                                "kind": "max_length",
                                "max_length": "10",
                                "weight": 1.0
                            }
                        ]
                    }
                }
            ]
        }
    ]

    # Act
    response = client_with_registry.post("/evaluate", json=request)

    # Assert (validate the HTTP response)
    assert response.status_code == 200  # check returned status code
    eval_result = response.json()[0]

    assert eval_result["weighted_average_score"] == 1.0
    assert eval_result["is_partial"] is False

    strat_result = eval_result["results"][0]
    assert strat_result["passed"] is True
    assert strat_result["normalised_score"] == 1.0
    assert strat_result["error"] is None
    assert strat_result["reasoning"] == "1/1 rules passed. format: pass (Output length 9 is within max length 10.)"