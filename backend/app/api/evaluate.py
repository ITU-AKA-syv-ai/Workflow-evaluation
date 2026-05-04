from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.dependencies import get_orchestrator, get_registry, get_repository
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.aggregated_result_entity import AggregatedResultEntity, AggregatedResultResponse
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluatorInfo,
)
from app.core.models.registry import EvaluationRegistry
from app.core.repositories.i_result_repository import IResultRepository
from app.core.services.evaluation_service import get_evaluators
from app.api.auth import get_current_user

router = APIRouter()


@router.post("/evaluate")
async def evaluate_endpoint(
    requests: list[EvaluationRequest],
    orchestrator: Annotated[EvaluationOrchestrator, Depends(get_orchestrator)],
    repo: Annotated[IResultRepository, Depends(get_repository)],
    user:dict = Depends(get_current_user)
) -> list[AggregatedResultResponse]:
    """
    Evaluate one or more evaluation requests using their respective evaluator configurations.

    Args:
        requests (list[EvaluationRequest]):
            A list of evaluation requests. Each request contains
            the input data and evaluator configuration to apply.
        orchestrator (EvaluationOrchestrator):
            Injected orchestrator to use for evaluation strategies.
        repo (IResultRepository):
            Injected repository used to persist responses.

    Returns:
        list[AggregatedResultResponse]:
            A list of evaluation results, one for each request,
            containing the outcome of the applied evaluator configuration and the id/uuid of the thing persisted in the db.
    """
    results = []
    for req in requests:
        result = await orchestrator.evaluate(req)
        entity = AggregatedResultEntity(request=req, result=result)

        try:
            result_id = repo.insert(entity)
            results.append(AggregatedResultResponse(result_id=result_id, result=result, persisted=True))
        except Exception:
            results.append(AggregatedResultResponse(result_id=None, result=result, persisted=False))

    return results


@router.get("/evaluators")
def evaluators(
    registry: Annotated[EvaluationRegistry, Depends(get_registry)],
    user:dict = Depends(get_current_user)
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
    user: dict = Depends(get_current_user)
) -> list[AggregatedResultEntity]:
    """Retrieve a paginated list of recent aggregated results.

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
    user: dict = Depends(get_current_user)
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
