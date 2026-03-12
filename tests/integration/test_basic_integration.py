from fastapi.testclient import TestClient

from app.main import app as fastapi_app

# HTTP request -> FastAPI endpoint -> service layer -> evaluator -> result -> HTTP response


def test_basic_integration() -> None:
    # Arrange (HTTP request)
    client = TestClient(fastapi_app)

    request = [
        {
            "model_output": "Hello, World!",
            "configs": [
                {
                    "evaluator_id": "substring_evaluator",
                    "weight": 1,
                    "config": {"substring": "World"},
                }
            ],
        }
    ]

    # Act (send HTTP request)
    response = client.post("/evaluate", json=request)

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
        }
    ]
