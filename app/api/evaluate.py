from fastapi import APIRouter

from app.core.engine.orchestrator import EvaluationOrchestrator
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluatorInfo,
)
from app.core.services.evaluation_service import get_evaluators

router = APIRouter()


@router.post("/evaluate")
async def evaluate_endpoint(
    requests: list[EvaluationRequest],
) -> list[EvaluationResponse]:
    """
    Evaluate one or more evaluation requests using their respective evaluator configurations.

    Args:
        requests (list[EvaluationRequest]):
            A list of evaluation requests. Each request contains
            the input data and evaluator configuration to apply.

    Returns:
        list[EvaluationResponse]:
            A list of evaluation results, one for each request,
            containing the outcome of the applied evaluator configuration.
    """
    orchestrator = EvaluationOrchestrator()
    return [await orchestrator.evaluate(req) for req in requests]


@router.get("/evaluators", response_model=list[EvaluatorInfo])
def evaluators() -> list[EvaluatorInfo]:
    """
    Retrieve all available evaluators from the registry.

    Returns:
        list[EvaluatorInfo]: A list of evaluators, each including the evaluator ID,
        description, and expected configuration schema.
    """
    return get_evaluators()
