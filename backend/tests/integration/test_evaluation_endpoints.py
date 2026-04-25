from datetime import UTC, datetime
from math import isclose
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import (
    EvaluationResponse,
    EvaluationResult,
)
from app.core.models.registry import EvaluationRegistry
from app.models import EvaluationStatus
from tests.conftest import (
    FakeResultRepository,
    MockEvaluator,
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
        status=EvaluationStatus.COMPLETED,
    ), id


def test_returns_result_when_found(client_with_registry: TestClient, fake_repo: FakeResultRepository) -> None:
    entity, id = make_entity()
    fake_repo.results[id] = entity

    response = client_with_registry.get(f"/evaluations/{entity.id}")

    assert response.status_code == 200
    assert response.json()["id"] == str(entity.id)


def test_returns_404_when_not_found(client_with_registry: TestClient) -> None:
    response = client_with_registry.get(f"/evaluations/{uuid4()}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_returns_422_for_invalid_uuid(client_with_registry: TestClient) -> None:
    response = client_with_registry.get("/evaluations/not-a-uuid")

    assert response.status_code == 422


def test_returns_empty_list(client_with_registry: TestClient) -> None:
    response = client_with_registry.get("/evaluations")

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

    response = client_with_registry.get("/evaluations")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["id"] == str(newer.id)
    assert data[1]["id"] == str(older.id)


def test_respects_limit(client_with_registry: TestClient, fake_repo: FakeResultRepository) -> None:
    for _ in range(10):
        entity, id = make_entity()
        fake_repo.results[id] = entity

    response = client_with_registry.get("/evaluations?limit=3")

    assert response.status_code == 200
    assert len(response.json()) == 3


def test_respects_offset(client_with_registry: TestClient, fake_repo: FakeResultRepository) -> None:
    for _ in range(5):
        entity, id = make_entity()
        fake_repo.results[id] = entity

    response = client_with_registry.get("/evaluations?offset=3&limit=10")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_rejects_negative_offset(client_with_registry: TestClient) -> None:
    response = client_with_registry.get("/evaluations?offset=-1")

    assert response.status_code == 422


def test_rejects_limit_over_max(client_with_registry: TestClient) -> None:
    response = client_with_registry.get("/evaluations?limit=101")

    assert response.status_code == 422


def test_limit_minimum(client_with_registry: TestClient) -> None:
    response = client_with_registry.get("/evaluations?limit=1")
    assert response.status_code == 200


def test_rejects_zero_limit(client_with_registry: TestClient) -> None:
    response = client_with_registry.get("/evaluations?limit=0")
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

    registry.register("mock_evaluator", MockEvaluator(name="mock_evaluator", score=1.0))

    response = client_with_registry.post("/evaluations", json=req)

    assert response.status_code == 200
    assert len(fake_repo.results) == 1


def test_persists_is_retrievable(
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
    registry.register("mock_evaluator", MockEvaluator(name="mock_evaluator", score=1.0))

    response = client_with_registry.post("/evaluations", json=req)
    job_id = response.json()[0]["job_id"]

    result = client_with_registry.get(f"/evaluations/{job_id}")
    assert result.status_code == 200
    assert result.json()["id"] == job_id


def test_batch_persists_all(
    client_with_registry: TestClient,
    fake_repo: FakeResultRepository,
    registry: EvaluationRegistry,
) -> None:
    req = [
        {
            "model_output": "Lorem Ipsum",
            "configs": [{"evaluator_id": "mock_evaluator", "weight": 1.0, "config": {}}],
        }
    ] * 3

    registry.register("mock_evaluator", MockEvaluator(name="mock_evaluator", score=1.0))

    evaluator = MockEvaluator()
    registry.register(evaluator.name, evaluator)

    response = client_with_registry.post("/evaluations", json=req)

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert len(fake_repo.results) == 3


def test_batch_persists_failure(
    client_with_occasional_failing_repo: TestClient,
    registry: EvaluationRegistry,
) -> None:
    mock_evaluator = MockEvaluator(name="mock_evaluator", score=1.0)
    registry.register(mock_evaluator.name, mock_evaluator)

    req = [
        {
            "model_output": "Some persist, some fail",
            "configs": [
                {"evaluator_id": "mock_evaluator", "config": {}},
            ],
        }
    ] * 3

    response = client_with_occasional_failing_repo.post("/evaluations", json=req)

    assert response.status_code == 200
    assert len(response.json()) == 3
    assert any(not v["persisted"] for v in response.json())
    assert any(v["persisted"] for v in response.json())
    for v in filter(lambda v: not v["persisted"], response.json()):
        assert v["job_id"] is None


def test_single_persistence_failure(
    client_with_failing_repo: TestClient,
    registry: EvaluationRegistry,
) -> None:

    mock_evaluator = MockEvaluator(name="mock_evaluator", score=1.0)
    registry.register(mock_evaluator.name, mock_evaluator)

    req = [
        {
            "model_output": "One persists, the other fails",
            "configs": [
                {"evaluator_id": "mock_evaluator", "config": {}},
                {"evaluator_id": "mock_evaluator", "config": {}},
            ],
        }
    ]

    resp = client_with_failing_repo.post("/evaluations", json=req)

    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert not resp.json()[0]["persisted"]
    assert resp.json()[0]["job_id"] is None


def test_request_evaluator_failure(
    client_with_registry: TestClient,
    registry: EvaluationRegistry,
) -> None:

    good_evaluator = MockEvaluator(name="good_evaluator", score=1.0)
    bad_evaluator = MockEvaluator(name="bad_evaluator", raise_on_evaluate=Exception("This should fail!"))
    registry.register(good_evaluator.name, good_evaluator)
    registry.register(bad_evaluator.name, bad_evaluator)

    req = [
        {
            "model_output": "One evaluator fails",
            "configs": [
                {"evaluator_id": good_evaluator.name, "config": {}},
                {"evaluator_id": bad_evaluator.name, "config": {}},
            ],
        }
    ]

    resp = client_with_registry.post("/evaluations", json=req)

    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["result"]["failure_count"] == 1
    assert resp.json()[0]["result"]["results"][0]["error"] is None
    assert resp.json()[0]["result"]["results"][1]["error"] is not None


def test_weighted_average(client_with_registry: TestClient, registry: EvaluationRegistry) -> None:
    full_score = MockEvaluator(name="evaluator_a", score=1.0)
    full_score_weight = 1.7

    half_score = MockEvaluator(name="evaluator_b", score=0.5)
    half_score_weight = 0.9

    quarter_score = MockEvaluator(name="evaluator_c", score=0.25)
    quarter_score_weight = 1.0

    expected_score = (
        (full_score.evaluation.normalised_score * full_score_weight)
        + (half_score.evaluation.normalised_score * half_score_weight)
        + (quarter_score.evaluation.normalised_score * quarter_score_weight)
    ) / (full_score_weight + half_score_weight + quarter_score_weight)

    registry.register(full_score.name, full_score)
    registry.register(half_score.name, half_score)
    registry.register(quarter_score.name, quarter_score)

    req = [
        {
            "model_output": "One evaluator fails",
            "configs": [
                {"evaluator_id": full_score.name, "weight": full_score_weight, "config": {}},
                {"evaluator_id": half_score.name, "weight": half_score_weight, "config": {}},
                {"evaluator_id": quarter_score.name, "weight": quarter_score_weight, "config": {}},
            ],
        }
    ]

    resp = client_with_registry.post("/evaluations", json=req)

    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert isclose(resp.json()[0]["result"]["weighted_average_score"], expected_score)


@pytest.fixture()
def req() -> dict[str, Any]:
    return {
        "model_output": "Lorem Ipsum",
        "configs": [{"evaluator_id": "mock_evaluator", "weight": 1.0, "config": {}}],
    }


def test_async_returns_202_with_job_id(
    client_with_registry: TestClient,
    registry: EvaluationRegistry,
    req: dict[str, Any],
) -> None:
    registry.register("mock_evaluator", MockEvaluator(name="mock_evaluator", score=1.0))

    with patch("app.api.evaluate.run_evaluation_task"):
        response = client_with_registry.post("/async/evaluations", json=req)

    assert response.status_code == 202
    assert response.json()["status"] == EvaluationStatus.PENDING.value
    assert "task_id" in response.json()


def test_async_inserts_entity_into_repo(
    client_with_registry: TestClient,
    fake_repo: FakeResultRepository,
    registry: EvaluationRegistry,
    req: dict[str, Any],
) -> None:
    registry.register("mock_evaluator", MockEvaluator(name="mock_evaluator", score=1.0))

    with patch("app.api.evaluate.run_evaluation_task"):
        response = client_with_registry.post("/async/evaluations", json=req)

    task_id = UUID(response.json()["task_id"])

    assert task_id in fake_repo.results
    assert fake_repo.results[task_id].status == EvaluationStatus.PENDING


@patch("app.api.evaluate.run_evaluation_task")
def test_async_rejects_unknown_evaluator(
    mock_task: MagicMock,
    client_with_registry: TestClient,
    req: dict[str, Any],
) -> None:
    response = client_with_registry.post("/async/evaluations", json=req)

    assert response.status_code == 400
    mock_task.delay.assert_not_called()


def test_async_returns_503_on_repo_failure(
    client_with_failing_repo: TestClient,
    registry: EvaluationRegistry,
    req: dict[str, Any],
) -> None:
    registry.register("mock_evaluator", MockEvaluator(name="mock_evaluator", score=1.0))

    with patch("app.api.evaluate.run_evaluation_task"):
        response = client_with_failing_repo.post("/async/evaluations", json=req)

    assert response.status_code == 503
    assert "accept" in response.json()["detail"].lower()


def test_async_returns_503_on_queue_failure(
    client_with_registry: TestClient,
    registry: EvaluationRegistry,
    req: dict[str, Any],
) -> None:
    registry.register("mock_evaluator", MockEvaluator(name="mock_evaluator", score=1.0))

    with patch("app.api.evaluate.run_evaluation_task") as mock_task:
        mock_task.delay.side_effect = Exception("Queue down")
        response = client_with_registry.post("/async/evaluations", json=req)

    assert response.status_code == 503
    assert "queue" in response.json()["detail"].lower()


def test_async_marks_failed_on_queue_failure(
    client_with_registry: TestClient,
    fake_repo: FakeResultRepository,
    registry: EvaluationRegistry,
    req: dict[str, Any],
) -> None:
    registry.register("mock_evaluator", MockEvaluator(name="mock_evaluator", score=1.0))

    with patch("app.api.evaluate.run_evaluation_task") as mock_task:
        mock_task.delay.side_effect = Exception("Queue down")
        client_with_registry.post("/async/evaluations", json=req)

    assert len(fake_repo.results) == 1
    entity = next(iter(fake_repo.results.values()))
    assert entity.status == EvaluationStatus.FAILED
