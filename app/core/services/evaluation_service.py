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
    weighted_score_sum = 0
    weights_sum = 0
    for strategy in req.configs:
        result = _evaluate_single(req, strategy)
        results.append(result)
        if result.error is None:
            weights_sum += strategy.weight
            weighted_score_sum += strategy.weight * result.normalised_score

    weighted_average_score = 0
    if weights_sum != 0:
        weighted_average_score = weighted_score_sum / weights_sum

    return EvaluationResponse(
        results=results, weighted_average_score=weighted_average_score
    )


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
            evaluator_id=config.evaluator_id,
            reasoning="Fatal error",
            error="Invalid evaluator_id",
        )

    if config.weight < 0:
        return EvaluationResult(
            evaluator_id=config.evaluator_id,
            reasoning="Weights cannot be negative",
            error="Negative weight",
        )

    cfg = evaluator.bind(config.config)
    if cfg is None:
        return EvaluationResult(
            evaluator_id=config.evaluator_id,
            reasoning="Configuration is formatted incorrectly",
            error="Invalid config",
        )

    return evaluator.evaluate(req.model_output, cfg, config.threshold)
