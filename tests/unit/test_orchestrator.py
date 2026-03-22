from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResult,
    EvaluatorConfig,
)
from app.core.models.registry import EvaluationRegistry


def make_mock_evaluator(
    *,
    name: str = "mock_eval",
    score: float = 0.8,
    validate_config_returns_none: bool = False,
    raise_on_evaluate: Exception | None = None,
) -> MagicMock:
    """
    Factory that builds a mock evaluator whose bind() and evaluate() behaviour
    can be controlled per-test.
    """
    evaluator = MagicMock()
    evaluator.name = name

    evaluator.validate_config.return_value = None if validate_config_returns_none else MagicMock(name="bound_config")

    if raise_on_evaluate is not None:
        evaluator.evaluate = AsyncMock(side_effect=raise_on_evaluate)
    else:
        evaluator.evaluate = AsyncMock(
            return_value=EvaluationResult(
                evaluator_id=name,
                passed=True,
                normalised_score=score,
                reasoning="Mock reasoning",
            )
        )

    return evaluator


# helpers
def _make_request(*configs: EvaluatorConfig) -> EvaluationRequest:
    return EvaluationRequest(model_output="hello world", configs=list(configs))


def _cfg(evaluator_id: str, weight: float = 1.0, **extra: object) -> EvaluatorConfig:
    return EvaluatorConfig(
        evaluator_id=evaluator_id,
        weight=weight,
        config=extra,
    )


# single strategy
@pytest.mark.asyncio
async def test_single_strategy_success(
    registry: EvaluationRegistry,
    orchestrator: EvaluationOrchestrator,
) -> None:
    """A single valid evaluator should return one result with the expected score."""
    registry.register("alpha", make_mock_evaluator(name="alpha", score=0.9))

    resp = await orchestrator.evaluate(_make_request(_cfg("alpha")))

    assert len(resp.results) == 1
    assert resp.results[0].evaluator_id == "alpha"
    assert resp.results[0].normalised_score == pytest.approx(0.9)
    assert resp.results[0].error is None
    assert resp.weighted_average_score == pytest.approx(0.9)
    assert resp.is_partial is False
    assert resp.failure_count == 0


@pytest.mark.asyncio
async def test_weighted_average_with_different_weights(
    registry: EvaluationRegistry,
    orchestrator: EvaluationOrchestrator,
) -> None:
    """
    Two evaluators with weights 3 and 1 scoring 1.0 and 0.0 respectively
    should give a weighted average of 0.75.
    """
    registry.register("high", make_mock_evaluator(name="high", score=1.0))
    registry.register("low", make_mock_evaluator(name="low", score=0.0))

    resp = await orchestrator.evaluate(_make_request(_cfg("high", weight=3.0), _cfg("low", weight=1.0)))

    assert len(resp.results) == 2
    assert resp.weighted_average_score == pytest.approx(0.75)


# invalid config: unknown evaluator id
@pytest.mark.asyncio
async def test_unknown_evaluator_id(orchestrator: EvaluationOrchestrator) -> None:
    """An unregistered evaluator_id should produce an error result, not raise."""
    resp = await orchestrator.evaluate(_make_request(_cfg("does_not_exist")))

    result = resp.results[0]
    assert result.error == "Invalid evaluator_id"
    assert result.normalised_score == 0
    assert resp.failure_count == 1
    assert resp.is_partial is True


# invalid config: bind returns None
@pytest.mark.asyncio
async def test_invalid_config_bind_returns_none(
    registry: EvaluationRegistry,
    orchestrator: EvaluationOrchestrator,
) -> None:
    """If bind() returns None the orchestrator should surface an 'Invalid config' error."""
    registry.register(
        "bad_bind",
        make_mock_evaluator(name="bad_bind", validate_config_returns_none=True),
    )

    resp = await orchestrator.evaluate(_make_request(_cfg("bad_bind")))

    assert resp.results[0].error == "Invalid config"
    assert resp.failure_count == 1


# invalid config: negative weight
@pytest.mark.asyncio
async def test_negative_weight(
    registry: EvaluationRegistry,
    orchestrator: EvaluationOrchestrator,
) -> None:
    """Negative weights should be rejected with an error result."""
    registry.register("nw", make_mock_evaluator(name="nw"))

    resp = await orchestrator.evaluate(_make_request(_cfg("nw", weight=-1.0)))

    assert resp.results[0].error == "Negative weight"
    assert resp.failure_count == 1


# partial failure: one fails, others succeed
@pytest.mark.asyncio
async def test_partial_failure_excludes_errors_from_average(
    registry: EvaluationRegistry,
    orchestrator: EvaluationOrchestrator,
) -> None:
    """
    When one strategy fails (unknown id) and another succeeds,
    the weighted average should only reflect the successful results
    and the response should be flagged as partial.
    """
    registry.register("good", make_mock_evaluator(name="good", score=0.8))

    resp = await orchestrator.evaluate(
        _make_request(
            _cfg("good", weight=1.0),
            _cfg("missing", weight=2.0),
        )
    )

    assert resp.is_partial is True
    assert resp.failure_count == 1
    assert resp.weighted_average_score == pytest.approx(0.8)


# all strategies fail
@pytest.mark.asyncio
async def test_all_fail_gives_zero_average(orchestrator: EvaluationOrchestrator) -> None:
    """If every evaluator errors out, weighted average should be 0."""
    resp = await orchestrator.evaluate(_make_request(_cfg("x"), _cfg("y")))

    assert resp.weighted_average_score == pytest.approx(0.0)
    assert resp.failure_count == 2
    assert resp.is_partial is True
