from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
    EvaluatorConfig,
    EvaluatorInfo,
)
from app.core.models.registry import registry


def get_evaluators() -> list[EvaluatorInfo]:
    """
    Retrieve all available evaluators from the registry.

    Returns:
        list[EvaluatorInfo]: A list of EvaluatorInfo objects, each containing the evaluator's ID, description, and
        configuration schema.
    """
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
    """
    Evaluate the provided output using a list of evaluator configurations.

    Args:
        req (EvaluationRequest): The evaluation request containing the output and evaluator configurations.

    Returns:
        EvaluationResponse: Contains a list of EvaluationResult for each evaluator configuration applied.
    """
    results = []
    for strategy in req.configs:
        results.append(_evaluate_single(req, strategy))

    return EvaluationResponse(results=results)


def _evaluate_single(
    req: EvaluationRequest, config: EvaluatorConfig
) -> EvaluationResult:
    """
    Evaluate a single evaluator configuration against the provided output.

    Args:
        req (EvaluationRequest): The evaluation request containing the output.
        config (EvaluatorConfig): Configuration specifying which evaluator to use and its parameters.

    Returns:
        EvaluationResult: The result of the evaluation, including whether it passed and any error messages.
    """
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
