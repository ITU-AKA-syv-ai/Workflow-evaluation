from math import isclose

from app.core.evaluators.rule_based_evaluator import (
    RuleBasedEvaluator,
    RuleBasedEvaluatorConfig,
)
from app.core.models.rules.format_rules import FormatRuleConfig
from app.core.models.rules.keyword_rules import KeywordRuleConfig
from app.core.models.rules.regex_rules import RegexRuleConfig


# BIND
def test_bind_happypath() -> None:
    eval = RuleBasedEvaluator()
    conf = {
        "rules": [
            {
                "name": "format",
                "kind": "valid_json",
                "weight": 1.0,
            },
            {
                "name": "regex",
                "pattern": "bye",
                "weight": 1.0,
            },
            {
                "name": "keyword",
                "kind": "forbidden",
                "keyword": "hello",
                "weight": 1.0,
            },
        ]
    }
    bound_conf = eval.validate_config(conf)
    assert bound_conf is not None
    assert len(bound_conf.rules) == 3


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

    conf4 = {
        "rules": [
            {
                "name": "keyword",
                "kind": "forbidden",
                # missing "keyword"
            }
        ]
    }

    assert eval.validate_config(conf4) is None


# RULE-BASED EVALUATOR
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
            KeywordRuleConfig(
                name="keyword",
                kind="required",
                keyword="hello",
            )
        ]
    )

    result = eval.evaluate(input, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert "3/3 rules passed" in result.reasoning
    assert "format: pass" in result.reasoning
    assert "regex: pass" in result.reasoning
    assert "keyword: pass" in result.reasoning


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


def test_evaluation_edgecase_empty_rules() -> None:
    # empty rulelist, make sure score is 0.0 and reasoning is "no rules were configured"
    input = "hello"
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(rules=[])

    result = eval.evaluate(input, conf)
    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert "No rules were configured." in result.reasoning


def test_evaluation_edgecase_weighted_score() -> None:
    # partial success of rules with different weight, make sure aggregated score is correct
    input = '{"message": "hello"}'
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(
        rules=[
            FormatRuleConfig(
                name="format",
                kind="valid_json",
                weight=2.0,
            ),
            RegexRuleConfig(
                name="regex",
                pattern="bye",
                weight=1.0,
            ),
        ]
    )

    result = eval.evaluate(output=input, config=conf)

    assert not result.passed
    assert isclose(result.normalised_score, 2.0 / 3.0)
    assert result.error is None
    assert "1/2 rules passed" in result.reasoning
    assert "format: pass" in result.reasoning
    assert "regex: fail" in result.reasoning


# FORMAT RULE
# KEYWORD RULE
def test_evaluation_keyword_required_match_happypath() -> None:
    input = "This response contains hello."
    eval = RuleBasedEvaluator()

    conf = RuleBasedEvaluatorConfig(
        rules=[
            KeywordRuleConfig(
                name="keyword",
                kind="required",
                keyword="hello",
                weight=1.0,
            )
        ]
    )

    result = eval.evaluate(input, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert "1/1 rules passed" in result.reasoning
    assert "keyword: pass" in result.reasoning


def test_evaluation_keyword_required_partial_match_happypath() -> None:
    input = "This response contains hello."
    eval = RuleBasedEvaluator()

    conf = RuleBasedEvaluatorConfig(
        rules=[
            KeywordRuleConfig(
                name="keyword",
                kind="required",
                keyword="hel",
                weight=1.0,
            )
        ]
    )

    result = eval.evaluate(input, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert "0/1 rules passed" in result.reasoning
    assert "keyword: fail" in result.reasoning
    assert "A close match 'hel' was found." in result.reasoning


def test_evaluation_keyword_required_no_match_happypath() -> None:
    input = "This response contains hello."
    eval = RuleBasedEvaluator()

    conf = RuleBasedEvaluatorConfig(
        rules=[
            KeywordRuleConfig(
                name="keyword",
                kind="required",
                keyword="xyz",
                weight=1.0,
            )
        ]
    )

    result = eval.evaluate(input, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert "0/1 rules passed" in result.reasoning
    assert "keyword: fail" in result.reasoning
    assert "No close match was found." in result.reasoning


def test_evaluation_keyword_forbidden_notfound_happypath() -> None:
    input = "This response does not contain the forbidden keyword."
    eval = RuleBasedEvaluator()

    conf = RuleBasedEvaluatorConfig(
        rules=[
            KeywordRuleConfig(
                name="keyword",
                kind="forbidden",
                keyword="hello",
                weight=1.0,
            )
        ]
    )

    result = eval.evaluate(input, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert "1/1 rules passed" in result.reasoning
    assert "keyword: pass" in result.reasoning
    assert "not present" in result.reasoning


def test_evaluation_keyword_forbidden_found_happypath() -> None:
    input = "This response contains hello."
    eval = RuleBasedEvaluator()

    conf = RuleBasedEvaluatorConfig(
        rules=[
            KeywordRuleConfig(
                name="keyword",
                kind="forbidden",
                keyword="hello",
                weight=1.0,
            )
        ]
    )

    result = eval.evaluate(input, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert "1/1 rules passed" not in result.reasoning
    assert "keyword: fail" in result.reasoning
    assert "is present" in result.reasoning


def test_evaluation_keyword_forbidden_partial_match_notfound_edgecase() -> None:
    input = "I feel very brainy"
    eval = RuleBasedEvaluator()

    conf = RuleBasedEvaluatorConfig(
        rules=[
            KeywordRuleConfig(
                name="keyword",
                kind="forbidden",
                keyword="brain",
                weight=1.0,
            )
        ]
    )

    result = eval.evaluate(input, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert "1/1 rules passed" in result.reasoning
    assert "keyword: pass" in result.reasoning
    assert "not present" in result.reasoning


def test_evaluation_keyword_required_empty_string_edgecase() -> None:
    input = "Some random text"
    eval = RuleBasedEvaluator()

    conf = RuleBasedEvaluatorConfig(
        rules=[
            KeywordRuleConfig(
                name="keyword",
                kind="required",
                keyword="",  # empty string edge case
                weight=1.0,
            )
        ]
    )

    result = eval.evaluate(input, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert "0/1 rules passed" in result.reasoning
    assert "keyword: fail" in result.reasoning
    assert "An empty string is not a valid keyword." in result.reasoning


def test_evaluation_keyword_forbidden_empty_string_edgecase() -> None:
    input = "Some random text"
    eval = RuleBasedEvaluator()

    conf = RuleBasedEvaluatorConfig(
        rules=[
            KeywordRuleConfig(
                name="keyword",
                kind="forbidden",
                keyword="",  # empty string edge case
                weight=1.0,
            )
        ]
    )

    result = eval.evaluate(input, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert "0/1 rules passed" in result.reasoning
    assert "keyword: fail" in result.reasoning
    assert "An empty string will always fail the forbidden keyword rule." in result.reasoning


# REGEX RULE
def test_evaluation_regex_invalid_is_handled_gracefully() -> None:
    # regex rule invalid. Make sure normal result is returned, reasoning "invalid regex"
    input = "hello"
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(
        rules=[
            RegexRuleConfig(
                name="regex",
                pattern="(",
                weight=1.0,
            )
        ]
    )

    result = eval.evaluate(output=input, config=conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert "1/1 rules passed" not in result.reasoning
    assert "regex: fail" in result.reasoning
    assert "Invalid regex pattern" in result.reasoning


def test_regex_empty_pattern_edgecase() -> None:
    # The empty string is a valid regex pattern.
    input_text = "Some text here"
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(
        rules=[RegexRuleConfig(name="regex", pattern="", weight=1.0)]
    )

    result = eval.evaluate(input_text, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert "regex: pass" in result.reasoning
    assert "Pattern matched" in result.reasoning


def test_regex_multiline_and_groups_complex() -> None:
    # Complex regex: multiline input with groups
    input_text = """Name: John Doe
Age: 29
Email: john@example.com"""
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(
        rules=[
            RegexRuleConfig(
                name="regex",
                pattern=r"Name: (\w+ \w+)\nAge: (\d+)\nEmail: (\S+@\S+)",
                weight=1.0,
            )
        ]
    )

    result = eval.evaluate(input_text, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert "regex: pass" in result.reasoning