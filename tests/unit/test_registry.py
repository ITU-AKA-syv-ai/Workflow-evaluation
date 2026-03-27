from app.core.models.registry import EvaluationRegistry
from tests.conftest import MockEvaluator


def test_get_fail(mock_evaluator_with_registry: EvaluationRegistry) -> None:
    invalid_evaluator_id = "abcAe27AJIdiK_wAIh"

    evaluator = mock_evaluator_with_registry.get(invalid_evaluator_id)
    assert evaluator is None


def test_get_pass(mock_evaluator_with_registry: EvaluationRegistry) -> None:
    for key in mock_evaluator_with_registry._registry:
        assert mock_evaluator_with_registry.get(key) is not None


def test_happypath_get_rule_based_evaluator(registry: EvaluationRegistry) -> None:
    evaluator = MockEvaluator()
    registry.register(evaluator.name, evaluator)
    assert registry.get(evaluator.name) is not None
