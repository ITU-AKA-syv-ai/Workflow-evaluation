from math import isclose

from app.core.engine.rule_based import (
    RuleBasedEvaluator,
    RuleBasedEvaluatorConfig,
)
from app.core.models.rules.format_rules import FormatRuleConfig
from app.core.models.rules.regex_rules import RegexRuleConfig


# TODO add keyword throughout tests
def test_bind_happypath() -> None:
    eval = RuleBasedEvaluator()
    conf = {
        "rules": [
            {
                "name": "format",
                "kind": "valid_json",
                "weight": 1.0,
            }
        ]
    }
    bound_conf = eval.validate_config(conf)
    assert bound_conf is not None
    assert len(bound_conf.rules) == 1


def test_bind_errorpath() -> None:
    # wrong/invalid rule in list
    eval = RuleBasedEvaluator()

    # case 1: missing rules
    conf = {}
    assert eval.validate_config(conf) is None

    # case 2: rules not a list
    conf2 = {"rules": "not a list"}
    assert eval.validate_config(conf2) is None

    # case 3: missing kind in format
    conf3 = {
        "rules": [
            {
                "name": "format",
                # missing "kind"
            }
        ]
    }
    assert eval.validate_config(conf3) is None


def test_evaluation_happypath() -> None:
    input = '{"message": "hello"}'
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(
        rules=[
            FormatRuleConfig(
                name="format",
                kind="valid_json",
                weight=1.0,
            ),
            RegexRuleConfig(
                name="regex",
                pattern="hello",
                weight=1.0,
            ),
        ]
    )

    result = eval.evaluate(input, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert "2/2 rules passed" in result.reasoning
    assert "format: pass" in result.reasoning
    assert "regex: pass" in result.reasoning


def test_evaluation_edgecase_partial_pass() -> None:
    input = '{"message": "hello"}'
    eval = RuleBasedEvaluator()

    conf = RuleBasedEvaluatorConfig(
         rules=[
             FormatRuleConfig(
                 name="format",
                 kind="valid_json",
                 weight=1.0,
             ),
             RegexRuleConfig(
                 name="regex",
                 pattern="not hello",
                 weight=1.0,
             ),
         ]
     )
    result = eval.evaluate(input, conf)
    assert not result.passed
    assert isclose(result.normalised_score, 0.5)
    assert result.error is None

    assert "1/2 rules passed" in result.reasoning
    assert "format: pass" in result.reasoning
    assert "regex: fail" in result.reasoning


# def test_evaluation_edgecase_empty_rules() -> None:
#     # empty rulelist, make sure score is 0.0 and reasoning is "no rules were configured"
#
# def test_evaluation_edgecase_weighted_score() -> None:
#     # partial success of rules with different weight, make sure aggregated score is correct
#
# def test_evaluation_regex_invalid_is_handled_gracefully() -> None:
#     # regex rule invalid. Make sure normal result is returned, reasoning "invalid regex"
