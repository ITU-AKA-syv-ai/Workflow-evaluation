
from openai.lib.azure import AzureOpenAI

from app.config.settings import Settings
from app.core.models.llm_judge import LLMJudgeConfig
from app.core.models.providers.base import BaseProvider, LLMResponse, LLMException
from app.core.models.providers.provider_registry import register_provider

_AZURE_SYSTEM_PROMPT = """
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

@register_provider("azure")
class AzureOpenAIProvider(BaseProvider):
    """
    The LLM provider class for Azure OpenAI.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self.client = AzureOpenAI(
            api_version=settings.llm.api_version,
            azure_endpoint=settings.llm.api_endpoint,
            api_key=settings.llm.api_key.get_secret_value(),
        )

    def generate_response(self, model_output: str, prompt: str, rubric: list[str]) -> LLMResponse:
        """
        Constructs the prompt and call to the LLM judge, sends it, and receives a response. Also handles errors.

        Args:
            model_output (str): The output of the model
            prompt (str): The prompt of the ai that generated the result
            rubric (list[str]): The rubric (the criteria) we must evaluate
        Returns:
        	LLMResponse: The response from the LLM judge, containing the rubric scores and reasoning for each.
        """

        user_prompt = f"""

        Now here are the inputs.

        USER QUESTION: {prompt}
        SYSTEM ANSWER: {model_output}
        CRITERIA:
            {"\n\t".join([f"\t{i + 1}. {crit}" for i, crit in enumerate(rubric)])}

        Provide your evaluation.

        """

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": _AZURE_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                text_format=LLMResponse,
            )

            if response and response.output_parsed:
                return response.output_parsed

        except Exception as e:
            raise LLMException(e) from e