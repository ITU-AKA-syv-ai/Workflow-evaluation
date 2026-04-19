# Tests for the testing utils

from math import isclose

import pytest
from pydantic import BaseModel

from tests.conftest import DEFAULT_CONFIG, MockEvaluator, create_evaluation_config, create_evaluation_request


@pytest.mark.asyncio
async def test_mockevaluator_config_and_evaluation() -> None:
    field_value = 10
    normalised_score = 0.5

    class ExampleEvaluationConfig(BaseModel):
        field: int

    evaluator = MockEvaluator(score=normalised_score, config=ExampleEvaluationConfig(field=field_value))

    config = evaluator.validate_config({"field": field_value})
    assert config is not None
    result = await evaluator.evaluate("Just testing...", config)

    assert type(config) is ExampleEvaluationConfig
    assert config.field == field_value
    assert isclose(result.normalised_score, normalised_score)


@pytest.mark.asyncio
async def test_mockevaluator_exception() -> None:
    evaluator = MockEvaluator(raise_on_evaluate=Exception("This is just a test"))
    result = await evaluator.evaluate("Just testing...", DEFAULT_CONFIG)

    assert result.error is not None
    assert "This is just a test" in result.error


@pytest.mark.asyncio
async def test_mockevaluator_threshold_pass() -> None:
    evaluator = MockEvaluator(threshold=0.2, score=1)
    result = await evaluator.evaluate("Just testing...", DEFAULT_CONFIG)
    assert result.passed


@pytest.mark.asyncio
async def test_mockevaluator_threshold_fail() -> None:
    evaluator = MockEvaluator(threshold=0.2, score=0.1)
    result = await evaluator.evaluate("Just testing...", DEFAULT_CONFIG)
    assert not result.passed


def test_create_evaluation_config() -> None:
    cfg = create_evaluation_config("abc", weight=0.5)
    assert cfg.evaluator_id == "abc"
    assert isclose(cfg.weight, 0.5)


def test_create_evaluation_request() -> None:
    req = create_evaluation_request([
        create_evaluation_config("mock", weight=0.5),
        create_evaluation_config("test", weight=2.0),
    ])

    assert len(req.configs) == 2
    assert req.configs[0].evaluator_id == "mock"
    assert isclose(req.configs[0].weight, 0.5)

    assert req.configs[1].evaluator_id == "test"
    assert isclose(req.configs[1].weight, 2.0)
