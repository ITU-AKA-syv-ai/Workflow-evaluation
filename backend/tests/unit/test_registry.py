import pytest

from app.core.models.registry import EvaluationRegistry
from tests.conftest import MockEvaluator


def test_get_fail(mock_evaluator_with_registry: EvaluationRegistry) -> None:
    invalid_evaluator_id = "abcAe27AJIdiK_wAIh"

    with pytest.raises(KeyError):
        mock_evaluator_with_registry.get(invalid_evaluator_id)


def test_get_pass(mock_evaluator_with_registry: EvaluationRegistry) -> None:
    for key in mock_evaluator_with_registry._registry:
        assert mock_evaluator_with_registry.get(key) is not None


def test_happypath_get_rule_based_evaluator(registry: EvaluationRegistry) -> None:
    evaluator = MockEvaluator()
    registry.register(evaluator.name, evaluator)
    assert registry.get(evaluator.name) is not None


def test_happtypath_register(registry: EvaluationRegistry) -> None:
    registry.register(MockEvaluator().name, MockEvaluator())
    assert registry.get(MockEvaluator().name) is not None


def test_register_fail_same_id(registry: EvaluationRegistry) -> None:
    evaluator = MockEvaluator()
    registry.register("id", evaluator)
    assert registry.register("id", evaluator) is False


def test_register_fail_empty_id(registry: EvaluationRegistry) -> None:
    with pytest.raises(ValueError):
        registry.register("", MockEvaluator())


def test_register_fail_evaluator_none(registry: EvaluationRegistry) -> None:
    with pytest.raises(ValueError):
        registry.register("", MockEvaluator())
