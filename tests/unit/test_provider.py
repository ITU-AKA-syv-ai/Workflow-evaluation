import pytest

from app.core.models.providers.base import (
    BaseProvider,
    CriterionResult,
    LLMResponse,
    LLMValidationError,
)


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
