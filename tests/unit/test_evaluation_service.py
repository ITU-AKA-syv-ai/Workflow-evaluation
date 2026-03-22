from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from app.core.evaluators.base import BaseEvaluator
from app.core.evaluators.length_evaluator import LengthEvaluator
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.evaluators.substring_evaluator import SubstringEvaluator
from app.core.models.evaluation_model import EvaluationRequest, EvaluationResult, EvaluatorConfig
from app.core.models.registry import EvaluationRegistry
from app.core.services.evaluation_service import get_evaluators


def test_get_evaluators() -> None:
    registry = EvaluationRegistry()
    registry.register(LengthEvaluator().name, LengthEvaluator())
    registry.register(SubstringEvaluator().name, SubstringEvaluator())

    evaluators = get_evaluators(registry)

    for e in evaluators:
        reg_eval = registry.get(e.evaluator_id)
        assert reg_eval is not None
        assert reg_eval.description == e.description
        assert reg_eval.config_schema == e.config_schema


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

    def validate_config(self, config: dict[str, Any]) -> ContainsSubStringConfig | None:
        try:
            return ContainsSubStringConfig.model_validate(config)
        except ValidationError:
            return None

    @property
    def default_threshold(self) -> float:
        return 1

    async def _evaluate(self, output: str, config: ContainsSubStringConfig) -> EvaluationResult:
        passed = config.expected_substr in output
        return EvaluationResult(
            evaluator_id=self.name,
            passed=passed,
            reasoning="Found substring" if passed else "Could not find substring",
            normalised_score=1 if passed else 0,
            execution_time=0,
        )


async def mock_runner(model_output: str, expected_substr: str) -> None:
    eval_id = "contains_substring_evaluator"
    test_registry = EvaluationRegistry()
    test_registry.register(eval_id, ContainsSubStringEvaluator())
    orchestrator = EvaluationOrchestrator(registry=test_registry)

    eval_config = EvaluatorConfig(
        evaluator_id=eval_id,
        threshold=0.5,
        weight=1,
        config={"expected_substr": expected_substr},
    )
    eval_req = EvaluationRequest(model_output=model_output, configs=[eval_config])

    resp = await orchestrator.evaluate(eval_req)
    result = resp.results[0]
    assert result.passed == (expected_substr in model_output)
    assert result.evaluator_id == eval_id
    assert result.error is None


@pytest.mark.asyncio
async def test_evaluate_pass_1() -> None:
    await mock_runner("Lorem Ipsum", "Ipsum")


@pytest.mark.asyncio
async def test_evaluate_fail_1() -> None:
    await mock_runner("Lorem Ipsum", "Fails")


@pytest.mark.asyncio
async def test_evaluate_fail_2() -> None:
    await mock_runner("Other string", "Ipsum")
