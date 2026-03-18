import os
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.models.base import BaseEvaluator
from app.core.models.evaluation_model import EvaluationResult
from app.core.models.providers.base import BaseProvider, LLMResponse

_SYSTEM_PROMPT = """
You are an impartial, expert judge evaluating AI-generated text.
You will be given a user_question, a system_answer and a list of user_criteria.

For each criterion, write out your detailed reasoning FIRST, explaining exactly why the text succeeds or fails.
After writing your reasoning, assign a score on a scale of 1 to 4. Here is the scale:
1: The system_answer is terrible: completely irrelevant to the criterion specified, or very partial
2: The system_answer is mostly not helpful: misses some key aspects of the criterion
3: The system_answer is mostly helpful: fulfills the criterion, but still could be improved
4: The system_answer is excellent: relevant, direct, detailed, and addresses all the concerns raised in the criterion

You should:
- carefully read the question and answer
- evaluate the answer ONLY based on the provided criterion
- for each criterion provide your reasoning for why it succeeds/fails, then assign the score on the given scale from 1 - 4

Important requirements:
- You must provide exactly one Reasoning per criterion in the rubric
- You must provide one score for every criterion in the rubric
- Do not add extra criteria
- Do not omit any criterion
- Scores must be numeric values between 1 and 4
- Use the exact text of the criterion as the key in your output dictionary
"""


class LLMJudgeConfig(BaseModel):
    prompt: str
    rubric: list[str]


class LLMJudgeEvaluator(BaseEvaluator):
    def __init__(self, provider: BaseProvider):
        self.provider = provider
        #TODO: figure out where to actually discover providers
#        discover_providers()

#        if provider == "mock":
#            pass
#        elif provider not in get_available_providers():
#            raise ProviderNotSupportedException("The given provider is not supported")

#        # Todo: error handling
#        self.provider = get_provider(provider)(model)

    @property
    def name(self) -> str:
        return "llm_judge"

    @property
    def description(self) -> str:
        return "Cool guy"

    @property
    def config_schema(self) -> dict[str, Any]:
        return LLMJudgeConfig.model_json_schema()

    def bind(self, config: dict[str, Any]) -> LLMJudgeConfig | None:
        """
        Converts a configuration consisting of ... to an instance of LLMJudgeConfig with ...

        Args:
            config (dict[str, Any]): The config to bind to a LLMJudgeConfig.

        Returns:
            LLMJudgeConfig | None: Returns LLMJudgeConfig if config is correctly formatted, otherwise None is returned.
        """

        try:
            bound = LLMJudgeConfig.model_validate(config)
        except ValidationError:
            return None

        return bound

    @property
    def default_threshold(self) -> float:
        return 1.0

    def _evaluate(self, output: str, config: LLMJudgeConfig) -> EvaluationResult:
        """
        Uses an LLM to judge the output of another LLM based on user defined criteria in a rubric, by constructing a prompt based on aforementioned.

        Args:
        	output (str): The AI output to be evaluated.
            config (LengthEvaluatorConfig): The config which specifies the criteria the judge should use, collectively called the rubric, as well as the original user prompt.

        Returns:
        	EvaluationResult: Result which contains the evaluator_id, normalised score, and a reasoning. The reasoning field contains the scores and reasoning of each individual criterion in the rubric.
        """

        user_prompt = """

        Now here are the inputs.

        USER QUESTION: {config.prompt}
        SYSTEM ANSWER: {output}
        CRITERIA:
            {"\n\t".join([f"\t{i + 1}. {crit}" for i, crit in enumerate(config.rubric)])}

        Provide your evaluation.

        """
        try:
            response = self.provider.generate_response(_SYSTEM_PROMPT, user_prompt)
            return EvaluationResult(
                evaluator_id="llm_judge",
                reasoning=response,
                normalised_score = _normalise_and_aggregate(response),
            )
        except Exception as e:
            return EvaluationResult(
                evaluator_id="llm_judge",
                reasoning=str(e),
                error=str(e),
            )

def _normalise_and_aggregate(response: LLMResponse) -> float:
    """
    Normalises and aggregates the scors of each criterion in the rubric. The scale is converted from 1-4 to 0-1.

    Args:
    	response: (LLMResponse): The response from the LLM judge, containing the rubric scores.

    Returns:
    	float: The normalised and aggregated score for each criterion in the rubric.
    """
    normalised_scores = []
    for res in response.results:
        normalised = (res.score-1) / 3
        normalised_scores.append(normalised)

    agg_result = sum(normalised_scores) / len(normalised_scores)
    return agg_result