import pytest
from pydantic import ValidationError

from backend.app.core.evaluators.orchestrator import EvaluationOrchestrator
from backend.app.core.models.registry import EvaluationRegistry
from backend.app.exceptions import UnknownEvaluatorsError
from backend.tests.conftest import MockEvaluator, create_evaluation_config, create_evaluation_request


# single strategy
@pytest.mark.asyncio
async def test_single_strategy_success(
    registry: EvaluationRegistry,
    orchestrator: EvaluationOrchestrator,
) -> None:
    """A single valid evaluator should return one result with the expected score."""
    registry.register("alpha", MockEvaluator(name="alpha", score=0.9))

    resp = await orchestrator.evaluate(create_evaluation_request([create_evaluation_config("alpha")]))

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
    registry.register("high", MockEvaluator(name="high", score=1.0))
    registry.register("low", MockEvaluator(name="low", score=0.0))

    resp = await orchestrator.evaluate(
        create_evaluation_request([
            create_evaluation_config("high", weight=3.0),
            create_evaluation_config("low", weight=1.0),
        ])
    )

    assert len(resp.results) == 2
    assert resp.weighted_average_score == pytest.approx(0.75)


# invalid config: unknown evaluator id
@pytest.mark.asyncio
async def test_unknown_evaluator_id(orchestrator: EvaluationOrchestrator) -> None:
    """An unregistered evaluator_id should raise UnknownEvaluatorsError."""
    with pytest.raises(UnknownEvaluatorsError):
        await orchestrator.evaluate(create_evaluation_request([create_evaluation_config("does_not_exist")]))


# invalid config: bind returns None
@pytest.mark.asyncio
async def test_invalid_config_bind_returns_none(
    registry: EvaluationRegistry,
    orchestrator: EvaluationOrchestrator,
) -> None:
    """If bind() returns None the orchestrator should surface an 'Invalid config' error."""
    registry.register("bad_bind", MockEvaluator(name="bad_bind", config=None))

    resp = await orchestrator.evaluate(create_evaluation_request([create_evaluation_config("bad_bind")]))

    assert resp.results[0].error == "Invalid config"
    assert resp.failure_count == 1


# invalid config: negative weight
def test_negative_weight() -> None:
    """Negative weights should be rejected by Pydantic validation."""
    with pytest.raises(ValidationError):
        create_evaluation_config("nw", weight=-1.0)


# partial failure: one fails, others succeed
@pytest.mark.asyncio
async def test_partial_failure_excludes_errors_from_average(
    registry: EvaluationRegistry,
    orchestrator: EvaluationOrchestrator,
) -> None:
    """
    When one strategy fails (evaluator exception) and another succeeds,
    the weighted average should only reflect the successful results
    and the response should be flagged as partial.
    """
    registry.register("good", MockEvaluator(name="good", score=0.8))
    registry.register("failing", MockEvaluator(name="failing", raise_on_evaluate=Exception("boom")))

    resp = await orchestrator.evaluate(
        create_evaluation_request([
            create_evaluation_config("good", weight=1.0),
            create_evaluation_config("failing", weight=2.0),
        ])
    )

    assert resp.is_partial is True
    assert resp.failure_count == 1
    assert resp.weighted_average_score == pytest.approx(0.8)


# all strategies fail
@pytest.mark.asyncio
async def test_all_fail_gives_zero_average(
    registry: EvaluationRegistry,
    orchestrator: EvaluationOrchestrator,
) -> None:
    """If every evaluator errors out, weighted average should be 0."""
    registry.register("x", MockEvaluator(name="x", raise_on_evaluate=Exception("boom")))
    registry.register("y", MockEvaluator(name="y", raise_on_evaluate=Exception("boom")))

    resp = await orchestrator.evaluate(
        create_evaluation_request([create_evaluation_config("x"), create_evaluation_config("y")])
    )

    assert resp.weighted_average_score == pytest.approx(0.0)
    assert resp.failure_count == 2
    assert resp.is_partial is True
