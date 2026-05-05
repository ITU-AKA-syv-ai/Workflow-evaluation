import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import (
    JobStateLookup,
    get_job_state_lookup,
    get_orchestrator,
    get_registry,
    get_repository,
    get_request_validator,
)
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.aggregated_result_entity import AggregatedResultEntity, AggregatedResultResponse
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluatorInfo,
    JobCreatedResponse,
)
from app.core.models.registry import EvaluationRegistry
from app.core.repositories.i_result_repository import IResultRepository
from app.core.services.evaluation_service import get_evaluators
from app.core.services.validator import EvaluationRequestValidator
from app.exceptions import ResultPersistenceError
from app.models import EvaluationStatus
from app.utils.time_utils import datetime_from_json_string
from app.workers.tasks import enqueue_evaluation_task

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/evaluations",
    summary="Evaluate AI-generated outputs",
    description="""
    Evaluate one or more AI-generated output using specified evaluation strategies.

    Each request contains:
    - The AI output to evaluate.
    - A set of evaluator configurations.

    Configurations are processed individually and persisted/stored in the database.

    Returns:
    - Results for each evaluator configuration.
    - Whether persistence in the database succeeded.
    - The ID of the aggregated result.
    - An aggregated score based on each strategy employed.
    """,
    response_model=list[AggregatedResultResponse],
    tags=["Evaluation"],
    responses={
        200: {"description": "Successful evaluation (even if persistence fails)"},
        400: {"description": "Bad request. Evaluator unknown or  not specified"},
        422: {"description": "Bad request. Validation error in request body"},
        500: {"description": "Unexpected error"},
    },
)
async def evaluate_endpoint(
    requests: list[EvaluationRequest],
    orchestrator: Annotated[EvaluationOrchestrator, Depends(get_orchestrator)],
    repo: Annotated[IResultRepository, Depends(get_repository)],
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
        entity = AggregatedResultEntity(request=req, result=result, status=EvaluationStatus.COMPLETED)

        try:
            job_id = repo.insert(entity)
            results.append(AggregatedResultResponse(job_id=job_id, result=result, persisted=True))
        except ResultPersistenceError:
            results.append(AggregatedResultResponse(job_id=None, result=result, persisted=False))

    return results


@router.post(
    "/async/evaluations",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Evaluate AI-generated outputs with asynchronous processing",
    description="""
    Submit an evaluation request for asynchronous processing using specified evaluation strategies.

    Each request contains:
    - The AI output to evaluate.
    - A set of evaluator configurations.

    The request is validated and persisted before being handed off to a background worker.

    Returns immediately without performing the evaluation.

    Returns:
    - A job ID that can be used to retrieve the evaluation later.
    - The current status of the evaluation job (initially pending).
    """,
    response_model=JobCreatedResponse,
    tags=["Async Evaluation"],
    responses={
        202: {"description": "Evaluation job accepted and queued for processing"},
        400: {"description": "Bad request. Evaluator unknown or not specified"},
        422: {"description": "Bad request. Validation error in request body"},
        500: {"description": "Unexpected error"},
    },
)
def create_evaluation(
    request: EvaluationRequest,
    repo: Annotated[IResultRepository, Depends(get_repository)],
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


@router.get(
    "/evaluators",
    summary="Browse all available evaluators.",
    description="""
    Fetch a comprehensive list of all evaluators available in the system.

    Including details:
    - Evaluator ID
    - Description
    - Config schema
    """,
    response_model=list[EvaluatorInfo],
    tags=["Evaluation"],
    responses={200: {"description": "Fetch was successful"}, 500: {"description": "Unexpected error"}},
)
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


@router.get(
    "/evaluations",
    summary="Fetch previous evaluations",
    description="""
    Fetch a paginated list of previously executed evaluations.

    Supports pagination via:
    - offset: The number of results to skip (must be >= 0).
    - limit: The maximum number of results to return (1-100).

    Supports filtering via:
    - start_date and end_date: Filter the stored evaluations by when they were created.
    - ascending: Whether you want the result to be sorted ascending or descending. Default: Descending.

    Returns:
    - A list of aggregated evaluation results.
    - Each result includes:
        - The original evaluation request.
        - The computed evaluation results.
        - Metadata such as ID and creation timestamp.
    """,
    response_model=list[AggregatedResultEntity],
    tags=["Evaluation"],
    responses={
        200: {"description": "Results successfully retrieved"},
        422: {"description": "Validation error. Invalid offset or limit"},
        500: {"description": "Unexpected error"},
    },
)
def results(
    repo: Annotated[IResultRepository, Depends(get_repository)],
    job_state: Annotated[JobStateLookup, Depends(get_job_state_lookup)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=5, ge=1, le=100),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    ascending: bool = Query(default=False),
) -> list[AggregatedResultEntity]:
    """Retrieve a paginated list of recent aggregated results.

    Args:
        repo: The result repository, injected via dependency.
        offset: Number of results to skip (for pagination). Defaults to 0.
        limit: Maximum number of results to return, between 1 and 100. Defaults to 5.
        start_date: The start date of the query, i.e. the maximum date for the oldest result.
        end_date: The end date of the query, i.e. the earliest date for the newest result.

    Returns:
        A list of aggregated result entities, ordered by most recent.

    Raises:
        HTTPException: If start_date or end_date is given and the string is malformed.
    """

    start_date_prime = datetime_from_json_string(start_date) if start_date is not None else None
    end_date_prime = datetime_from_json_string(end_date) if end_date is not None else None

    entities = repo.get_recent_results(
        offset=offset, limit=limit, start=start_date_prime, end=end_date_prime, ascending=ascending
    )
    # Populate status from Celery for each entity. AsyncResult lookups are local to
    # the configured backend and don't hit the broker, so this is N small DB reads.
    for entity in entities:
        if entity.id is not None:
            entity.status = job_state(entity.id)
    return entities


@router.get(
    "/evaluations/{job_id}",
    summary="Fetch a single result by its ID.",
    description="""
    Fetch a single previously executed evaluation by its unique result ID.

    The result includes:
    - The original evaluation request used to generate the result.
    - The full aggregated evaluation output.
    - Individual evaluator results and scores.
    - Creation timestamp.
    """,
    response_model=AggregatedResultEntity,
    tags=["Evaluation"],
    responses={
        200: {"description": "Result successfully retrieved"},
        404: {"description": "No result found with the given result_id"},
        422: {"description": "Validation error. Invalid result_id"},
        500: {"description": "Unexpected error"},
    },
)
def get_result(
    job_id: UUID,
    repo: Annotated[IResultRepository, Depends(get_repository)],
    job_state: Annotated[JobStateLookup, Depends(get_job_state_lookup)],
) -> AggregatedResultEntity:
    """Retrieve a single aggregated result by its ID.

    The repository raises ``ResultNotFoundError`` (handled globally as a 404) when the
    id is unknown, so this handler doesn't need to translate the missing case itself.

    Args:
        result_id: The unique identifier of the result to fetch.
        repo: The result repository, injected via dependency.

    Returns:
        The matching aggregated result entity.

    Raises:
        HTTPException: 404 if no result with the given ID exists.
    """
    result = repo.get_result_by_id(job_id)
    result.status = job_state(job_id)
    return result
