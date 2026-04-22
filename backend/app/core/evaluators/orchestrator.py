import asyncio
import logging
import time

from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
    EvaluatorConfig,
)
from app.core.models.registry import EvaluationRegistry
from app.logging.context import evaluator_id_ctx

logger = logging.getLogger(__name__)

# Per-evaluator timeout. This fires before Celery's task-level soft_time_limit,
# allowing graceful per-evaluator failure rather than catastrophic task interruption.
DEFAULT_EVALUATOR_TIMEOUT_SECONDS = 60.0


class EvaluationOrchestrator:
    """Coordinates running multiple evaluation strategies and aggregating results.

    The orchestrator is queue-agnostic: it knows nothing about Celery, FastAPI, or
    any other transport. It can be invoked from a Celery task (via asyncio.run),
    from a script, or directly from an async route handler.

    Validation of the EvaluationRequest is the caller's responsibility and should
    happen synchronously before this orchestrator is invoked, so that invalid
    requests fail fast rather than being queued.
    """

    def __init__(
        self,
        registry: EvaluationRegistry,
        evaluator_timeout_seconds: float = DEFAULT_EVALUATOR_TIMEOUT_SECONDS,
    ) -> None:
        """
        Initialize the orchestrator with an evaluator registry.

        Args:
            registry: The registry used to look up evaluators by ID.
            evaluator_timeout_seconds: Per-evaluator timeout. An evaluator that
                exceeds this is recorded as a failed result rather than aborting
                the entire request.
        """
        self._registry = registry
        self._evaluator_timeout_seconds = evaluator_timeout_seconds

    async def evaluate(self, req: EvaluationRequest) -> EvaluationResponse:
        """
        Execute all evaluators for a request concurrently and return an aggregated result.

        Logs evaluation lifecycle events and excludes failed evaluators from the
        final score. Per-evaluator failures (including timeouts) do not abort the
        overall request; the response is marked partial instead.
        """
        logger.info(
            "evaluation_started",
            extra={"num_strategies": len(req.configs)},
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("evaluation_request_payload", extra={"payload": req.model_output})

        start = time.monotonic()

        tasks = [self._evaluate_single(req, config) for config in req.configs]
        results = await asyncio.gather(*tasks)
        response = self._aggregate(req.configs, list(results))

        duration = time.monotonic() - start

        logger.info(
            "evaluation_completed",
            extra={
                "execution_time": duration,
                "failure_count": response.failure_count,
                "is_partial": response.is_partial,
            },
        )

        return response

    async def _evaluate_single(
        self,
        req: EvaluationRequest,
        evaluator_config: EvaluatorConfig,
    ) -> EvaluationResult:
        """
        Evaluate a single evaluator configuration against the provided output.

        Returns an EvaluationResult in all cases — exceptions and timeouts are
        captured as failed results so one bad evaluator does not break the batch.
        """
        evaluator_id_ctx.set(evaluator_config.evaluator_id)

        logger.info("strategy_started")
        start = time.monotonic()

        evaluator = self._registry.get(evaluator_config.evaluator_id)

        # evaluator_config.config is a generic dict[str, Any] from the request payload.
        # Each evaluator declares its own typed config schema (e.g. SubstringEvaluatorConfig
        # for the substring evaluator). validate_config converts the generic dict into the
        # typed config the evaluator expects, returning None if the dict is malformed.
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

        try:
            result = await asyncio.wait_for(
                evaluator.evaluate(req.model_output, cfg, evaluator_config.threshold),
                timeout=self._evaluator_timeout_seconds,
            )
        except asyncio.TimeoutError:
            duration = time.monotonic() - start
            logger.warning(
                "strategy_timed_out",
                extra={"execution_time": duration},
            )
            return EvaluationResult(
                evaluator_id=evaluator_config.evaluator_id,
                reasoning=f"Evaluator exceeded {self._evaluator_timeout_seconds}s timeout",
                error="Timeout",
            )
        except Exception as e:
            # Catch-all so a single misbehaving evaluator never aborts the gather.
            # Specific evaluators should ideally catch their own expected failure
            # modes; this is a safety net for the unexpected.
            duration = time.monotonic() - start
            logger.exception(
                "strategy_raised_unexpected_exception",
                extra={"execution_time": duration},
            )
            return EvaluationResult(
                evaluator_id=evaluator_config.evaluator_id,
                reasoning="Evaluator raised an unexpected exception",
                error=str(e),
            )

        duration = time.monotonic() - start

        if result.error:
            logger.warning(
                "strategy_completed_with_error",
                extra={"execution_time": duration, "error": result.error},
            )
        else:
            logger.info(
                "strategy_completed_success",
                extra={"execution_time": duration, "score": result.normalised_score},
            )

        return result

    @staticmethod
    def _aggregate(
        configs: list[EvaluatorConfig],
        results: list[EvaluationResult],
    ) -> EvaluationResponse:
        """
        Combine individual evaluator results into a single aggregated response.

        Only successful evaluator results (no error) contribute to the weighted
        average score. Failed evaluators are counted separately and cause the
        aggregated response to be marked partial.
        """
        weighted_score_sum = 0.0
        weights_sum = 0.0

        for config, result in zip(configs, results, strict=True):
            if result.error is None:
                weights_sum += config.weight
                weighted_score_sum += config.weight * result.normalised_score

        weighted_average_score = (
            weighted_score_sum / weights_sum if weights_sum != 0 else 0.0
        )
        failure_count = sum(1 for r in results if r.error is not None)
        is_partial = failure_count > 0

        return EvaluationResponse(
            results=results,
            weighted_average_score=weighted_average_score,
            is_partial=is_partial,
            failure_count=failure_count,
        )