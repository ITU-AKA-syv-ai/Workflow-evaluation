from fastapi import APIRouter

from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluatorInfo,
)
from app.core.services.evaluation_service import evaluate, get_evaluators

router = APIRouter()


@router.post("/evaluate")
def evaluate_endpoint(req: EvaluationRequest) -> EvaluationResponse:
    return evaluate(req)


@router.get("/evaluators", response_model=list[EvaluatorInfo])
def evaluators() -> list[EvaluatorInfo]:
    return get_evaluators()
