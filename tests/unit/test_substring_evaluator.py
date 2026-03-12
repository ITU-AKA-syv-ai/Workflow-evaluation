from app.core.models.substring_evaluator import (
    SubstringEvaluator,
    SubstringEvaluatorConfig,
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


def test_evaluation_happypath() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="bc")
    result = eval.evaluate(input, conf)
    assert result.passed
    assert result.reasoning == 'Substring "bc" is present.'
    assert result.normalised_score == 1


def test_evaluation_edgecase_fullstring() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="abc")
    result = eval.evaluate(input, conf)
    assert result.passed
    assert result.reasoning == 'Substring "abc" is present.'
    assert result.normalised_score == 1


def test_evaluation_edgecase_emptystring() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="")
    result = eval.evaluate(input, conf)
    assert result.passed
    assert result.normalised_score == 1
    assert result.reasoning == "The empty string is a substring of all strings."


def test_evaluation_errorpath_nonexistent() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="xyz")
    result = eval.evaluate(input, conf)
    assert not result.passed
    assert result.reasoning == 'No occurences of "xyz" found.'


def test_evaluation_partial_match() -> None:
    input = "hello bob"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="box")
    result = eval.evaluate(input, conf)
    assert not result.passed
    assert result.normalised_score == len("bo") / len("box")
    assert result.reasoning == 'Only found partial match "bo".'
