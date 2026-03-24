from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.dependencies import get_orchestrator, get_registry
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluatorInfo,
)
from app.core.models.registry import EvaluationRegistry
from app.core.services.evaluation_service import get_evaluators

router = APIRouter()


@router.post("/evaluate")
async def evaluate_endpoint(
    requests: list[EvaluationRequest],
    orchestrator: Annotated[EvaluationOrchestrator, Depends(get_orchestrator)],
) -> list[EvaluationResponse]:
    """
    Evaluate one or more evaluation requests using their respective evaluator configurations.

    Args:
        requests (list[EvaluationRequest]):
            A list of evaluation requests. Each request contains
            the input data and evaluator configuration to apply.
        orchestrator (EvaluationOrchestrator):
            Injected orchestrator to use for evaluation strategies.

    Returns:
        list[EvaluationResponse]:
            A list of evaluation results, one for each request,
            containing the outcome of the applied evaluator configuration.
    """
    return [await orchestrator.evaluate(req) for req in requests]


@router.get("/evaluators", response_model=list[EvaluatorInfo])
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
