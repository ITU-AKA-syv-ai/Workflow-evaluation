import pytest

from app.core.evaluators.llm_judge import (
    LLMJudgeConfig,
    LLMJudgeEvaluator,
    _normalise_and_aggregate,
)
from app.core.providers.base import (
    CriterionResult,
    LLMResponse,
)
from tests.conftest import ErrorProvider, MockProvider


def test_normalise_all_max() -> None:
    response = LLMResponse(
        results=[
            CriterionResult(criterion_name="idk", score=4, reasoning="ok")
            for i in range(3)
        ]
    )
    assert _normalise_and_aggregate(response) == pytest.approx(1.0)


def test_normalise_all_min() -> None:
    response = LLMResponse(
        results=[
            CriterionResult(criterion_name=f"c{i}", score=1, reasoning="bad")
            for i in range(3)
        ]
    )
    assert _normalise_and_aggregate(response) == pytest.approx(0.0)


def test_normalise_mixed() -> None:
    response = LLMResponse(
        results=[
            CriterionResult(criterion_name="a", score=1, reasoning="bad"),
            CriterionResult(criterion_name="b", score=4, reasoning="good"),
        ]
    )

    assert _normalise_and_aggregate(response) == pytest.approx(0.5)


def test_normalise_single_criterion() -> None:
    response = LLMResponse(
        results=[CriterionResult(criterion_name="only", score=3, reasoning="ok")]
    )
    assert _normalise_and_aggregate(response) == pytest.approx(2 / 3)


def test_bind_valid_config() -> None:
    evaluator = LLMJudgeEvaluator(MockProvider())
    cfg = evaluator.validate_config({
        "prompt": "What is 2+2?",
        "rubric": ["correctness"],
    })
    assert isinstance(cfg, LLMJudgeConfig)
    assert cfg.prompt == "What is 2+2?"
    assert cfg.rubric == ["correctness"]


def test_bind_missing_prompt() -> None:
    assert (
        LLMJudgeEvaluator(MockProvider()).validate_config({"rubric": ["correctness"]})
        is None
    )


def test_bind_missing_rubric() -> None:
    assert (
        LLMJudgeEvaluator(MockProvider()).validate_config({"prompt": "hello"}) is None
    )


def test_evaluate_single_criterion(mock_provider: MockProvider) -> None:
    evaluator = LLMJudgeEvaluator(mock_provider)
    config = LLMJudgeConfig(prompt="test", rubric=["clarity"])
    result = evaluator._evaluate("some output", config)

    assert result.evaluator_id == "llm_judge"
    assert isinstance(result.reasoning, LLMResponse)
    assert result.normalised_score == pytest.approx(2 / 3)


def test_evaluate_multi_criterion_average() -> None:
    provider = MockProvider(
        response=LLMResponse(
            results=[
                CriterionResult(criterion_name="a", score=1, reasoning="bad"),
                CriterionResult(criterion_name="b", score=4, reasoning="great"),
            ]
        )
    )
    evaluator = LLMJudgeEvaluator(provider)
    config = LLMJudgeConfig(prompt="test", rubric=["a", "b"])
    result = evaluator._evaluate("output", config)

    assert result.normalised_score == pytest.approx(0.5)


def test_evaluate_threshold_pass(mock_provider: MockProvider) -> None:
    evaluator = LLMJudgeEvaluator(mock_provider)
    config = LLMJudgeConfig(prompt="test", rubric=["clarity"])
    result = evaluator.evaluate("some output", config, threshold=0.5)

    assert result.passed is True
    assert result.normalised_score == pytest.approx(2 / 3)


def test_evaluate_threshold_fail(mock_provider: MockProvider) -> None:
    evaluator = LLMJudgeEvaluator(mock_provider)
    config = LLMJudgeConfig(prompt="test", rubric=["clarity"])
    result = evaluator.evaluate("some output", config, threshold=0.9)

    assert result.passed is False
    assert result.normalised_score == pytest.approx(2 / 3)


# Idea here to ensure that errors are not propogated but caught and put into the result
# This might change when we actually get proper APIErrors
def test_evaluate_error_is_caught_and_not_propogated() -> None:
    provider = ErrorProvider(ValueError(":)"))
    evaluator = LLMJudgeEvaluator(provider)
    config = LLMJudgeConfig(prompt="test", rubric=["clarity"])
    result = evaluator.evaluate("some output", config)

    assert result.error is not None


# @pytest.fixture
# def mock_provider():
#    class MockProvider(object):
#        def generate_response(
#            self, model_output: str, prompt: str, rubric: list[str]
#        ) -> LLMResponse:
#            response: list[CriterionResult] = []
#            for st in rubric:
#                response.append(
#                    CriterionResult(criterion_name=st, score=4, reasoning="Very good")
#                )
#
#            return LLMResponse(results=response)
#

# def test_evaluate(mock_provider):
#     config: LLMJudgeConfig = LLMJudgeConfig(
#         prompt="How can I eat bananas most efficiently?",
#         rubric=["correctness: is it correct?", "politeness: is it polite?"],
#     )
#
#     result = LLMJudgeEvaluator(mock_provider).evaluate(
#         "Peel the banana from the bottom tip, pull the peel down in strips, and eat it in a few large bites for the fastest and least messy consumption.",
#         config,
#         1,
#     )
#
#     assert result == EvaluationResult()
#
#
# def test_evaluate1(mocker):
#     # Create a mock API client
#     mock_api_client = mocker.Mock()
#
#     # Mock the response of the API client
#     mock_response = mocker.Mock()
#
#     # Assumes the LLM returns JSON
#     mock_response.json.return_value = {
#         [
#             CriterionResult(
#                 criterion_name="correctness: is it correct?",
#                 score=4,
#                 reasoning="The method of peeling from the bottom tip to avoid stringy fibers and then eating in larger bites is a recognized, practical approach to eating bananas efficiently. The guidance is accurate and actionable, with no incorrect claims.",
#             ),
#             CriterionResult(
#                 criterion_name="politeness: is it polite?",
#                 score=4,
#                 reasoning="The wording is neutral, non-judgmental, and concise, with no rude or condescending language. It provides steps in a courteous manner.",
#             ),
#         ]
#     }
#
#     # Set the mock API client to return the mocked response
#     mock_api_client.return_value = mock_response
#
#     # Call the function with the mock API client
#     result = llm_judge.evaluate(mock_api_client)
#
#     # Assert result
#     assert result == EvaluationResult(
#         evaluator_id="llm_judge",
#         reasoning={
#             [
#                 CriterionResult(
#                     criterion_name="correctness: is it correct?",
#                     score=4,
#                     reasoning="The method of peeling from the bottom tip to avoid stringy fibers and then eating in larger bites is a recognized, practical approach to eating bananas efficiently. The guidance is accurate and actionable, with no incorrect claims.",
#                 ),
#                 CriterionResult(
#                     criterion_name="politeness: is it polite?",
#                     score=4,
#                     reasoning="The wording is neutral, non-judgmental, and concise, with no rude or condescending language. It provides steps in a courteous manner.",
#                 ),
#             ]
#         },
#         normalised_score=0,
#     )
#
#     mock_api_client.get.assert_called_once()
