from app.core.models.length_evaluator import LengthEvaluator, LengthEvaluatorConfig


def test_binding() -> None:
    expected_length = 10
    eval = LengthEvaluator()
    conf = {"expected_length": 10}
    bound_conf = eval.bind(conf)
    assert bound_conf.expected_length == expected_length


def test_evaluation() -> None:
    input = "abc"
    eval = LengthEvaluator()
    conf = LengthEvaluatorConfig(expected_length=len(input))
    assert eval.evaluate(input, conf)
