from fastapi.testclient import TestClient

from app.core.evaluators.length_evaluator import LengthEvaluator
from app.core.evaluators.substring_evaluator import SubstringEvaluator
from app.core.models.registry import EvaluationRegistry

# HTTP request -> FastAPI endpoint -> service layer -> evaluator -> result -> HTTP response


def test_basic_integration(
    client_with_registry: TestClient, registry: EvaluationRegistry
) -> None:
    # Arrange
    registry.register(SubstringEvaluator().name, SubstringEvaluator())

    request = [
        {
            "model_output": "Hello, World!",
            "configs": [
                {
                    "evaluator_id": "substring_evaluator",
                    "weight": 1,
                    "threshold": 0.4,
                    "config": {"substring": "World"},
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
                    "evaluator_id": "substring_evaluator",
                    "passed": True,
                    "reasoning": 'Substring "World" is present.',
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


def test_weighted_average_changes(
    client_with_registry: TestClient, registry: EvaluationRegistry
) -> None:
    model_output = "Lorem Ipsum"
    registry.register(LengthEvaluator().name, LengthEvaluator())

    # Evaluator which scores higher is weighted higher
    request_a = [
        {
            "model_output": model_output,
            "configs": [
                {
                    "evaluator_id": "length_evaluator",
                    "weight": 2.5,
                    "threshold": 0.4,
                    "config": {"expected_length": len(model_output)},
                },
                {
                    "evaluator_id": "length_evaluator",
                    "weight": 1.2,
                    "threshold": 0.4,
                    "config": {"expected_length": len(model_output) * 2},
                },
            ],
        }
    ]

    # Evaluator which scores higher is weighted lower
    request_b = [
        {
            "model_output": model_output,
            "configs": [
                {
                    "evaluator_id": "length_evaluator",
                    "weight": 1.2,
                    "threshold": 0.4,
                    "config": {"expected_length": len(model_output)},
                },
                {
                    "evaluator_id": "length_evaluator",
                    "weight": 2.5,
                    "threshold": 0.4,
                    "config": {"expected_length": len(model_output) * 2},
                },
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


def test_negative_weights_are_rejected(
    client_with_registry: TestClient, registry: EvaluationRegistry
) -> None:
    registry.register(LengthEvaluator().name, LengthEvaluator())

    # Evaluator which scores higher is weighted higher
    request = [
        {
            "model_output": "Should fail",
            "configs": [
                {
                    "evaluator_id": "length_evaluator",
                    "weight": -4.2,
                    "threshold": 0.4,
                    "config": {"expected_length": 5},
                }
            ],
        }
    ]

    # Act (send HTTP request)
    response = client_with_registry.post("/evaluate", json=request)

    # Assert (validate the HTTP response)

    assert response.status_code == 200  # check returned status code
    json = response.json()

    assert json[0]["results"][0]["error"] == "Negative weight"
