# Tests for the testing utils

import pytest
from pydantic import BaseModel

from app.core.models.evaluation_model import EvaluationResult
from tests.conftest import MockEvaluator


@pytest.mark.asyncio
async def test_mockevaluator_simple() -> None:
    class ExampleEvaluationConfig(BaseModel):
        field: int = 10

    evaluator = MockEvaluator(
        evaluation=EvaluationResult(evaluator_id="abc", reasoning="This is a mock"),
        config_type=ExampleEvaluationConfig)

    config = evaluator.validate_config({})
    assert config.field == 10
    result = await evaluator.evaluate("Just testing...", config)

    assert type(config) is ExampleEvaluationConfig
    assert config.field == 10

    assert result.reasoning == "This is a mock"
