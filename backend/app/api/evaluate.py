import logging
from typing import Annotated
from uuid import UUID
from datetime import date
from typing import Literal
from fastapi import HTTPException

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    JobStateLookup,
    get_evaluation_repository,
    get_job_state_lookup,
    get_orchestrator,
    get_registry,
    get_request_validator,
    get_result_repository,
)
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.aggregated_result_entity import AggregatedResultEntity, AggregatedResultResponse
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluatorInfo,
    JobCreatedResponse,
)
from app.core.models.registry import EvaluationRegistry
from app.core.repositories.i_evalution_repository import IEvaluationRepository
from app.core.repositories.i_result_repository import IResultRepository
from app.core.services.evaluation_service import get_evaluators
from app.core.services.validator import EvaluationRequestValidator
from app.exceptions import ResultPersistenceError
from app.models import EvaluationStatus
from app.utils.time_utils import datetime_from_json_string
from app.workers.tasks import enqueue_evaluation_task

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/evaluations")
async def evaluate_endpoint(
    requests: list[EvaluationRequest],
    orchestrator: Annotated[EvaluationOrchestrator, Depends(get_orchestrator)],
    result_repo: Annotated[IResultRepository, Depends(get_result_repository)],
    eval_repo: Annotated[IEvaluationRepository, Depends(get_evaluation_repository)],
) -> list[AggregatedResultResponse]:
    """
    Evaluate one or more evaluation requests synchronously and persist each one.

    A persistence failure on a single request is non-fatal here: the response is still
    returned with ``persisted=False`` so callers see the evaluation result even when
    the row could not be written.
    """
    results = []
    for req in requests:
        result = await orchestrator.evaluate(req)
        entity = AggregatedResultEntity(
            request=req, result=result, weighted_score=result.weighted_average_score, status=EvaluationStatus.COMPLETED
        )

        try:
            job_id = result_repo.insert(entity)
            results.append(AggregatedResultResponse(job_id=job_id, result=result, persisted=True))
            for single_result in result.results:
                eval_repo.insert(single_result, job_id)
        except ResultPersistenceError:
            results.append(AggregatedResultResponse(job_id=None, result=result, persisted=False))
    return results


@router.post("/async/evaluations", status_code=status.HTTP_202_ACCEPTED)
def create_evaluation(
    request: EvaluationRequest,
    repo: Annotated[IResultRepository, Depends(get_result_repository)],
    registry: Annotated[EvaluationRegistry, Depends(get_registry)],
    validator: Annotated[EvaluationRequestValidator, Depends(get_request_validator)],
) -> JobCreatedResponse:
    """Submit an evaluation request for asynchronous processing.

    The request is validated and persisted, then handed off to a background
    worker. Returns immediately with a task_id that can be used to poll
    GET /async/evaluations/{task_id} for status and results.
    """

    validator.validate(request, registry)

    entity = AggregatedResultEntity(request=request, result=None)
    job_id = repo.insert(entity)

    enqueue_evaluation_task(job_id, request, repo)

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
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=5, ge=1, le=100),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    min_score: float | None = Query(default=None, ge=0, le=1),
    max_score: float | None = Query(default=None, ge=0, le=1),
    sorting: Literal["date", "score"] = Query(default="date"),
    sorting_direction: Literal["asc", "desc"] = Query(default="desc"),
) -> list[AggregatedResultEntity]:
    """Retrieve a paginated list of recent aggregated results.

    Args:
        repo (IResultRepository): The result repository, injected via dependency.
        job_state (JobStateLookup): The job state lookup function, injected via dependency.
        offset (int): Number of results to skip (for pagination). Defaults to 0.
        limit (int): Maximum number of results to return, between 1 and 100. Defaults to 5.
        start_date (date | None): The start date of the query, i.e. the maximum date for the oldest result. Defaults to None.
        end_date (date | None): The end date of the query, i.e. the earliest date for the newest result. Defaults to None.
        min_score (float | None): The minimum score of the query, i.e. the minimum score for the results. Defaults to None.
        max_score (float | None): The maximum score of the query, i.e. the maximum score for the results. Defaults to None.
        sorting (Literal["date", "score"]): The field to sort by in the query. Defaults to "date".
        sorting_direction (Literal["asc", "desc"]): The sorting direction of the query. Defaults to "desc".

    Returns:
        A list of aggregated result entities, by default sorted by date descending and containing 5 results per page.
        Can be filtered by start_date, end_date, min_score, and max_score.
        Can be sorted by date or score ascending or descending.
        Can be paginated by offset and limit.

    Raises:
        HTTPException: If the start_date is after the end_date or if the min_score is greater than the max_score.
    """

    # start_date_prime = datetime_from_json_string(start_date) if start_date is not None else None
    # end_date_prime = datetime_from_json_string(end_date) if end_date is not None else None
    # todo: vær sikker på, at frontend ikke breaker siden date parameters er skiftet fra str til date - i så fald, slet ovenstående udkommenteret kode

    if start_date is not None and end_date is not None:
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date cannot be after end_date")

    if min_score is not None and max_score is not None:
        if min_score > max_score:
            raise HTTPException(status_code=400, detail="min_score cannot be greater than max_score")

    entities = repo.get_results(
        offset=offset,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        min_score=min_score,
        max_score=max_score,
        sorting=sorting,
        sorting_direction=sorting_direction,
    )
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
