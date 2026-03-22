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

    async def _evaluate_single(
        self, req: EvaluationRequest, config: EvaluatorConfig
    ) -> EvaluationResult:
        """
        Evaluate a single evaluator configuration against the provided output.

        Args:
            req (EvaluationRequest): The evaluation request containing the output.
            config (EvaluatorConfig): Configuration specifying which evaluator to use and its parameters.

        Returns:
            EvaluationResult: The result of the evaluation, including whether it passed and any error messages.
        """
        evaluator = self._registry.get(config.evaluator_id)
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

        return await evaluator.evaluate(req.model_output, cfg, config.threshold)

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
