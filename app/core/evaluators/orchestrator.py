import asyncio

from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
    EvaluatorConfig,
)
from app.core.models.registry import EvaluationRegistry


class EvaluationOrchestrator:
    """Coordinates running multiple evaluation strategies and aggregating results."""

    def __init__(self, registry: EvaluationRegistry) -> None:
        self._registry = registry

    async def evaluate(self, req: EvaluationRequest) -> EvaluationResponse:
        tasks = [self._evaluate_single(req, config) for config in req.configs]
        results = await asyncio.gather(*tasks)
        return self._aggregate(req.configs, list(results))

    async def _evaluate_single(self, req: EvaluationRequest, evaluator_config: EvaluatorConfig) -> EvaluationResult:
        """
        Evaluate a single evaluator configuration against the provided output.

        Args:
            req (EvaluationRequest): The evaluation request containing the output.
            config (EvaluatorConfig): Configuration specifying which evaluator to use and its parameters.

        Returns:
            EvaluationResult: The result of the evaluation, including whether it passed and any error messages.
        """
        evaluator = self._registry.get(evaluator_config.evaluator_id)
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

        cfg = evaluator.validate_config(evaluator_config.config)
        if cfg is None:
            return EvaluationResult(
                evaluator_id=evaluator_config.evaluator_id,
                reasoning="Configuration is formatted incorrectly",
                error="Invalid config",
            )

        return await evaluator.evaluate(req.model_output, cfg, evaluator_config.threshold)

    @staticmethod
    def _aggregate(
        configs: list[EvaluatorConfig],
        results: list[EvaluationResult],
    ) -> EvaluationResponse:
        weighted_score_sum = 0.0
        weights_sum = 0.0

        for config, result in zip(configs, results, strict=True):
            if result.error is None:
                weights_sum += config.weight
                weighted_score_sum += config.weight * result.normalised_score

        weighted_average_score = weighted_score_sum / weights_sum if weights_sum != 0 else 0.0
        is_partial = any(r.error is not None for r in results)
        failure_count = sum(1 for r in results if r.error is not None)

        return EvaluationResponse(
            results=results,
            weighted_average_score=weighted_average_score,
            is_partial=is_partial,
            failure_count=failure_count,
        )
