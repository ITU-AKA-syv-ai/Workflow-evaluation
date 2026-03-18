from typing import Any

from pydantic import BaseModel, ValidationError
from scipy.spatial.distance import cosine as distance
from sentence_transformers import SentenceTransformer

from app.core.evaluators.base import BaseEvaluator
from app.core.models.evaluation_model import EvaluationResult


class CosineEvaluatorConfig(BaseModel):
    """
    Configuration for the CosineEvaluator.

    Defines the standard for the cosine similarity.

    Attributes:
        standard (str): The standard used in the cosine similarity.
    """

    standard: str


class CosineEvaluator(BaseEvaluator):
    @property
    def name(self) -> str:
        return "cosine_similarity_evaluator"

    @property
    def description(self) -> str:
        return (
            "Evaluates the cosine similarity between a know standard an the ai output"
        )

    @property
    def config_schema(self) -> dict[str, Any]:
        return CosineEvaluatorConfig.model_json_schema()

    @property
    def default_threshold(self) -> float:
        return 0.7

    def validate_config(self, config: dict[str, Any]) -> CosineEvaluatorConfig | None:
        """
        Converts a configuration consisting of `{ "golden_standard": x }` where x is a string to an instance of CosineEvaluatorConfig with the golden_standard field set to x.
        None is returned if the config is malformed

        Args:
            config (dict[str, Any]): The config to bind to a CosineEvaluatorConfig

        Returns:
            CosineEvaluatorConfig | None: Returns CosineEvaluatorConfig if config is correctly formattered, otherwise None is returned

        """
        try:
            return CosineEvaluatorConfig.model_validate(config)
        except ValidationError:
            return None

    def _evaluate(self, output: str, config: CosineEvaluatorConfig) -> EvaluationResult:
        """
        Calculates the cosine similarity between a know standard and the AI output
        Args:
            output (str): The AI output to be evaluated
            config (CosineEvaluatorConfig): The config that defines the standard

        Returns:
            EvaluationResult: Result which contains the evaluator id,score and a potential error message. The remaining fields are set by the "evaluate" method defined in BaseEvaluator.
        """

        if len(config.standard) == 0:
            message = "the standard cannot be empty"
            return EvaluationResult(
                evaluator_id=self.name,
                reasoning=message,
                error=message,
            )
        if len(output) == 0:
            message = "the output cannot be empty"
            return EvaluationResult(
                evaluator_id=self.name,
                reasoning=message,
                error=message,
            )
        if len(config.standard) > 2400:
            message = "the standard cannot be greater than 2400"
            return EvaluationResult(
                evaluator_id=self.name,
                reasoning=message,
                error=message,
            )
        if len(output) > 2400:
            message = "the output cannot be greater than 2400"
            return EvaluationResult(
                evaluator_id=self.name,
                reasoning=message,
                error=message,
            )

        # sets the NLP model to embed the words into vectors
        model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

        embeddings = model.encode([output, config.standard])

        # calculates the cosine similarity of the two vectors using the scipy library
        dist = 1 - distance(embeddings[0], embeddings[1])
        message = f"The similarity between the standard and ai output is {dist}"
        return EvaluationResult(
            evaluator_id=self.name,
            reasoning=message,
            normalised_score=dist,
        )
