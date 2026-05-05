from unittest import mock

import pytest
from openai import RateLimitError

from app.core.evaluators.llm_judge import (
    LLMJudgeConfig,
    LLMJudgeEvaluator,
    _normalise_and_aggregate,
)
from app.core.providers.base import (
    Criterion,
    CriterionResult,
    LLMResponse,
)
from tests.conftest import ErrorProvider, MockProvider


def test_normalise_all_max() -> None:
    response = LLMResponse(results=[CriterionResult(criterion_id="idk", score=4, reasoning="ok") for i in range(3)])
    assert _normalise_and_aggregate(response) == pytest.approx(1.0)


def test_normalise_all_min() -> None:
    response = LLMResponse(results=[CriterionResult(criterion_id=f"c{i}", score=1, reasoning="bad") for i in range(3)])
    assert _normalise_and_aggregate(response) == pytest.approx(0.0)


def test_normalise_mixed() -> None:
    response = LLMResponse(
        results=[
            CriterionResult(criterion_id="a", score=1, reasoning="bad"),
            CriterionResult(criterion_id="b", score=4, reasoning="good"),
        ]
    )

    assert _normalise_and_aggregate(response) == pytest.approx(0.5)


def test_normalise_single_criterion() -> None:
    response = LLMResponse(results=[CriterionResult(criterion_id="only", score=3, reasoning="ok")])
    assert _normalise_and_aggregate(response) == pytest.approx(2 / 3)


def test_bind_valid_config() -> None:
    evaluator = LLMJudgeEvaluator(MockProvider(), threshold=1.0, timeout=30)
    cfg = evaluator.validate_config({
        "prompt": "What is 2+2?",
        "rubric": [{"id": "correctness", "description": "Is the advice scientifically valid?"}],
    })
    assert isinstance(cfg, LLMJudgeConfig)
    assert cfg.prompt == "What is 2+2?"
    assert cfg.rubric[0].id == "correctness"
    assert cfg.rubric[0].description == "Is the advice scientifically valid?"


def test_bind_missing_prompt() -> None:
    assert (
        LLMJudgeEvaluator(MockProvider(), threshold=1.0, timeout=30).validate_config({
            "rubric": [{"id": "correctness", "description": "Is the advice scientifically valid?"}]
        })
        is None
    )


def test_bind_missing_rubric() -> None:
    assert LLMJudgeEvaluator(MockProvider(), threshold=1.0, timeout=30).validate_config({"prompt": "hello"}) is None


def test_bind_empty_rubric() -> None:
    assert (
        LLMJudgeEvaluator(MockProvider(), threshold=1.0, timeout=30).validate_config({
            "prompt": "hello",
            "rubric": [],
        })
        is None
    )


@pytest.mark.asyncio
async def test_evaluate_single_criterion(mock_provider: MockProvider) -> None:
    evaluator = LLMJudgeEvaluator(mock_provider, threshold=1.0, timeout=30)
    config = LLMJudgeConfig(
        prompt="test", rubric=[Criterion(id="clarity", description="Is the explanation easy to follow?")]
    )
    
    result = await evaluator._evaluate("some output", config)

    assert result.evaluator_id == "llm_judge"
    assert isinstance(result.reasoning, LLMResponse)
    assert result.normalised_score == pytest.approx(2 / 3)


@pytest.mark.asyncio
async def test_evaluate_multi_criterion_average() -> None:
    provider = MockProvider(
        response=LLMResponse(
            results=[
                CriterionResult(criterion_id="a", score=1, reasoning="bad"),
                CriterionResult(criterion_id="b", score=4, reasoning="great"),
            ]
        )
    )
    evaluator = LLMJudgeEvaluator(provider, threshold=1.0, timeout=30)
    config = LLMJudgeConfig(
        prompt="test",
        rubric=[
            Criterion(id="a", description="b"),
            Criterion(id="c", description="d"),
        ],
    )
    
    result = await evaluator._evaluate("output", config)

    assert result.normalised_score == pytest.approx(0.5)


@pytest.mark.asyncio
async def test_evaluate_threshold_pass(mock_provider: MockProvider) -> None:
    evaluator = LLMJudgeEvaluator(mock_provider, threshold=1.0, timeout=30)
    config = LLMJudgeConfig(
        prompt="test", rubric=[Criterion(id="clarity", description="Is the explanation easy to follow?")]
    )
    
    result = await evaluator.evaluate("some output", config, threshold=0.5)

    assert result.passed is True
    assert result.normalised_score == pytest.approx(2 / 3)


@pytest.mark.asyncio
async def test_evaluate_threshold_fail(mock_provider: MockProvider) -> None:
    evaluator = LLMJudgeEvaluator(mock_provider, threshold=1.0, timeout=30)
    config = LLMJudgeConfig(
        prompt="test", rubric=[Criterion(id="clarity", description="Is the explanation easy to follow?")]
    )

    result = await evaluator.evaluate("some output", config, threshold=0.9)

    assert result.passed is False
    assert result.normalised_score == pytest.approx(2 / 3)


# Idea here to ensure that errors are not propogated but caught and put into the result
# This might change when we actually get proper APIErrors
async def test_evaluate_error_is_caught_and_not_propogated() -> None:
    provider = ErrorProvider(ValueError(":)"))
    evaluator = LLMJudgeEvaluator(provider, threshold=1.0, timeout=30)
    config = LLMJudgeConfig(
        prompt="test", rubric=[Criterion(id="clarity", description="Is the explanation easy to follow?")]
    )

    result = await evaluator.evaluate("some output", config)

    assert result.error is not None


@pytest.mark.asyncio
async def test_generate_response_raises_llm_exception() -> None:
    provider = ErrorProvider(mock.Mock(spec=RateLimitError))

    evaluator = LLMJudgeEvaluator(provider, threshold=1.0, timeout=30)
    config = LLMJudgeConfig(
        prompt="test", rubric=[Criterion(id="clarity", description="Is the explanation easy to follow?")]
    )

    result = await evaluator.evaluate("some output", config)

    assert result.passed is False
    assert result.error == "Your request was rate limited. Please wait a moment and try again."
