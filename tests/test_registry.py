from app.core.models.length_evaluator import LengthEvaluator
from app.core.models.registry import registry


def test_get_fail() -> None:
    invalid_evaluator_id = "abcAe27AJIdiK_wAIh"
    evaluator = registry.get(invalid_evaluator_id)
    assert evaluator is None


def test_get_pass() -> None:
    for key in registry.registry:
        assert registry.get(key) is not None


def test_get_length_evaluator() -> None:
    assert registry.get(LengthEvaluator().name) is not None
