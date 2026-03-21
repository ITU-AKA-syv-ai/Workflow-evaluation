import pytest

from app.core.providers.base import (
    BaseProvider,
    CriterionResult,
    LLMResponse,
    LLMValidationError,
)


class FakeProvider(BaseProvider):
    def __init__(self, fake_response: LLMResponse | None = None) -> None:
        self.model = "fake"
        self._fake_response = fake_response

    def _generate_response(
        self, model_output: str, prompt: str, rubric: list[str]
    ) -> LLMResponse | None:
        return self._fake_response


def test_empty_rubric_raises_error() -> None:
    provider = FakeProvider()

    with pytest.raises(LLMValidationError):
        provider.generate_response(model_output="hmm", prompt="hmm", rubric=[])


def test_none_response_raises_error() -> None:
    provider = FakeProvider(fake_response=None)
    with pytest.raises(LLMValidationError):
        provider.generate_response(model_output="hmm", prompt="hmm", rubric=["clarity"])


def test_generate_response_rejects_invalid_response() -> None:
    provider = FakeProvider(
        fake_response=LLMResponse(
            results=[CriterionResult(criterion_name="hmm", score=3, reasoning="hmm")]
        )
    )
    with pytest.raises(LLMValidationError):
        provider.generate_response("!!", "!!!", rubric=["clarity"])


def test_build_user_prompt_contains_all_inputs() -> None:
    prompt_text = BaseProvider.build_user_prompt(
        model_output="The answer is 42.",
        prompt="What is the meaning of life?",
        rubric=["accuracy", "depth"],
    )
    assert "What is the meaning of life?" in prompt_text
    assert "The answer is 42." in prompt_text
    assert "accuracy" in prompt_text
    assert "depth" in prompt_text


def test_validate_response_valid() -> None:
    rubric = ["clarity", "accuracy"]
    response = LLMResponse(
        results=[
            CriterionResult(criterion_name="clarity", score=3, reasoning="ok"),
            CriterionResult(criterion_name="accuracy", score=4, reasoning="good"),
        ]
    )

    # Sanity check. Our test should not raise if the response is valid.
    BaseProvider.validate_response(response, rubric)


def test_validate_response_wrong_count() -> None:
    rubric = ["clarity", "accuracy"]
    response = LLMResponse(
        results=[CriterionResult(criterion_name="clarity", score=3, reasoning="ok")]
    )
    with pytest.raises(LLMValidationError, match="Expected 2 criteria, got 1"):
        BaseProvider.validate_response(response, rubric)


def test_validate_response_mismatched_names() -> None:
    rubric = ["clarity", "accuracy"]
    response = LLMResponse(
        results=[
            CriterionResult(criterion_name="clarity", score=3, reasoning="ok"),
            CriterionResult(criterion_name="WRONG", score=4, reasoning="bad"),
        ]
    )
    with pytest.raises(LLMValidationError, match="Criteria mismatch"):
        BaseProvider.validate_response(response, rubric)
