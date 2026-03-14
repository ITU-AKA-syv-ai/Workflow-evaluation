import asyncio
from collections.abc import Sequence

from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
    EvaluatorConfig,
)
from app.core.services.evaluation_service import evaluate_single


class EvaluationOrchestrator:
    """Coordinates running multiple evaluation strategies and aggregating results."""

    async def evaluate(self, req: EvaluationRequest) -> EvaluationResponse:
        tasks = [evaluate_single(req, strategy) for strategy in req.configs]  # coroutines, not yet running
        results = await asyncio.gather(*tasks)  # scheduled onto the event loop and awaits their completion together
        return self._aggregate(req.configs, list(results))

    @staticmethod
    def _aggregate(
        configs: Sequence[EvaluatorConfig],
        results: list[EvaluationResult],
    ) -> EvaluationResponse:
        weighted_score_sum = 0.0
        weights_sum = 0.0

        for config, result in zip(configs, results, strict=True):
            if result.error is None:
                weights_sum += config.weight
                weighted_score_sum += config.weight * result.normalised_score

        weighted_average_score = (
            weighted_score_sum / weights_sum if weights_sum != 0 else 0.0
        )

        is_partial = any(r.error is not None for r in results)

        return EvaluationResponse(
            results=results,
            weighted_average_score=weighted_average_score,
            is_partial=is_partial
        )
