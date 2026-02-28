from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
    EvaluatorConfig,
    EvaluatorInfo,
)
from app.core.models.registry import registry


def get_evaluators() -> list[EvaluatorInfo]:
    results = []
    for evaluator in registry.registry.values():
        results.append(
            EvaluatorInfo(
                evaluator_id=evaluator.name,
                description=evaluator.description,
                config_schema=evaluator.config_schema,
            )
        )

    return results


def evaluate(req: EvaluationRequest) -> EvaluationResponse:
    results = []
    for strategy in req.configs:
        results.append(_evaluate_single(req, strategy))

    return EvaluationResponse(results=results)


def _evaluate_single(
    req: EvaluationRequest, config: EvaluatorConfig
) -> EvaluationResult:

    evaluator = registry.get(config.evaluator_id)
    if evaluator is None:
        return EvaluationResult(
            evaluator_id=config.evaluator_id, passed=False, error="Invalid evaluator_id"
        )

    cfg = evaluator.bind(config.config)
    if cfg is None:
        return EvaluationResult(
            evaluator_id=config.evaluator_id, passed=False, error="Invalid config"
        )

    result = evaluator.evaluate(req.output, cfg)
    return EvaluationResult(evaluator_id=evaluator.name, passed=result)
