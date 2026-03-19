import pytest

from app.core.engine.orchestrator import EvaluationOrchestrator
from app.core.models.evaluation_model import EvaluationResponse, EvaluationResult, EvaluatorConfig


def test_aggregate_weighted_average() -> None:
    configs = [
        EvaluatorConfig(
            evaluator_id="a",
            weight=2,
            threshold=0.5,
            config={},
        ),
        EvaluatorConfig(
            evaluator_id="b",
            weight=1,
            threshold=0.5,
            config={},
        ),
    ]

    results = [
        EvaluationResult(
            evaluator_id="a",
            normalised_score=0.5,
            error=None,
        ),
        EvaluationResult(
            evaluator_id="b",
            normalised_score=1.0,
            error=None,
        ),
    ]

    response = EvaluationOrchestrator._aggregate(configs, results)

    assert response.weighted_average_score == pytest.approx((2 * 0.5 + 1 * 1.0) / 3)
    assert response.is_partial is False
    assert response.failure_count == 0
    assert response.results == results