from typing import Protocol

from openai import AzureOpenAI

from app.config.settings import Settings


class EmbeddingClient(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class AzureEmbeddingClient:
    def __init__(self, settings: Settings) -> None:
        self._client = AzureOpenAI(
            api_key=settings.llm.api_key.get_secret_value(),
            api_version=settings.llm.api_version,
            azure_endpoint=settings.llm.api_endpoint,
        )
        self._model = "text-embedding-3-large"

    async def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(
            input=texts,
            model=self._model,
            encoding_format="float",
        )
        return [item.embedding for item in response.data]
