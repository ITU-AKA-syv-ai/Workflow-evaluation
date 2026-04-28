from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_orchestrator, get_registry, get_repository
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
from app.core.services.job_status_service import get_job_state
from app.core.services.validator import EvaluationRequestValidator
from app.models import EvaluationStatus
from app.workers.tasks import run_evaluation_task

router = APIRouter()


@router.post("/evaluations")
async def evaluate_endpoint(
    requests: list[EvaluationRequest],
    orchestrator: Annotated[EvaluationOrchestrator, Depends(get_orchestrator)],
    repo: Annotated[IResultRepository, Depends(get_repository)],
) -> list[AggregatedResultResponse]:
    """
    Evaluate one or more evaluation requests synchronously and persist each one.
    """
    results = []
    for req in requests:
        result = await orchestrator.evaluate(req)
        entity = AggregatedResultEntity(request=req, result=result)

        try:
            job_id = repo.insert(entity)
            results.append(AggregatedResultResponse(job_id=job_id, result=result, persisted=True))
        except Exception:
            results.append(AggregatedResultResponse(job_id=None, result=result, persisted=False))

    return results


@router.post("/async/evaluations", status_code=status.HTTP_202_ACCEPTED)
def create_evaluation(
    request: EvaluationRequest,
    repo: Annotated[IResultRepository, Depends(get_repository)],
    registry: Annotated[EvaluationRegistry, Depends(get_registry)],
) -> JobCreatedResponse:
    EvaluationRequestValidator().validate(request, registry)

    try:
        entity = AggregatedResultEntity(request=request, result=None)
        job_id = repo.insert(entity)
    except Exception as e:
        raise HTTPException(status_code=503, detail="Unable to accept your request.") from e

    try:
        # Pin the Celery task id to the Result row id so AsyncResult(job_id) returns
        # the lifecycle state of *this* job. This is what lets job_status_service.
        # get_job_state look up status without us having to store a separate column.
        run_evaluation_task.apply_async(
            args=(job_id, request.model_dump(mode="json")),
            task_id=str(job_id),
        )
    except Exception as e:
        # Roll back the Result row so we don't leave orphaned rows mapped to no task.
        # With Celery owning status, there's no "FAILED" marker to set on the row;
        # deletion is the cleanest signal that this job never reached the queue.
        repo.delete(job_id)
        raise HTTPException(status_code=503, detail="Unable to queue your request.") from e

    return JobCreatedResponse(task_id=job_id, status=EvaluationStatus.PENDING)


@router.get("/evaluators")
def evaluators(
    registry: Annotated[EvaluationRegistry, Depends(get_registry)],
) -> list[EvaluatorInfo]:
    """Retrieve all available evaluators from the registry."""
    return get_evaluators(registry)


@router.get("/evaluations")
def results(
    repo: Annotated[IResultRepository, Depends(get_repository)],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=5, ge=1, le=100),
) -> list[AggregatedResultEntity]:
    """Retrieve a paginated list of recent aggregated results."""
    entities = repo.get_recent_results(offset=offset, limit=limit)
    # Populate status from Celery for each entity. AsyncResult lookups are local to
    # the configured backend and don't hit the broker, so this is N small DB reads.
    for entity in entities:
        if entity.id is not None:
            entity.status = get_job_state(entity.id)
    return entities


@router.get("/evaluations/{job_id}")
def get_result(
    job_id: UUID,
    repo: Annotated[IResultRepository, Depends(get_repository)],
) -> AggregatedResultEntity:
    """Retrieve a single aggregated result by its ID."""
    result = repo.get_result_by_id(job_id)

    if result is None:
        raise HTTPException(status_code=404, detail=f"Result {job_id} not found")

    result.status = get_job_state(job_id)
    return result
