import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import (
    JobStateLookup,
    SessionDep,
    get_job_state_lookup,
    get_orchestrator,
    get_persistence_service,
    get_registry,
    get_request_validator,
    get_result_repository,
)
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.aggregated_result_entity import AggregatedResultEntity, AggregatedResultResponse
from app.core.models.evaluation_model import (
    EvaluationQuery,
    EvaluationRequest,
    EvaluatorInfo,
    JobCreatedResponse,
)
from app.core.models.registry import EvaluationRegistry
from app.core.repositories.i_result_repository import IResultRepository
from app.core.services.evaluation_service import get_evaluators
from app.core.services.result_persistence_service import ResultPersistenceService
from app.core.services.validator import EvaluationRequestValidator
from app.exceptions import ResultPersistenceError
from app.models import EvaluationStatus
from app.workers.tasks import enqueue_evaluation_task

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/evaluations")
async def evaluate_endpoint(
    requests: list[EvaluationRequest],
    orchestrator: Annotated[EvaluationOrchestrator, Depends(get_orchestrator)],
    persistence: Annotated[ResultPersistenceService, Depends(get_persistence_service)],
) -> list[AggregatedResultResponse]:
    """
    Evaluate one or more evaluation requests synchronously and persist each one.

    A persistence failure on a single request is non-fatal here: the response is still
    returned with ``persisted=False`` so callers see the evaluation result even when
    the row could not be written. The service owns the transaction boundary; this
    handler only decides what to do when the domain-level
    ``ResultPersistenceError`` bubbles up.
    """
    results = []
    for req in requests:
        result = await orchestrator.evaluate(req)
        if result.weighted_average_score is None:
            raise ValueError("weighted_average_score was None")
        entity = AggregatedResultEntity(
            request=req, result=result, weighted_score=result.weighted_average_score, status=EvaluationStatus.COMPLETED
        )

        try:
            job_id = persistence.persist_completed(entity)
            results.append(AggregatedResultResponse(job_id=job_id, result=result, persisted=True))
        except ResultPersistenceError:
            results.append(AggregatedResultResponse(job_id=None, result=result, persisted=False))

    return results


@router.post("/async/evaluations", status_code=status.HTTP_202_ACCEPTED)
def create_evaluation(
    request: EvaluationRequest,
    session: SessionDep,
    repo: Annotated[IResultRepository, Depends(get_result_repository)],
    registry: Annotated[EvaluationRegistry, Depends(get_registry)],
    validator: Annotated[EvaluationRequestValidator, Depends(get_request_validator)],
) -> JobCreatedResponse:
    """Submit an evaluation request for asynchronous processing.

    The request is validated and persisted, then handed off to a background
    worker. Returns immediately with a task_id that can be used to poll
    GET /async/evaluations/{task_id} for status and results.

    The repository no longer commits internally, so the insert is wrapped in
    a transaction here and ``SQLAlchemyError`` is translated to the domain-level
    ``ResultPersistenceError`` (which the global handler turns into a 503).
    """

    validator.validate(request, registry)

    entity = AggregatedResultEntity(request=request, result=None)
    try:
        with session.begin():
            job_id = repo.insert(entity)
    except SQLAlchemyError as e:
        logger.exception("Failed to persist async evaluation row")
        raise ResultPersistenceError() from e

    enqueue_evaluation_task(job_id, request, repo, session)

    return JobCreatedResponse(task_id=job_id, status=EvaluationStatus.PENDING)


@router.get("/evaluators")
def evaluators(
    registry: Annotated[EvaluationRegistry, Depends(get_registry)],
) -> list[EvaluatorInfo]:
    """Retrieve all available evaluators from the registry."""
    return get_evaluators(registry)


@router.get("/evaluations")
def results(
    repo: Annotated[IResultRepository, Depends(get_result_repository)],
    job_state: Annotated[JobStateLookup, Depends(get_job_state_lookup)],
    query: Annotated[EvaluationQuery, Query()],
) -> list[AggregatedResultEntity]:
    """Retrieve a paginated list of recent aggregated results.

    Field validation (ranges, allowed values) and cross-field validation live on the
    ``EvaluationQuery`` model. FastAPI surfaces violations as 422 with
    field-level error messages.

    Args:
        repo (IResultRepository): The result repository, injected via dependency.
        job_state (JobStateLookup): The job state lookup function, injected via dependency.
        query (EvaluationQuery): Bundled pagination, filtering, and sorting parameters.

    Returns:
        A list of aggregated result entities, by default sorted by date descending and containing 5 results per page.
        Can be filtered by start_date, end_date, min_score, max_score and evaluator_ids.
        Can be sorted by date or score ascending or descending.
        Can be paginated by offset and limit.
    """
    entities = repo.get_results(**query.model_dump())
    # Populate status from Celery for each entity. AsyncResult lookups are local to
    # the configured backend and don't hit the broker, so this is N small DB reads.
    for entity in entities:
        if entity.id is not None:
            entity.status = job_state(entity.id)
    return entities


@router.get("/evaluations/{job_id}")
def get_result(
    job_id: UUID,
    repo: Annotated[IResultRepository, Depends(get_result_repository)],
    job_state: Annotated[JobStateLookup, Depends(get_job_state_lookup)],
) -> AggregatedResultEntity:
    """Retrieve a single aggregated result by its ID.

    The repository raises ``ResultNotFoundError`` (handled globally as a 404) when the
    id is unknown, so this handler doesn't need to translate the missing case itself.
    """
    result = repo.get_result_by_id(job_id)
    result.status = job_state(job_id)
    return result
