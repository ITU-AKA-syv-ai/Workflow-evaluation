from app.core.models.registry import EvaluationRegistry
from tests.conftest import MockEvaluator


def _random_registry() -> EvaluationRegistry:
    registry = EvaluationRegistry()
    evaluator = MockEvaluator()
    registry.register(evaluator.name, evaluator)

    return registry


def test_get_fail() -> None:
    invalid_evaluator_id = "abcAe27AJIdiK_wAIh"

    registry = _random_registry()
    evaluator = registry.get(invalid_evaluator_id)
    assert evaluator is None


def test_get_pass() -> None:
    registry = _random_registry()
    for key in registry._registry:
        assert registry.get(key) is not None


def test_happypath_get_rule_based_evaluator() -> None:
    registry = EvaluationRegistry()

    evaluator = MockEvaluator()
    registry.register(evaluator.name, evaluator)
    assert registry.get(evaluator.name) is not None


def test_get_length_evaluator() -> None:
    registry = _random_registry()
    evaluator = MockEvaluator()
    assert registry.get(evaluator.name) is not None
