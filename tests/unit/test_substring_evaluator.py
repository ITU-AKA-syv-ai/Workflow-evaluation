from app.core.models.substring_evaluator import (
    SubstringEvaluator,
    SubstringEvaluatorConfig,
)


def test_bind() -> None:
    conf = {"substring": "test"}
    bound_conf = SubstringEvaluator().bind(conf)
    assert bound_conf is not None
    assert bound_conf.substring == "test"


def test_evaluation_happypath() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="bc")
    result = eval.evaluate(input, conf)
    assert result.passed


def test_evaluation_edgecase_fullstring() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="abc")
    result = eval.evaluate(input, conf)
    assert result.passed


def test_evaluation_edgecase_emptystring() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="")
    result = eval.evaluate(input, conf)
    assert result.passed


def test_evaluation_errorpath_nonexistent() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="xyz")
    result = eval.evaluate(input, conf)
    assert not result.passed
