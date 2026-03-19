import random
import string

from app.core.evaluators.cosine_evaluator import CosineEvaluator, CosineEvaluatorConfig


def test_bind_happy_path() -> None:
    standard = "test"
    evaluator = CosineEvaluator()
    conf = {"standard": standard}
    bound_conf = evaluator.validate_config(conf)
    assert bound_conf is not None
    assert bound_conf.standard == standard


def test_bind_error_path() -> None:
    standard = "test"
    evaluator = CosineEvaluator()
    conf = {"golden_standard": standard}
    bound_conf = evaluator.validate_config(conf)
    assert bound_conf is None


def test_bind_edge_case_empty_standard() -> None:
    standard = ""
    evaluator = CosineEvaluator()
    conf = {"standard": standard}
    bound_conf = evaluator.validate_config(conf)
    assert bound_conf is None


def test_bind_edge_case_to_long_standard() -> None:
    length = 2401
    standard = "".join(random.choices(string.ascii_letters, k=length))
    evaluator = CosineEvaluator()
    conf = {"standard": standard}
    bound_conf = evaluator.validate_config(conf)
    assert bound_conf is None


def test_evaluation_edge_case_empty_input() -> None:
    standard = "test"
    evaluator = CosineEvaluator()
    conf = CosineEvaluatorConfig(standard=standard)
    result = evaluator.evaluate("", conf)
    assert result.error is not None


def test_evaluation_edge_case_to_long_input() -> None:
    length = 2401
    standard = "test"
    evaluator = CosineEvaluator()
    conf = CosineEvaluatorConfig(standard=standard)
    output = "".join(random.choices(string.ascii_letters, k=length))
    result = evaluator.evaluate(output, conf)
    assert result.error is not None


def test_evaluation_same_standard_and_input() -> None:
    standard = "test"
    evaluator = CosineEvaluator()
    conf = CosineEvaluatorConfig(standard=standard)
    result = evaluator.evaluate("test", conf)
    assert result.passed
    assert result.normalised_score == 1


def test_evaluation_happy_path_within_threshold() -> None:
    standard = "glad"
    evaluator = CosineEvaluator()
    conf = CosineEvaluatorConfig(standard=standard)
    result = evaluator.evaluate("munter", conf)
    assert result.passed


def test_evaluation_happy_path_outside_threshold() -> None:
    standard = "test"
    evaluator = CosineEvaluator()
    conf = CosineEvaluatorConfig(standard=standard)
    result = evaluator.evaluate("kode", conf)
    assert not result.passed
