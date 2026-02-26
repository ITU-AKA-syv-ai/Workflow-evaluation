
from app.core.models.evaluationModel import EvaluationRequest, registry

def evaluate(req: EvaluationRequest) -> bool:
    evaluator = registry.get(req.evaluator_id)
    if evaluator is None:
        raise ValueError(f"Evaluator with id '{req.evaluator_id}' does not exist")

    cfg = evaluator.bind(config=req.config)
    if cfg is None:
        raise ValueError("Unable to parse cfg")

    return evaluator.evaluate(output=req.output, config=cfg)
