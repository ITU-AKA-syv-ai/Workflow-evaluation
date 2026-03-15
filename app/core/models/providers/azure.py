import os

from openai.lib.azure import AzureOpenAI

from app.core.models.providers.base import BaseProvider, LLMResponse
from app.core.models.providers.provider_registry import register_provider


@register_provider("azure")
class AzureOpenAIProvider(BaseProvider):
    def __init__(self) -> None:
        self.client = AzureOpenAI(
            api_version=os.environ.get("AZURE_API_VERSION", "fixme"),
            azure_endpoint=os.environ.get("AZURE_ENDPOINT", "fixme"),
            api_key=os.environ.get("AZURE_OPENAI_API_KEY", "fixme"),
        )

    def generate_response(
        self, model: str, user_prompt: str, system_prompt: str
    ) -> LLMResponse:
        response = self.client.responses.parse(
            model="gpt-5-nano-ITU-students",
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

        raise ValueError("LLM failed to return a valid structured response.")
