from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.models.base import BaseEvaluator
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResult,
    EvaluatorConfig,
)
from app.core.models.registry import registry
from app.core.services.evaluation_service import (
    evaluate,
    get_evaluators,
)


def test_get_evaluators() -> None:
    evaluators = get_evaluators()
    for eval in evaluators:
        reg_eval = registry.get(eval.evaluator_id)
        assert reg_eval is not None
        assert reg_eval.description == eval.description
        assert reg_eval.config_schema == eval.config_schema


class ContainsSubStringConfig(BaseModel):
    expected_substr: str


# Simple mock evaluator used for testing
class ContainsSubStringEvaluator(BaseEvaluator):
    @property
    def name(self) -> str:
        return "contains_substring_evaluator"

    @property
    def description(self) -> str:
        return "Determines if string contains substring"

    @property
    def config_schema(self) -> dict[str, Any]:
        return ContainsSubStringConfig.model_json_schema()

    def bind(self, config: dict[str, Any]) -> ContainsSubStringConfig | None:
        try:
            return ContainsSubStringConfig.model_validate(config)
        except ValidationError:
            return None

    @property
    def default_threshold(self) -> float:
        return 1

    def _evaluate(
        self, output: str, config: ContainsSubStringConfig
    ) -> EvaluationResult:
        passed = config.expected_substr in output
        return EvaluationResult(
            evaluator_id=self.name,
            passed=passed,
            reasoning="Found substring" if passed else "Could not find substring",
            normalised_score=1 if passed else 0,
            execution_time=0,
        )


def mock_runner(model_output: str, expected_substr: str) -> None:
    eval_id = "contains_substring_evaluator"
    registry.register(eval_id, ContainsSubStringEvaluator())

    eval_config = EvaluatorConfig(
        evaluator_id=eval_id,
        threshold=0.5,
        weight=1,
        config={"expected_substr": expected_substr},
    )
    eval_req = EvaluationRequest(model_output=model_output, configs=[eval_config])

    resps = evaluate(eval_req)
    assert len(resps.results) == 1

    resp = resps.results[0]
    assert resp.passed == (expected_substr in model_output)
    assert resp.evaluator_id == eval_id
    assert resp.error is None


def test_evaluate_pass_1() -> None:
    mock_runner("Lorem Ipsum", "Ipsum")


def test_evaluate_fail_1() -> None:
    mock_runner("Lorem Ipsum", "Fails")


def test_evaluate_fail_2() -> None:
    mock_runner("Other string", "Ipsum")
