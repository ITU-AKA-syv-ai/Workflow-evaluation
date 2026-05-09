import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.auth import get_current_user
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
        400: {"description": "Bad request. Evaluator unknown or not specified"},
        401: {"description": "Invalid or expired token"},
        422: {"description": "Bad request. Validation error in request body"},
        500: {"description": "Unexpected error"},
    },
)
async def evaluate_endpoint(
    requests: list[EvaluationRequest],
    orchestrator: Annotated[EvaluationOrchestrator, Depends(get_orchestrator)],
    persistence: Annotated[ResultPersistenceService, Depends(get_persistence_service)],
    user: Annotated[dict[str, str], Depends(get_current_user)],
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
            request=req,
            result=result,
            weighted_score=result.weighted_average_score,
            status=EvaluationStatus.COMPLETED,
            created_by=user["sub"],
        )

        try:
            job_id = persistence.persist_completed(entity)
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
        401: {"description": "Invalid or expired token"},
        422: {"description": "Bad request. Validation error in request body"},
        500: {"description": "Unexpected error"},
    },
)
def create_evaluation(
    request: EvaluationRequest,
    session: SessionDep,
    repo: Annotated[IResultRepository, Depends(get_result_repository)],
    registry: Annotated[EvaluationRegistry, Depends(get_registry)],
    validator: Annotated[EvaluationRequestValidator, Depends(get_request_validator)],
    user: Annotated[dict[str, str], Depends(get_current_user)],
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

    entity = AggregatedResultEntity(request=request, result=None, created_by=user["sub"])
    try:
        with session.begin():
            job_id = repo.insert(entity)
    except SQLAlchemyError as e:
        logger.exception("Failed to persist async evaluation row")
        raise ResultPersistenceError() from e

    enqueue_evaluation_task(job_id, request, repo, session)

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
    responses={200: {"description": "Fetch was successful"}, 401: {"description": "invalid or expired token"}, 500: {"description": "Unexpected error"}},

)
def evaluators(
    registry: Annotated[EvaluationRegistry, Depends(get_registry)],
    user: Annotated[dict[str, str], Depends(get_current_user)],
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
        401: {"description": "Invalid or expired token"},
        422: {"description": "Validation error. Invalid offset or limit"},
        500: {"description": "Unexpected error"},
    },
)
def results(
    user: Annotated[dict[str, str], Depends(get_current_user)],
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
        401: {"description": "Invalid or expired token"},
        404: {"description": "No result found with the given result_id"},
        422: {"description": "Validation error. Invalid result_id"},
        500: {"description": "Unexpected error"},
    },
)
def get_result(
    job_id: UUID,
    repo: Annotated[IResultRepository, Depends(get_result_repository)],
    job_state: Annotated[JobStateLookup, Depends(get_job_state_lookup)],
    user: Annotated[dict[str, str], Depends(get_current_user)],
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
