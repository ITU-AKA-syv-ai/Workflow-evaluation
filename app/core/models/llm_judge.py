from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.models.base import BaseEvaluator
from app.core.models.providers.provider_registry import (
    get_available_providers,
    get_provider,
)


class LLMJudgeConfig(BaseModel):
    provider: str
    model: str = "Hello"

    prompt: str
    rubric: list[str]


class LLMJudgeEvaluator(BaseEvaluator):
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

        if bound.provider not in get_available_providers():
            return None

        return bound

    def evaluate(self, output: str, config: LLMJudgeConfig) -> bool:
        provider = get_provider(
            config.provider
        )()  # This can return an error if the provider doesnt exist, shouldnt happen because of validation in config
        system_prompt = """
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
        - for each criterion provide your reasoning for why it suceeds/fails, then assign the score on the given scale from 1 - 4

        Important requirements:
        - You must provide exactly one Reasoning per criterion in the rubric
        - You must provide one score for every criterion in the rubric
        - Do not add extra criteria
        - Do not omit any criterion
        - Scores must be numeric values between 1 and 4
        - Use the exact text of the criterion as the key in your output dictionary
        """

        user_prompt = f"""

        Now here are the inputs.

        USER QUESTION: {config.prompt}
        SYSTEM ANSWER: {output}
        CRITERIA:
            {"\n\t".join([f"\t{i + 1}. {crit}" for i, crit in enumerate(config.rubric)])}

        Provide your evaluation.

        """
        response = provider.generate_response(config.model, system_prompt, user_prompt)

        print(response)
        return True
