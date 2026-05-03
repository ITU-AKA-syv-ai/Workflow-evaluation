from unittest import mock

import pytest
from openai import UnprocessableEntityError

from app.core.providers.base import (
    BaseProvider,
    Criterion,
    CriterionResult,
    LLMExceptionError,
    LLMResponse,
    LLMValidationError,
)


class FakeProvider(BaseProvider):
    def __init__(self, fake_response: LLMResponse | None = None) -> None:
        self.model = "fake"
        self._fake_response = fake_response

    async def check_health(self) -> None:
        """
        Mock health check for the provider.

        Returns:
            None: Always succeeds for tests that focus on response validation.
        """
        return

    async def _generate_response(self, model_output: str, prompt: str, rubric: list[Criterion]) -> LLMResponse | None:
        return self._fake_response


@pytest.mark.asyncio
async def test_empty_rubric_raises_error() -> None:
    provider = FakeProvider()

    with pytest.raises(LLMValidationError):
        await provider.generate_response(model_output="hmm", prompt="hmm", rubric=[])


@pytest.mark.asyncio
async def test_none_response_raises_error() -> None:
    provider = FakeProvider(fake_response=None)
    with pytest.raises(LLMValidationError):
        await provider.generate_response(model_output="hmm", prompt="hmm", rubric=[Criterion(id="clarity", description="...")])


@pytest.mark.asyncio
async def test_generate_response_rejects_invalid_response() -> None:
    provider = FakeProvider(
        fake_response=LLMResponse(results=[CriterionResult(criterion_id="hmm", score=3, reasoning="hmm")])
    )
    with pytest.raises(LLMValidationError):
        await provider.generate_response("!!", "!!!", rubric=[Criterion(id="clarity", description="...")])


def test_build_user_prompt_contains_all_inputs() -> None:
    prompt_text = BaseProvider.build_user_prompt(
        model_output="The answer is 42.",
        prompt="What is the meaning of life?",
        rubric=[
            Criterion(id="accuracy", description="..."),
            Criterion(id="depth", description="..."),
        ],
    )
    assert "What is the meaning of life?" in prompt_text
    assert "The answer is 42." in prompt_text
    assert "accuracy" in prompt_text
    assert "depth" in prompt_text


def test_validate_response_valid() -> None:
    rubric = [
        Criterion(id="clarity", description="..."),
        Criterion(id="accuracy", description="..."),
    ]
    response = LLMResponse(
        results=[
            CriterionResult(criterion_id="clarity", score=3, reasoning="ok"),
            CriterionResult(criterion_id="accuracy", score=4, reasoning="good"),
        ]
    )

    # Sanity check. Our test should not raise if the response is valid.
    BaseProvider.validate_response(response, rubric)


def test_validate_response_wrong_count() -> None:
    rubric = [
        Criterion(id="clarity", description="..."),
        Criterion(id="accuracy", description="..."),
    ]
    response = LLMResponse(results=[CriterionResult(criterion_id="clarity", score=3, reasoning="ok")])
    with pytest.raises(LLMValidationError, match="Expected 2 criteria, got 1"):
        BaseProvider.validate_response(response, rubric)


def test_validate_response_mismatched_names() -> None:
    rubric = [
        Criterion(id="clarity", description="..."),
        Criterion(id="accuracy", description="..."),
    ]
    response = LLMResponse(
        results=[
            CriterionResult(criterion_id="clarity", score=3, reasoning="ok"),
            CriterionResult(criterion_id="WRONG", score=4, reasoning="bad"),
        ]
    )
    with pytest.raises(LLMValidationError, match="Criteria mismatch"):
        BaseProvider.validate_response(response, rubric)


@pytest.mark.parametrize(
    "exception,expected_message",
    [
        (
            mock.Mock(spec=UnprocessableEntityError),
            "The LLM couldn't understand the request. Could you try asking in a different way?",
        ),
        (Exception(), "Something unexpected happened. Please try again."),
    ],
)
def test_exception_mapping_returns_expected_message(exception: Exception, expected_message: str) -> None:
    result = LLMExceptionError(exception)

    assert result.message == expected_message
