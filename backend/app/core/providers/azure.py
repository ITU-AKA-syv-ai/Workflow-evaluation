from openai.lib.azure import AsyncAzureOpenAI

from app.config.settings import Settings
from app.core.providers.base import (
    BaseProvider,
    Criterion,
    LLMExceptionError,
    LLMResponse,
)
from app.core.providers.provider_registry import register_provider

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
- Scores must be numeric values between 1 and 4
- Do not add extra criteria
- Do not omit any criterion
- Each criterion has a unique ID and a description
- You must use only the criteria ID as the identifier in your output
- Do not include the criteria descriptions in your output
- Do not modify, rephrase or add anything to the criteria IDs
- Do not include numbering (e.g. "1. clarity")
- The criterion_id field must match exactly one of the provided IDs
"""


@register_provider("azure")
class AzureOpenAIProvider(BaseProvider):
    """
    The LLM provider class for Azure OpenAI.
    """

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self.client = AsyncAzureOpenAI(
            api_version=settings.llm.api_version,
            azure_endpoint=settings.llm.api_endpoint,
            api_key=settings.llm.api_key.get_secret_value(),
        )

    async def check_health(self) -> None:
        """Raise an exception if the provider is unavailable."""
        await self.client.models.list()

    async def _generate_response(self, model_output: str, prompt: str, rubric: list[Criterion]) -> LLMResponse | None:
        """
        Constructs the prompt and call to the LLM judge, sends it, and receives a response. Also handles errors.

        Args:
            model_output (str): The output of the model
            prompt (str): The prompt of the AI that generated the result
            rubric (list[str]): The rubric (the criteria) we must evaluate
        Returns:
                LLMResponse: The response from the LLM judge, containing the rubric scores and reasoning for each.
        """

        try:
            response = await self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": _AZURE_SYSTEM_PROMPT,
                    },
                    {
                        "role": "user",
                        "content": self.build_user_prompt(model_output, prompt, rubric),
                    },
                ],
                text_format=LLMResponse,
            )
        except Exception as e:
            print(e)
            raise LLMExceptionError(e) from e

        return response.output_parsed
