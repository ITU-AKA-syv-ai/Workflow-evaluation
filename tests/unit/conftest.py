from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.evaluation_model import EvaluationResult
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

    evaluator.validate_config.return_value = None if validate_config_returns_none else MagicMock(
        name="bound_config")

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


@pytest.fixture()
def registry() -> EvaluationRegistry:
    return EvaluationRegistry()


@pytest.fixture()
def orchestrator(registry: EvaluationRegistry) -> EvaluationOrchestrator:
    return EvaluationOrchestrator(registry=registry)
