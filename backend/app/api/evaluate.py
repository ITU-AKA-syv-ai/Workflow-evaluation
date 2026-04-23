from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_job_status_service, get_registry, get_repository
from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluatorInfo,
    JobCreatedResponse,
    JobStatusResponse,
)
from app.core.models.registry import EvaluationRegistry
from app.core.repositories.i_result_repository import IResultRepository
from app.core.services.evaluation_service import get_evaluators
from app.core.services.job_status_service import JobNotFoundError, JobStatus, JobStatusService
from app.core.services.validator import EvaluationRequestValidator
from app.workers.tasks import run_evaluation_task

router = APIRouter()


@router.post("/evaluations", status_code=status.HTTP_202_ACCEPTED)
def create_evaluation(
    request: EvaluationRequest,
    registry: Annotated[EvaluationRegistry, Depends(get_registry)],
) -> JobCreatedResponse:
    """
    Submit an evaluation request for asynchronous processing.

    Validates the request and enqueues the evaluation on a Celery worker. Returns
    immediately with the task ID. The actual evaluation runs in the background. Poll
    GET /evaluations/{task_id} to check status and retrieve the result ID once completed.

    Args:
        request (EvaluationRequest): The evaluation request to process in the background.
        registry (EvaluationRegistry): Injected registry used to validate evaluator IDs.

    Returns:
        JobCreatedResponse: The task ID and initial status of the newly enqueued task.
    """
    # Validate up front so malformed requests fail fast with a 400. Any EvaluationError raised
    # here is converted to an HTTP response by the global exception handler.
    EvaluationRequestValidator().validate(request, registry)

    async_result = run_evaluation_task.delay(request.model_dump(mode="json"))

    return JobCreatedResponse(task_id=UUID(async_result.id), status=JobStatus.PENDING)


@router.get("/evaluations/{task_id}")
def get_evaluation_status(
    task_id: UUID,
    job_status_service: Annotated[JobStatusService, Depends(get_job_status_service)],
) -> JobStatusResponse:
    """
    Retrieve the status of an evaluation task.

    When status is COMPLETED, the result_id field points to the persisted result, which can
    be fetched via GET /results/{result_id}. When status is FAILED, the error field contains
    a description of the failure.

    Args:
        task_id (UUID): The unique identifier of the Celery task returned from POST.
        job_status_service (JobStatusService): Injected service that queries task state.

    Returns:
        JobStatusResponse: The current state of the task.

    Raises:
        HTTPException: 404 if no task with the given ID exists, or if its result has expired.
    """
    try:
        job_status, result_id, error = job_status_service.get_status(task_id)
    except JobNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

    return JobStatusResponse(
        task_id=task_id,
        status=job_status,
        result_id=result_id,
        error=error,
    )


@router.get("/evaluators")
def evaluators(
    registry: Annotated[EvaluationRegistry, Depends(get_registry)],
) -> list[EvaluatorInfo]:
    """
    Retrieve all available evaluators from the registry.

    Returns:
        list[EvaluatorInfo]: A list of evaluators, each including the evaluator ID,
        description, and expected configuration schema.
    """
    return get_evaluators(registry)


@router.get("/results")
def results(
    repo: Annotated[IResultRepository, Depends(get_repository)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=5, ge=1, le=100),
) -> list[AggregatedResultEntity]:
    """
    Retrieve a paginated list of recent aggregated results.

    Args:
        repo: The result repository, injected via dependency.
        offset: Number of results to skip (for pagination). Defaults to 0.
        limit: Maximum number of results to return, between 1 and 100. Defaults to 5.

    Returns:
        A list of aggregated result entities, ordered by most recent.
    """
    return repo.get_recent_results(offset=offset, limit=limit)


@router.get("/results/{result_id}")
def get_result(
    result_id: UUID,
    repo: Annotated[IResultRepository, Depends(get_repository)],
) -> AggregatedResultEntity:
    """
    Retrieve a single aggregated result by its ID.

    Args:
        result_id: The unique identifier of the result to fetch.
        repo: The result repository, injected via dependency.

    Returns:
        The matching aggregated result entity.

    Raises:
        HTTPException: 404 if no result with the given ID exists.
    """
    result = repo.get_result_by_id(result_id)

    if result is None:
        raise HTTPException(status_code=404, detail=f"Result {result_id} not found")

    return result
