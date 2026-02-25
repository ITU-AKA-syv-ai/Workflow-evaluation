from fastapi import APIRouter

from app.core.models.evaluationModel import EvaluationRequest, LengthEvaluator

router = APIRouter()

@router.get("/")
async def index():
    return {"Message": "Go to `/docs` for documentation on how to request an evaluation"}

@router.post("/")
def evaluate(req: EvaluationRequest) -> bool:
    evaluator = LengthEvaluator()
    if evaluator is None:
        raise ValueError(f"Evaluator with id '{req.evaluator_id}' does not exist")

    cfg = evaluator.bind(config=req.config)
    if cfg is None:
        raise ValueError("Unable to parse cfg")

    return evaluator.evaluate(output=req.output, config=cfg)
