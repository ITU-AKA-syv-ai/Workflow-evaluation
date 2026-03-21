from app.core.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.core.models.registry import registry


def test_get_fail() -> None:
    invalid_evaluator_id = "abcAe27AJIdiK_wAIh"
    evaluator = registry.get(invalid_evaluator_id)
    assert evaluator is None


def test_get_pass() -> None:
    for key in registry.registry:
        assert registry.get(key) is not None


def test_happypath_get_rule_based_evaluator() -> None:
    assert registry.get(RuleBasedEvaluator().name) is not None
