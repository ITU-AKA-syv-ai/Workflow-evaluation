
from openai.lib.azure import AzureOpenAI

from app.config.settings import Settings
from app.core.models.providers.base import BaseProvider, LLMResponse, LLMException
from app.core.models.providers.provider_registry import register_provider


@register_provider("azure")
class AzureOpenAIProvider(BaseProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self.client = AzureOpenAI(
            api_version=settings.llm.api_version,
            azure_endpoint=settings.llm.api_endpoint,
            api_key=settings.llm.api_key.get_secret_value(),
        )

    def generate_response(self, user_prompt: str, system_prompt: str) -> LLMResponse:
        """
        Constructs the call to the LLM judge, sends it, and receives a response. Also handles errors.

        Args:
            user_prompt (str): The original prompt that the user gave to an LLM.
        	system_prompt (str): The prompt constructed for the LLM-judge, asking it to evaluate.

        Returns:
        	LLMResponse: The response from the LLM judge, containing the rubric scores and reasoning for each.
        """

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
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
