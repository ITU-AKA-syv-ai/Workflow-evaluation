from app.core.models.substring_evaluator import (
    SubstringEvaluator,
    SubstringEvaluatorConfig,
)


def test_bind() -> None:
    conf = {"substring": "test"}
    bound_conf = SubstringEvaluator().validate_config(conf)
    assert bound_conf is not None
    assert bound_conf.substring == "test"


def test_evaluation_happypath() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="bc")
    assert eval.evaluate(input, conf)


def test_evaluation_edgecase_fullstring() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="abc")
    assert eval.evaluate(input, conf)


def test_evaluation_edgecase_emptystring() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="")
    assert eval.evaluate(input, conf)


def test_evaluation_errorpath_nonexistent() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="xyz")
    assert not eval.evaluate(input, conf)
