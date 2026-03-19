from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
    EvaluatorConfig,
    EvaluatorInfo,
)
from app.core.models.registry import EvaluationRegistry


def get_evaluators(registry: EvaluationRegistry) -> list[EvaluatorInfo]:
    """
    Retrieve all available evaluators from the registry.

    Returns:
        list[EvaluatorInfo]: A list of EvaluatorInfo objects, each containing the evaluator's ID, description, and
        configuration schema.
    """
    results = []
    for evaluator in registry.get_evaluators():
        results.append(
            EvaluatorInfo(
                evaluator_id=evaluator.name,
                description=evaluator.description,
                config_schema=evaluator.config_schema,
            )
        )

    return results


def evaluate(
    req: EvaluationRequest, registry: EvaluationRegistry
) -> EvaluationResponse:
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
        result = _evaluate_single(req, strategy, registry)
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
    req: EvaluationRequest,
    evaluator_config: EvaluatorConfig,
    registry: EvaluationRegistry,
) -> EvaluationResult:
    """
    Evaluate a single evaluator configuration against the provided output.

    Args:
        req (EvaluationRequest): The evaluation request containing the output.
        config (EvaluatorConfig): Configuration specifying which evaluator to use and its parameters.

    Returns:
        EvaluationResult: The result of the evaluation, including whether it passed and any error messages.
    """

    evaluator = registry.get(evaluator_config.evaluator_id)
    if evaluator is None:
        return EvaluationResult(
            evaluator_id=evaluator_config.evaluator_id,
            reasoning="Fatal error",
            error="Invalid evaluator_id",
        )

    if evaluator_config.weight < 0:
        return EvaluationResult(
            evaluator_id=evaluator_config.evaluator_id,
            reasoning="Weights cannot be negative",
            error="Negative weight",
        )

    # The variable "evaluator_config" contains the overall configuration for the evaluator to be executed.
    # The fields "evaluator_config.weight" and "evaluator_config.threshold" are universal for all evaluators.
    #
    # However, each evaluator also expects a specially formatted configuration which acts as the
    # parameters to that evaluator. For instance, the substring evaluator expects a string which
    # tells the evaluator what substring to search for. This configuration is stored within "evaluator_config.config".
    #
    # Since each evaluator expects a different configuration, the "evaluator_config.config" is given as a
    # dict[str, Any]. So, the configuration must be typechecked and converted into the actual
    # type the evaluator expects. For the substring evaluator, this would be the
    # "SubstringEvaluatorConfig" class which contains a substring field.
    # This is what "bind" does. It takes this generic configuration and spits back an evaluator
    # config that can be given to the evaluator.
    bound_evaluator_config = evaluator.bind(evaluator_config.config)
    if bound_evaluator_config is None:
        return EvaluationResult(
            evaluator_id=evaluator_config.evaluator_id,
            reasoning="Configuration is formatted incorrectly",
            error="Invalid config",
        )

    return evaluator.evaluate(
        req.model_output, bound_evaluator_config, evaluator_config.threshold
    )
