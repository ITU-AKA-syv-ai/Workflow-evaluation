from fastapi.testclient import TestClient

from app.core.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.core.models.registry import EvaluationRegistry

# HTTP request -> FastAPI endpoint -> service layer -> evaluator -> result -> HTTP response


def test_weighted_average_changes(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    model_output = "Lorem Ipsum"
    evaluator = RuleBasedEvaluator(0.4)
    registry.register(evaluator.name, evaluator)

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
    response_a = client_with_registry.post("/evaluations", json=request_a)
    response_b = client_with_registry.post("/evaluations", json=request_b)

    # Assert (validate the HTTP response)

    assert response_a.status_code == 200  # check returned status code
    assert response_b.status_code == 200  # check returned status code
    json_a = response_a.json()
    json_b = response_b.json()

    assert json_a[0]["result"]["weighted_average_score"] > json_b[0]["result"]["weighted_average_score"]


def test_negative_weights_are_rejected(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    evaluator = RuleBasedEvaluator(0.4)
    registry.register(evaluator.name, evaluator)

    request = [
        {
            "model_output": "Should fail",
            "configs": [
                {
                    "evaluator_id": "rule_based_evaluator",
                    "weight": -4.2,  # negative weight rejected by Pydantic
                    "threshold": 0.4,
                    "config": {"rules": [{"name": "format", "kind": "max_length", "max_length": 10}]},
                }
            ],
        }
    ]

    # Act (send HTTP request)
    response = client_with_registry.post("/evaluations", json=request)

    # Assert
    assert response.status_code == 422
