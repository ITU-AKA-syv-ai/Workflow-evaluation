import pytest
from pydantic import BaseModel

from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.registry import EvaluationRegistry
from app.core.services.evaluation_service import get_evaluators
from tests.conftest import MockEvaluator, create_evaluation_config, create_evaluation_request


def test_get_evaluators() -> None:
    registry = EvaluationRegistry()
    evaluator = MockEvaluator()
    registry.register(evaluator.name, evaluator)

    evaluators = get_evaluators(registry)

    for e in evaluators:
        reg_eval = registry.get(e.evaluator_id)
        assert reg_eval is not None
        assert reg_eval.description == e.description
        assert reg_eval.config_schema == e.config_schema


async def mock_runner(model_output: str, expected_substr: str) -> None:
    score = 1 if expected_substr in model_output else 0
    evaluator = MockEvaluator(name="contains_substring_evaluator", score=score)
    test_registry = EvaluationRegistry()
    test_registry.register(evaluator.name, evaluator)
    orchestrator = EvaluationOrchestrator(registry=test_registry)

    class ExpectedSubstringConfig(BaseModel):
        expected_substr: str

    req = create_evaluation_request([create_evaluation_config(evaluator.name, {"expected_substr": expected_substr})])

    resp = await orchestrator.evaluate(req)
    result = resp.results[0]
    assert result.passed == (expected_substr in model_output)
    assert result.evaluator_id == evaluator.name
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
