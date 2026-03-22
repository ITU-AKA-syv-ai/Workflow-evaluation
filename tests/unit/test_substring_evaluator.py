import pytest

from app.core.models.substring_evaluator import (
    SubstringEvaluator,
    SubstringEvaluatorConfig,
    find_almost_substring,
)


def test_bind_happypath() -> None:
    conf = {"substring": "test"}
    bound_conf = SubstringEvaluator().bind(conf)
    assert bound_conf is not None
    assert bound_conf.substring == "test"


def test_bind_edgecase_edgecase() -> None:
    conf = {"substring": ""}
    bound_conf = SubstringEvaluator().bind(conf)
    assert bound_conf is not None
    assert bound_conf.substring == ""


def test_bind_edgecase_errorpath_int() -> None:
    conf = {"substring": 23}
    bound_conf = SubstringEvaluator().bind(conf)
    assert bound_conf is None


def test_bind_edgecase_errorpath_float() -> None:
    conf = {"substring": 5.4}
    bound_conf = SubstringEvaluator().bind(conf)
    assert bound_conf is None


def test_bind_edgecase_errorpath_bool() -> None:
    conf = {"substring": True}
    bound_conf = SubstringEvaluator().bind(conf)
    assert bound_conf is None


@pytest.mark.asyncio
async def test_evaluation_happypath() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="bc")
    result = await eval.evaluate(input, conf)
    assert result.passed
    assert result.reasoning == 'Substring "bc" is present.'
    assert result.normalised_score == 1


@pytest.mark.asyncio
async def test_evaluation_edgecase_fullstring() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="abc")
    result = await eval.evaluate(input, conf)
    assert result.passed
    assert result.reasoning == 'Substring "abc" is present.'
    assert result.normalised_score == 1


@pytest.mark.asyncio
async def test_evaluation_edgecase_emptystring() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="")
    result = await eval.evaluate(input, conf)
    assert result.passed
    assert result.normalised_score == 1
    assert result.reasoning == "The empty string is a substring of all strings."


@pytest.mark.asyncio
async def test_evaluation_errorpath_nonexistent() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="xyz")
    result = await eval.evaluate(input, conf)
    assert not result.passed
    assert result.reasoning == 'No occurences of "xyz" found.'


@pytest.mark.asyncio
async def test_evaluation_partial_match() -> None:
    input = "hello bob"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="box")
    result = await eval.evaluate(input, conf)
    assert not result.passed
    assert result.normalised_score == len("bo") / len("box")
    assert result.reasoning == 'Only found partial match "bo".'


def test_almost_substring_full_match_1() -> None:
    needle = "proper substring"
    haystack = "abc proper proper proper example proper substring distraction proper"
    assert find_almost_substring(needle, haystack) == needle


def test_almost_substring_full_match_2() -> None:
    needle = "because"
    haystack = "The missile knows where it is at all times, it konws this because it knows where it isn't."
    assert find_almost_substring(needle, haystack) == needle


def test_almost_substring_partial_match_1() -> None:
    needle = "love"
    haystack = "I loathe testing"
    assert find_almost_substring(needle, haystack) == "lo"


def test_almost_substring_partial_match_2() -> None:
    needle = "abcd"
    haystack = "abce"
    assert find_almost_substring(needle, haystack) == "abc"


def test_almost_substring_partial_no_match() -> None:
    needle = "does not exist"
    haystack = "yup"
    assert find_almost_substring(needle, haystack) == ""
