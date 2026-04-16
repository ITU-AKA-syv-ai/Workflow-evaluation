import asyncio
import logging
import time

from backend.app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
    EvaluatorConfig,
)
from backend.app.core.models.registry import EvaluationRegistry
from backend.app.core.services.validator import EvaluationRequestValidator
from backend.app.logging.context import evaluator_id_ctx

logger = logging.getLogger(__name__)


class EvaluationOrchestrator:
    """Coordinates running multiple evaluation strategies and aggregating results."""

    def __init__(self, registry: EvaluationRegistry) -> None:
        """
        Initialize the orchestrator with an evaluator registry.

        Args:
            registry (EvaluationRegistry): The registry used to look up evaluators by ID when executing evaluation requests.
        """
        self._registry = registry
        self._validator = EvaluationRequestValidator()

    async def evaluate(self, req: EvaluationRequest) -> EvaluationResponse:
        """
        Execute all evaluators for a request concurrently and return an aggregated result.
        Logs evaluation lifecycle events and excludes failed evaluators from the final score.
        """
        self._validator.validate(req, self._registry)

        logger.info(
            "evaluation_started",
            extra={
                "num_strategies": len(req.configs),
            },
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("evaluation_request_payload", extra={"payload": req.model_output})

        start = time.time()

        tasks = [self._evaluate_single(req, config) for config in req.configs]
        results = await asyncio.gather(*tasks)
        response = self._aggregate(req.configs, list(results))

        duration = time.time() - start

        logger.info(
            "evaluation_completed",
            extra={
                "execution_time": duration,
                "failure_count": response.failure_count,
                "is_partial": response.is_partial,
            },
        )

        return response

    async def _evaluate_single(self, req: EvaluationRequest, evaluator_config: EvaluatorConfig) -> EvaluationResult:
        """
        Evaluate a single evaluator configuration against the provided output.

        Args:
            req (EvaluationRequest): The evaluation request containing the output.
            config (EvaluatorConfig): Configuration specifying which evaluator to use and its parameters.

        Returns:
            EvaluationResult: The result of the evaluation, including whether it passed and any error messages.
        """
        evaluator_id = evaluator_config.evaluator_id

        evaluator_id_ctx.set(evaluator_id)

        logger.info("strategy_started")

        start = time.time()

        evaluator = self._registry.get(evaluator_config.evaluator_id)

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
        # This is what "validate_config" does. It takes this generic configuration and spits back an evaluator
        # config that can be given to the evaluator.

        evaluator = self._registry.get(evaluator_config.evaluator_id)

        cfg = evaluator.validate_config(evaluator_config.config)
        if cfg is None:
            logger.warning("strategy_failed_invalid_config")
            return EvaluationResult(
                evaluator_id=evaluator_config.evaluator_id,
                reasoning="Configuration is formatted incorrectly",
                error="Invalid config",
            )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                "strategy_input",
                extra={"config": cfg, "model_output": req.model_output},
            )

        result = await evaluator.evaluate(req.model_output, cfg, evaluator_config.threshold)

        duration = time.time() - start

        if result.error:
            logger.warning(
                "strategy_completed_with_error",
                extra={
                    "execution_time": duration,
                    "error": result.error,
                },
            )
        else:
            logger.info(
                "strategy_completed_success",
                extra={
                    "execution_time": duration,
                    "score": result.normalised_score,
                },
            )

        return result

    @staticmethod
    def _aggregate(
        configs: list[EvaluatorConfig],
        results: list[EvaluationResult],
    ) -> EvaluationResponse:
        """
        Combine individual evaluator results into a single aggregated response.

        Only successful evaluator results, meaning results without an error, contribute to the weighted average score.
        Failed evaluators are counted separately and cause the aggregated response to be marked as partial.

        Args:
            configs (list[EvaluatorConfig]): The evaluator configurations used for the evaluation, including each evaluator's weight.
            results (list[EvaluationResult]): The individual results returned by the evaluators.

        Returns:
            EvaluationResponse: An aggregated response containing the individual results,
            the weighted average score, whether the result is partial, and the number of failed evaluators.
        """
        weighted_score_sum = 0.0
        weights_sum = 0.0

        for config, result in zip(configs, results, strict=True):
            if result.error is None:
                weights_sum += config.weight
                weighted_score_sum += config.weight * result.normalised_score

        weighted_average_score = weighted_score_sum / weights_sum if weights_sum != 0 else 0.0
        failure_count = sum(1 for r in results if r.error is not None)
        is_partial = failure_count > 0

        return EvaluationResponse(
            results=results,
            weighted_average_score=weighted_average_score,
            is_partial=is_partial,
            failure_count=failure_count,
        )
