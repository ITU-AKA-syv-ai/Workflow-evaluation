from app.core.models.substring_evaluator import SubstringEvaluator, SubstringEvaluatorConfig

# def test_bind() -> None:
    # conf = {"substring": "test"}
    # bound_conf = SubstringEvaluator().bind(conf)
    # assert bound_conf is not None
    # assert bound_conf.substring == "test"

def test_evaluation_happypath() -> None:
    input = "abc"
    eval = SubstringEvaluator()
    conf = SubstringEvaluatorConfig(substring="bc")
    assert eval.evaluate(input, conf)

