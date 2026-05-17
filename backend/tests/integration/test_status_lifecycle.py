"""End-to-end tests for the GET endpoints' status determination, exercising the real
SQLAlchemy repository and a controllable stand-in for Celery.

The fake-repo tests in ``test_evaluation_endpoints.py`` verify the API-layer branch
logic in isolation. These tests round-trip through the real SQL pipeline to verify:

"""

from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.auth import create_token
from app.api.dependencies import (
    get_job_state_lookup,
    get_result_repository,
)
from app.api.evaluate import get_registry
from app.config.settings import get_settings
from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
)
from app.core.models.registry import EvaluationRegistry
from app.core.repositories.sqlalchemy_result_repository import SQLAlchemyResultRepository
from app.factory import create_app
from app.models import Base, EvaluationStatus
from tests.conftest import TestSettings


def _make_pending_entity() -> AggregatedResultEntity:
    """Mimic the shape of a row inserted by POST /async/evaluations: result is None,
    minimal request, no evaluator results yet."""
    return AggregatedResultEntity(
        request=EvaluationRequest(model_output="output", configs=[]),
        result=None,
        created_by="test-user",
    )


def _make_completed_response() -> EvaluationResponse:
    return EvaluationResponse(
        weighted_average_score=0.8,
        results=[EvaluationResult(evaluator_id="mock_evaluator", passed=True, normalised_score=0.8)],
    )


@pytest.fixture()
def sql_repo_client() -> Generator[
    tuple[TestClient, SQLAlchemyResultRepository, dict[UUID, EvaluationStatus]], None, None
]:
    """A TestClient backed by the real SQLAlchemyResultRepository plus a
    controllable job_state map. Tests insert entities through the real repo and
    tweak the map to simulate what Celery would say for a given job_id.

    Unlike the shared ``db_session`` fixture in ``integration/conftest.py``, this
    fixture builds its own engine with ``check_same_thread=False`` and
    ``StaticPool``. Reason: Starlette's ``TestClient`` runs sync endpoints in a
    worker thread, but SQLite refuses cross-thread access by default. The other
    repo tests don't hit this because they call the repo directly from the test
    thread; these tests go through HTTP, which spawns a worker. ``StaticPool``
    ensures every connection sees the same in-memory database.

    Yields a 3-tuple: ``(client, repo, job_state_overrides)``.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine)
    session = session_local()

    test_settings = TestSettings()
    repo = SQLAlchemyResultRepository(session)
    job_state_overrides: dict[UUID, EvaluationStatus] = {}

    def fake_job_state(job_id: UUID) -> EvaluationStatus:
        # Default any unmapped id to PENDING -- this mirrors Celery's behavior for
        # task ids it has no record of, which is the most realistic fallback.
        return job_state_overrides.get(job_id, EvaluationStatus.PENDING)

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_registry] = lambda: EvaluationRegistry(settings=test_settings)
    app.dependency_overrides[get_result_repository] = lambda: repo
    app.dependency_overrides[get_job_state_lookup] = lambda: fake_job_state
    with TestClient(app) as client:
        yield client, repo, job_state_overrides
    app.dependency_overrides.clear()
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_async_job_lifecycle_pending_then_completed(
    sql_repo_client: tuple[TestClient, SQLAlchemyResultRepository, dict[UUID, EvaluationStatus]],
) -> None:
    """Round-trip the async lifecycle:

    1. Insert an entity with ``result=None`` (the shape POST /async/evaluations
       persists before the worker has run).
    2. GET /evaluations/{id} returns PENDING -- the row's result column is null and
       the mocked job_state returns PENDING by default.
    3. Worker completes: write the response via ``repo.update``.
    4. GET /evaluations/{id} now returns COMPLETED, even though the mocked job_state
       still says PENDING. Proves the DB row is the authoritative signal after the
       worker finishes.
    """
    client, repo, _ = sql_repo_client
    entity = _make_pending_entity()
    job_id = repo.insert(entity)
    headers = {"Authorization": f"Bearer {create_token('test-user')}"}

    # Step 2: still pending -- no result on the row, job_state mock defaults to PENDING.
    response = client.get(f"/evaluations/{job_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == EvaluationStatus.PENDING.value

    # Step 3: worker finishes its evaluation and persists the response.
    repo.update(job_id, _make_completed_response())

    # Step 4: COMPLETED wins over the (still-PENDING) mocked job_state.
    response = client.get(f"/evaluations/{job_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == EvaluationStatus.COMPLETED.value


def test_list_results_status_against_sql_repo(
    sql_repo_client: tuple[TestClient, SQLAlchemyResultRepository, dict[UUID, EvaluationStatus]],
) -> None:
    """Same status logic on the list endpoint, exercised against the real SQL repo.
    Two rows go in -- one with a populated result, one without -- and the response
    must mark them COMPLETED and RUNNING respectively. The RUNNING case proves the
    fallback path doesn't just collapse everything to PENDING; the mocked job_state
    answer actually surfaces when the result column is empty.
    """
    client, repo, job_state_overrides = sql_repo_client

    # Row 1: finished -- result is non-null, so endpoint must say COMPLETED.
    completed_entity = _make_pending_entity()
    completed_id = repo.insert(completed_entity)
    repo.update(completed_id, _make_completed_response())

    # Row 2: in-flight -- result is null. The mocked job_state says RUNNING for this
    # id, so endpoint must surface RUNNING (not the default PENDING).
    running_entity = _make_pending_entity()
    running_id = repo.insert(running_entity)
    job_state_overrides[running_id] = EvaluationStatus.RUNNING

    headers = {"Authorization": f"Bearer {create_token('test-user')}"}
    response = client.get("/evaluations", headers=headers)

    assert response.status_code == 200
    data = response.json()
    by_id = {item["id"]: item["status"] for item in data}
    assert by_id[str(completed_id)] == EvaluationStatus.COMPLETED.value
    assert by_id[str(running_id)] == EvaluationStatus.RUNNING.value
