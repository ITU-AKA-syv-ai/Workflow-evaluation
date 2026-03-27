from typing import Any

from pydantic import BaseModel, Field, ValidationError
from scipy.spatial.distance import cosine as distance

from app.core.evaluators.base import BaseEvaluator
from app.core.models.embeddings import EmbeddingClient
from app.core.models.evaluation_model import EvaluationResult


class CosineEvaluatorConfig(BaseModel):
    """
    Configuration for the CosineEvaluator.

    Defines the reference for the cosine similarity.

    Attributes:
        reference (str): The reference used in the cosine similarity.
    """

    reference: str = Field(..., min_length=1, max_length=2400)


class CosineEvaluator(BaseEvaluator):
    def __init__(self, embedding_client: EmbeddingClient) -> None:
        self._embedding_client = embedding_client

    @property
    def name(self) -> str:
        return "cosine_similarity_evaluator"

    @property
    def description(self) -> str:
        return "Evaluates the cosine similarity between a know reference an the ai output"

    @property
    def config_schema(self) -> dict[str, Any]:
        return CosineEvaluatorConfig.model_json_schema()

    @property
    def default_threshold(self) -> float:
        return 0.7

    def validate_config(self, config: dict[str, Any]) -> CosineEvaluatorConfig | None:
        """
        Converts a configuration consisting of `{ "reference": x }` where x is a string to an instance of CosineEvaluatorConfig with the reference field set to x.
        None is returned if the config is malformed

        Args:
            config (dict[str, Any]): The config to bind to a CosineEvaluatorConfig

        Returns:
            CosineEvaluatorConfig | None: Returns CosineEvaluatorConfig if config is correctly formatted, otherwise None is returned

        """
        try:
            return CosineEvaluatorConfig.model_validate(config)
        except ValidationError:
            return None

    async def _evaluate(self, output: str, config: CosineEvaluatorConfig) -> EvaluationResult:
        """
        Calculates the cosine similarity between a know reference and the AI output
        Args:
            output (str): The AI output to be evaluated
            config (CosineEvaluatorConfig): The config that defines the reference

        Returns:
            EvaluationResult: Result which contains the evaluator id,score and a potential error message. The remaining fields are set by the "evaluate" method defined in BaseEvaluator.
        """
        if len(output) == 0:
            message = "the output cannot be empty"
            return EvaluationResult(
                evaluator_id=self.name,
                reasoning=message,
                error=message,
            )

        if len(output) > self._embedding_client.max_length:
            message = "the output cannot be greater than 2400"
            return EvaluationResult(
                evaluator_id=self.name,
                reasoning=message,
                error=message,
            )

        embeddings = await self._embedding_client.embed([config.reference, output])

        # calculates the cosine similarity of the two vectors using the scipy library
        dist = 1 - distance(embeddings[0], embeddings[1])
        message = f"The similarity between the reference and ai output is {dist}"
        return EvaluationResult(
            evaluator_id=self.name,
            reasoning=message,
            normalised_score=dist,
        )
