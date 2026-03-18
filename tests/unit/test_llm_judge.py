from app.core.models import llm_judge
from app.core.models.evaluation_model import EvaluationResult
from app.core.models.llm_judge import LLMJudgeEvaluator, LLMJudgeConfig
from app.core.models.providers.base import CriterionResult, LLMResponse
import pytest

#todo: 10 test cases

@pytest.fixture
def mock_provider():
    class MockProvider(object):

        def generate_response(self, model_output: str, prompt: str, rubric: list[str]) -> LLMResponse:
            response: list[CriterionResult] = []
            for st in rubric:
                response.append(CriterionResult(criterion_name = st, score = 4, reasoning = "Very good") )

            return LLMResponse(results = response)

def test_evaluate(mock_provider):
    config: LLMJudgeConfig = LLMJudgeConfig(prompt = "How can I eat bananas most efficiently?", rubric=["correctness: is it correct?","politeness: is it polite?"])

    result = LLMJudgeEvaluator(mock_provider).evaluate("Peel the banana from the bottom tip, pull the peel down in strips, and eat it in a few large bites for the fastest and least messy consumption.", config,1)

    assert result == EvaluationResult()


# todo: maybe install pytest-mock

def test_evaluate1(mocker):
    # Create a mock API client
    mock_api_client = mocker.Mock()

    # Mock the response of the API client
    mock_response = mocker.Mock()

    # Assumes the LLM returns JSON
    mock_response.json.return_value = {
        [CriterionResult(criterion_name='correctness: is it correct?', score=4, reasoning='The method of peeling from the bottom tip to avoid stringy fibers and then eating in larger bites is a recognized, practical approach to eating bananas efficiently. The guidance is accurate and actionable, with no incorrect claims.'),
         CriterionResult(criterion_name='politeness: is it polite?', score=4, reasoning='The wording is neutral, non-judgmental, and concise, with no rude or condescending language. It provides steps in a courteous manner.')]}

    # Set the mock API client to return the mocked response
    mock_api_client.return_value = mock_response

    # Call the function with the mock API client
    result = llm_judge.evaluate(mock_api_client)

    # Assert result
    assert result == EvaluationResult(
        evaluator_id="llm_judge",
        reasoning= {[CriterionResult(criterion_name='correctness: is it correct?', score=4, reasoning='The method of peeling from the bottom tip to avoid stringy fibers and then eating in larger bites is a recognized, practical approach to eating bananas efficiently. The guidance is accurate and actionable, with no incorrect claims.'),
        CriterionResult(criterion_name='politeness: is it polite?', score=4, reasoning='The wording is neutral, non-judgmental, and concise, with no rude or condescending language. It provides steps in a courteous manner.')]},
        normalised_score = 0,
    )

    mock_api_client.get.assert_called_once()

"""
Todo: Possible test cases:

- Test construct of prompt
    - System prompt and user prompt merges correctly and values are filled in
    - 

- Test response from LLM
    - Valid format (structured data - not plaintext)
    - Non valid format (not json)
    - Wrong score - not between 1-4 - handled gracefully
    - Missing field / unexpected field / more criterion

- Test connection to API
    - Failed to connect
    - API throws error
    - Good connect

- Test normalize score
    - 1-4 input
    - invalid input

- SUPER IMPORDANTÉ!!!!!
    - Validate that the amount of criterion results in the LLM response
      is equal to the amount of criteria in the rubric!
    - AND THEY ARE THE SAME CRITERIA

"""