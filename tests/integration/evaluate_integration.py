# tests/test_evaluate_integration.py

from collections.abc import Generator

import pytest
from starlette.testclient import TestClient

from app.api.dependencies import get_orchestrator
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.registry import EvaluationRegistry
from app.main import app
from tests.conftest import MockEvaluator


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    registry = EvaluationRegistry()
    evaluator = MockEvaluator()
    registry.register(evaluator.name, evaluator)
    orchestrator = EvaluationOrchestrator(registry)

    app.dependency_overrides[get_orchestrator] = lambda: orchestrator
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def make_request(  # noqa: ANN201
    model_output: str = "test output",
    evaluator_id: str = "mock_evaluator",
):
    return {
        "model_output": model_output,
        "configs": [
            {"evaluator_id": evaluator_id, "config": {}},
        ],
    }


class TestEvaluateHappyPath:
    def test_returns_200_with_valid_request(self, client: TestClient) -> None:
        response = client.post("/evaluate", json=[make_request()])

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["weighted_average_score"] == pytest.approx(0.8)
        assert data[0]["results"][0]["evaluator_id"] == "mock_evaluator"
        assert data[0]["results"][0]["normalised_score"] == pytest.approx(0.8)

    def test_multiple_requests_in_batch(self, client: TestClient) -> None:
        response = client.post(
            "/evaluate",
            json=[make_request(), make_request(model_output="second")],
        )

        assert response.status_code == 200
        assert len(response.json()) == 2


class TestEvaluateValidationErrors:
    def test_missing_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/evaluate")
        assert response.status_code == 422

    def test_missing_model_output_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/evaluate",
            json=[{"configs": [{"evaluator_id": "x", "config": {}}]}],
        )
        assert response.status_code == 422

    def test_missing_config_field_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/evaluate",
            json=[{"model_output": "test", "configs": [{"evaluator_id": "x"}]}],
        )
        assert response.status_code == 422

    def test_not_a_list_returns_422(self, client: TestClient) -> None:
        response = client.post("/evaluate", json="not a list")
        assert response.status_code == 422


class TestEvaluateDomainErrors:
    def test_unknown_evaluator_returns_error_in_result(self, client: TestClient) -> None:
        response = client.post(
            "/evaluate",
            json=[make_request(evaluator_id="nonexistent")],
        )

        assert response.status_code == 200
        result = response.json()[0]["results"][0]
        assert result["error"] == "Invalid evaluator_id"

    def test_negative_weight_returns_error_in_result(self, client: TestClient) -> None:
        response = client.post(
            "/evaluate",
            json=[{
                "model_output": "test",
                "configs": [
                    {"evaluator_id": "mock_evaluator", "config": {}, "weight": -1.0},
                ],
            }],
        )

        assert response.status_code == 200
        result = response.json()[0]["results"][0]
        assert result["error"] == "Negative weight"
