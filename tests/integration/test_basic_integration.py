from fastapi.testclient import TestClient

from app.core.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.core.models.registry import EvaluationRegistry

# HTTP request -> FastAPI endpoint -> service layer -> evaluator -> result -> HTTP response


def test_basic_integration(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    # Arrange
    rule_based = RuleBasedEvaluator(threshold=1.0)
    registry.register(rule_based.name, rule_based)

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


def test_weighted_average_changes(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    model_output = "Lorem Ipsum"
    rule_based = RuleBasedEvaluator(threshold=1.0)
    registry.register(rule_based.name, rule_based)

    # Evaluator which scores higher is weighted higher
    # request_a
    request_a = [
        {
            "model_output": model_output,
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": 1.0,
                    "threshold": 0.4,
                    "config": {
                        "rules": [
                            {
                                "name": "format",
                                "kind": "max_length",
                                "max_length": len(model_output),
                                "weight": 2.5,
                            },
                            # passes
                            {
                                "name": "format",
                                "kind": "max_length",
                                "max_length": len(model_output) // 2,
                                "weight": 1.0,
                            },  # fails
                        ]
                    },
                }
            ],
        }
    ]

    # Evaluator which scores higher is weighted lower
    request_b = [
        {
            "model_output": model_output,
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": 1.0,
                    "threshold": 0.4,
                    "config": {
                        "rules": [
                            {
                                "name": "format",
                                "kind": "max_length",
                                "max_length": len(model_output),
                                "weight": 1.0,
                            },
                            # passes
                            {
                                "name": "format",
                                "kind": "max_length",
                                "max_length": len(model_output) // 2,
                                "weight": 2.5,
                            },  # fails
                        ]
                    },
                }
            ],
        }
    ]

    # Act (send HTTP request)
    response_a = client_with_registry.post("/evaluate", json=request_a)
    response_b = client_with_registry.post("/evaluate", json=request_b)

    # Assert (validate the HTTP response)

    assert response_a.status_code == 200  # check returned status code
    assert response_b.status_code == 200  # check returned status code
    json_a = response_a.json()
    json_b = response_b.json()

    assert json_a[0]["weighted_average_score"] > json_b[0]["weighted_average_score"]


def test_negative_weights_are_rejected(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    rule_based = RuleBasedEvaluator(threshold=1.0)
    registry.register(rule_based.name, rule_based)

    request = [
        {
            "model_output": "Should fail",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": -4.2,  # negative weight to trigger the check
                    "threshold": 0.4,
                    "config": {"rules": [{"name": "format", "kind": "max_length", "max_length": 10}]},
                }
            ],
        }
    ]

    # Act (send HTTP request)
    response = client_with_registry.post("/evaluate", json=request)

    # Assert
    assert response.status_code == 200
    json = response.json()

    assert json[0]["results"][0]["error"] == "Negative weight"
