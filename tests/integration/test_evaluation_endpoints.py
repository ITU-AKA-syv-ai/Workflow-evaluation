from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import (
    EvaluationResponse,
    EvaluationResult,
)
from app.core.models.registry import EvaluationRegistry
from tests.conftest import (
    FakeResultRepository,
    create_evaluation_config,
    create_evaluation_request,
)


def make_entity() -> tuple[AggregatedResultEntity, UUID]:
    id = uuid4()
    return AggregatedResultEntity(
        id=id,
        created_at=datetime.now(UTC),
        request=create_evaluation_request(
            configs=[create_evaluation_config("mock_evaluator")],
        ),
        result=EvaluationResponse(
            weighted_average_score=0.8,
            results=[
                EvaluationResult(evaluator_id="mock_evaluator", passed=True, normalised_score=0.8),
            ],
        ),
    ), id


def test_returns_result_when_found(client_with_registry: TestClient, fake_repo: FakeResultRepository) -> None:
    entity, id = make_entity()
    fake_repo.results[id] = entity

    response = client_with_registry.get(f"/results/{entity.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(entity.id)


def test_returns_404_when_not_found(client_with_registry: TestClient) -> None:
    response = client_with_registry.get(f"/results/{uuid4()}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_returns_422_for_invalid_uuid(client_with_registry: TestClient) -> None:
    response = client_with_registry.get("/results/not-a-uuid")

    assert response.status_code == 422


def test_returns_empty_list(client_with_registry: TestClient) -> None:
    response = client_with_registry.get("/results")

    assert response.status_code == 200
    assert response.json() == []


def test_returns_results_ordered_by_most_recent(
    client_with_registry: TestClient, fake_repo: FakeResultRepository
) -> None:
    older, oid = make_entity()
    older.created_at = datetime(2024, 1, 1, tzinfo=UTC)
    fake_repo.results[oid] = older

    newer, nid = make_entity()
    newer.created_at = datetime(2025, 1, 1, tzinfo=UTC)
    fake_repo.results[nid] = newer

    response = client_with_registry.get("/results")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["id"] == str(newer.id)
    assert data[1]["id"] == str(older.id)


def test_respects_limit(client_with_registry: TestClient, fake_repo: FakeResultRepository) -> None:
    for _ in range(10):
        entity, id = make_entity()
        fake_repo.results[id] = entity

    response = client_with_registry.get("/results?limit=3")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_respects_offset(client_with_registry: TestClient, fake_repo: FakeResultRepository) -> None:
    for _ in range(5):
        entity, id = make_entity()
        fake_repo.results[id] = entity

    response = client_with_registry.get("/results?offset=3&limit=10")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_rejects_negative_offset(client_with_registry: TestClient) -> None:
    response = client_with_registry.get("/results?offset=-1")

    assert response.status_code == 422


def test_rejects_limit_over_max(client_with_registry: TestClient) -> None:
    response = client_with_registry.get("/results?limit=101")

    assert response.status_code == 422


def test_persists_result(
    client_with_registry: TestClient,
    fake_repo: FakeResultRepository,
    registry: EvaluationRegistry,
) -> None:
    req = [
        {
            "model_output": "Lorem Ipsum",
            "configs": [{"evaluator_id": "mock_evaluator", "weight": 1.0, "config": {}}],
        }
    ]

    response = client_with_registry.post("/evaluate", json=req)

    assert response.status_code == 200
    assert len(fake_repo.results) == 1


# TODO: Mangler at teste at evaluate faktisk persister
