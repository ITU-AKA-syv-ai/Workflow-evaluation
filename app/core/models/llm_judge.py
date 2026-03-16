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
        try:
            bound = LLMJudgeConfig.model_validate(config)
        except ValidationError:
            return None

        return bound

    @property
    def default_threshold(self) -> float:
        return 1.0

    def _evaluate(self, output: str, config: LLMJudgeConfig) -> EvaluationResult:
        user_prompt = f"""

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
                # norm_score = (score-1) / 3
                # agg_norm_score = sum(norm_scores) / norm_scores.count
                # Where norm_score is the score of an individual criterion
                normalised_score = _normalise_and_aggregate(response),
            )
        except Exception as e:
            return EvaluationResult(
                evaluator_id="llm_judge",
                reasoning=str(e),
                error=str(e),
            )

def _normalise_and_aggregate(result: LLMResponse) -> float:
    normalised_scores = []
    for res in result.results:
        normalised = (res.score-1) / 3
        normalised_scores.append(normalised)

    agg_result = sum(normalised_scores) / len(normalised_scores)
    return agg_result