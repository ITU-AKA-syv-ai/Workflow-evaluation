from fastapi.testclient import TestClient

from app.main import app

# HTTP request -> FastAPI endpoint -> service layer -> evaluator -> result -> HTTP response


def test_basic_integration() -> None:
    # Arrange (HTTP request)
    client = TestClient(app)

    request = {
        "output": "Hello, World!",
        "configs": [
            {"evaluator_id": "substring_evaluator", "config": {"substring": "World"}}
        ],
    }

    # Act (send HTTP request)
    response = client.post("/evaluate", json=request)

    # Assert (validate the HTTP response)

    assert response.status_code == 200  # check returned status code
    assert response.json() == {
        "results": [
            {"evaluator_id": "substring_evaluator", "passed": True, "error": None}
        ]
    }
