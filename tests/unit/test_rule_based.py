from math import isclose

import pytest

from app.core.evaluators.rule_based_evaluator import (
    RuleBasedEvaluator,
    RuleBasedEvaluatorConfig,
)
from app.core.models.rules.format_rules import FormatRuleConfig
from app.core.models.rules.keyword_rules import KeywordRuleConfig
from app.core.models.rules.regex_rules import RegexRuleConfig


# BIND
def test_bind_happypath_valid_configuration() -> None:
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


def test_bind_errorpath_invalid_configuration() -> None:
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
@pytest.mark.asyncio
async def test_rulebased_happypath_all_rules_pass() -> None:
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
            ),
        ]
    )

    result = await eval.evaluate(input, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None

    assert isinstance(result.reasoning, str)
    assert "3/3 rules passed" in result.reasoning
    assert "format: pass" in result.reasoning
    assert "regex: pass" in result.reasoning
    assert "keyword: pass" in result.reasoning


@pytest.mark.asyncio
async def test_rulebased_edgecase_partial_pass() -> None:
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
    result = await eval.evaluate(input, conf)
    assert not result.passed
    assert isclose(result.normalised_score, 0.5)
    assert result.error is None

    assert isinstance(result.reasoning, str)
    assert "1/2 rules passed" in result.reasoning
    assert "format: pass" in result.reasoning
    assert "regex: fail" in result.reasoning


@pytest.mark.asyncio
async def test_rulebased_edgecase_empty_rules() -> None:
    # empty rulelist, make sure score is 0.0 and reasoning is "no rules were configured"
    input = "hello"
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(rules=[])

    result = await eval.evaluate(input, conf)
    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "No rules were configured." in result.reasoning


@pytest.mark.asyncio
async def test_rulebased_edgecase_weighted_score_aggregation() -> None:
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

    result = await eval.evaluate(output=input, config=conf)

    assert not result.passed
    assert isclose(result.normalised_score, 2.0 / 3.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "1/2 rules passed" in result.reasoning
    assert "format: pass" in result.reasoning
    assert "regex: fail" in result.reasoning


# FORMAT RULE
@pytest.mark.asyncio
async def test_format_happypath_valid_json() -> None:
    input_text = '{"key": "value"}'
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(rules=[FormatRuleConfig(name="format", kind="valid_json", weight=1.0)])

    result = await eval.evaluate(input_text, conf)
    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert isinstance(result.reasoning, str)
    assert "format: pass" in result.reasoning
    assert "Output is valid JSON" in result.reasoning


@pytest.mark.asyncio
async def test_format_edgecase_invalid_json() -> None:
    input_text = '{"key": "value"'  # missing closing }
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(rules=[FormatRuleConfig(name="format", kind="valid_json", weight=1.0)])

    result = await eval.evaluate(input_text, conf)
    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert isinstance(result.reasoning, str)
    assert "format: fail" in result.reasoning
    assert "Output is not valid JSON" in result.reasoning


@pytest.mark.asyncio
async def test_format_happypath_max_length_within_limit() -> None:
    input_text = "Hello"
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(
        rules=[FormatRuleConfig(name="format", kind="max_length", max_length=10, weight=1.0)]
    )

    result = await eval.evaluate(input_text, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "format: pass" in result.reasoning
    assert "1/1 rules passed"
    assert "Output length 5 is within max length 10." in result.reasoning


@pytest.mark.asyncio
async def test_format_edgecase_max_length_exceeded() -> None:
    input_text = "Hello, this is too long"
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(
        rules=[FormatRuleConfig(name="format", kind="max_length", max_length=5, weight=1.0)]
    )

    result = await eval.evaluate(input_text, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "format: fail" in result.reasoning
    assert "0/1 rules passed"
    assert "Output length 23 exceeds max length 5" in result.reasoning


@pytest.mark.asyncio
async def test_format_edgecase_max_length_none() -> None:
    input_text = "Hello"
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(
        rules=[FormatRuleConfig(name="format", kind="max_length", max_length=None, weight=1.0)]
    )

    result = await eval.evaluate(input_text, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "format: fail" in result.reasoning
    assert "0/1 rules passed"
    assert "Format rule kind 'max_length' requires 'max_length' to be set." in result.reasoning


# KEYWORD RULE
@pytest.mark.asyncio
async def test_keyword_happypath_required_keyword_present() -> None:
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

    result = await eval.evaluate(input, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "1/1 rules passed" in result.reasoning
    assert "keyword: pass" in result.reasoning


@pytest.mark.asyncio
async def test_keyword_edgecase_required_partial_match() -> None:
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

    result = await eval.evaluate(input, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "0/1 rules passed" in result.reasoning
    assert "keyword: fail" in result.reasoning
    assert "A close match 'hel' was found." in result.reasoning


@pytest.mark.asyncio
async def test_keyword_edgecase_required_no_match() -> None:
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

    result = await eval.evaluate(input, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "0/1 rules passed" in result.reasoning
    assert "keyword: fail" in result.reasoning
    assert "No close match was found." in result.reasoning


@pytest.mark.asyncio
async def test_keyword_happypath_forbidden_keyword_not_present() -> None:
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

    result = await eval.evaluate(input, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "1/1 rules passed" in result.reasoning
    assert "keyword: pass" in result.reasoning
    assert "not present" in result.reasoning


@pytest.mark.asyncio
async def test_keyword_happypath_forbidden_keyword_present() -> None:
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

    result = await eval.evaluate(input, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "1/1 rules passed" not in result.reasoning
    assert "keyword: fail" in result.reasoning
    assert "is present" in result.reasoning


@pytest.mark.asyncio
async def test_keyword_edgecase_forbidden_partial_match_not_found() -> None:
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

    result = await eval.evaluate(input, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "1/1 rules passed" in result.reasoning
    assert "keyword: pass" in result.reasoning
    assert "not present" in result.reasoning


@pytest.mark.asyncio
async def test_keyword_edgecase_required_empty_string() -> None:
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

    result = await eval.evaluate(input, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "0/1 rules passed" in result.reasoning
    assert "keyword: fail" in result.reasoning
    assert "An empty string is not a valid keyword." in result.reasoning


@pytest.mark.asyncio
async def test_keyword_edgecase_forbidden_empty_string() -> None:
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

    result = await eval.evaluate(input, conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "0/1 rules passed" in result.reasoning
    assert "keyword: fail" in result.reasoning
    assert "An empty string will always fail the forbidden keyword rule." in result.reasoning


# REGEX RULE
@pytest.mark.asyncio
async def test_regex_edgecase_invalid_pattern_is_handled_gracefully() -> None:
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

    result = await eval.evaluate(output=input, config=conf)

    assert not result.passed
    assert isclose(result.normalised_score, 0.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "1/1 rules passed" not in result.reasoning
    assert "regex: fail" in result.reasoning
    assert "Invalid regex pattern" in result.reasoning


@pytest.mark.asyncio
async def test_regex_edgecase_empty_pattern() -> None:
    # The empty string is a valid regex pattern.
    input_text = "Some text here"
    eval = RuleBasedEvaluator()
    conf = RuleBasedEvaluatorConfig(rules=[RegexRuleConfig(name="regex", pattern="", weight=1.0)])

    result = await eval.evaluate(input_text, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "regex: pass" in result.reasoning
    assert "Pattern matched" in result.reasoning


@pytest.mark.asyncio
async def test_regex_happypath_multiline_groups_complex() -> None:
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

    result = await eval.evaluate(input_text, conf)

    assert result.passed
    assert isclose(result.normalised_score, 1.0)
    assert result.error is None
    assert isinstance(result.reasoning, str)
    assert "regex: pass" in result.reasoning
