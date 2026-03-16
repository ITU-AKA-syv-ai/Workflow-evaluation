from math import isclose

from app.core.models.length_evaluator import LengthEvaluator, LengthEvaluatorConfig


def test_bind_happypath() -> None:
    expected_length = 10
    eval = LengthEvaluator()
    conf = {"expected_length": expected_length}
    bound_conf = eval.bind(conf)
    assert bound_conf is not None
    assert bound_conf.expected_length == expected_length


def test_bind_errorpath() -> None:
    eval = LengthEvaluator()
    conf = {"expected_length": -1}
    bound_conf = eval.bind(conf)
    assert bound_conf is None


def test_evaluation_happypath() -> None:
    input = "abc"
    eval = LengthEvaluator()
    conf = LengthEvaluatorConfig(expected_length=len(input))
    result = eval.evaluate(input, conf)
    assert result.passed
    assert result.normalised_score == 1


def test_evaluation_edgecase_1() -> None:
    input = "a"
    eval = LengthEvaluator()
    conf = LengthEvaluatorConfig(expected_length=len(input) + 1)
    result = eval.evaluate(input, conf)
    assert not result.passed
    assert isclose(result.normalised_score, 1 / 2)


def test_evaluation_edgecase_2() -> None:
    input = "abc"
    eval = LengthEvaluator()
    conf = LengthEvaluatorConfig(expected_length=len(input) + 1)
    result = eval.evaluate(input, conf)
    assert not result.passed
    assert isclose(result.normalised_score, 3 / 4)


def test_evaluation_errorpath() -> None:
    input = "abc"
    eval = LengthEvaluator()
    conf = LengthEvaluatorConfig(expected_length=-1)
    result = eval.evaluate(input, conf)
    assert result.error is not None
