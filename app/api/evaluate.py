from fastapi import APIRouter

from app.core.models.evaluationModel import EvaluationRequest, LengthEvaluator

from app.core.services.evaluationService import evaluate

router = APIRouter()

@router.get("/")
async def index():
    return {"Message": "Go to `/docs` for documentation on how to request an evaluation"}

@router.post("/")
def evaluateEndpoint(req: EvaluationRequest) -> bool:
    return evaluate(req)
