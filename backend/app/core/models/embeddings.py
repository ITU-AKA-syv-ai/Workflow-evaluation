from abc import ABC, abstractmethod

from openai import AsyncAzureOpenAI

from backend.app.config.settings import Settings


class EmbeddingClient(ABC):
    """
    Abstract class for an embedding client
    """

    max_length: int

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generates an embedding from a list of texts

        Args:
            texts: list of texts

        Returns:
            list[list[float]]: embedding of texts
        """


class AzureEmbeddingClient(EmbeddingClient):
    """
    The embedding client for Azure OpenAI
    """

    def __init__(self, settings: Settings) -> None:
        self._client = AsyncAzureOpenAI(
            api_key=settings.embedding.api_key.get_secret_value(),
            api_version=settings.embedding.api_version,
            azure_endpoint=settings.embedding.api_endpoint,
        )
        self._model = settings.embedding.model
        self.max_length = settings.similarity.max_length

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generates an embedding from a list of texts

        Args:
            texts: list of texts

        Returns:
            list[list[float]]: embedding of texts
        """
        response = await self._client.embeddings.create(
            input=texts,
            model=self._model,
            encoding_format="float",
        )
        return [item.embedding for item in response.data]


class MockEmbeddingClient(EmbeddingClient):
    """
    The mock embedding client

    This is used for testing purposes
    """

    def __init__(self, embeddings: list[list[float]]) -> None:
        self._embeddings = embeddings
        self.max_length = 2400

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generates an embedding from a list of texts

        Args:
            texts: list of texts

        Returns:
            list[list[float]]: embedding of texts

        Keep in mind the embeddings that it creates are the same as the ones made on initialization
        """
        return self._embeddings
