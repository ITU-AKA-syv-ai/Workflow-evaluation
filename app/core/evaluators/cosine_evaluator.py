from typing import Any
from pydantic import BaseModel, ValidationError

from app.core.evaluators.base import BaseEvaluator, T
from app.core.models.evaluation_model import EvaluationResult

from sentence_transformers import SentenceTransformer
from scipy.spatial.distance import cosine as distance

class CosineEvaluatorConfig(BaseModel):
    golden_standard: str
class CosineEvaluator(BaseEvaluator):

    @property
    def name(self) -> str:
        return "cosine_similarity_evaluator"


    @property
    def description(self) -> str:
        return "Evaluates the cosine similarity between a know standard an the ai output"

    @property
    def config_schema(self) -> dict[str,Any]:
        return CosineEvaluatorConfig.model_json_schema()



    @property
    def default_threshold(self) -> float:
        return 0.7

    def validate_config(self, config: dict[str, Any]) -> CosineEvaluatorConfig | None:
        try:
            bound_config = CosineEvaluatorConfig.model_validate(config)

            if bound_config.golden_standard is None:
                return None
            return bound_config
        except ValidationError:
            return None

    def _evaluate(self, output: str, config: CosineEvaluatorConfig) -> EvaluationResult:
        if len(config.golden_standard) == 0:
            message = "the standard cannot be empty"
            return EvaluationResult(
                evaluator_id= self.name,
                reasoning= message,
                error= message,
            )
        if len(output) == 0:
            message = "the output cannot be empty"
            return EvaluationResult(
                evaluator_id= self.name,
                reasoning= message,
                error= message,
            )
        if len(config.golden_standard) > 2400:
            message = "the standard cannot be greater than 2400"
            return EvaluationResult(
                evaluator_id= self.name,
                reasoning= message,
                error= message,
            )
        if len(output) > 2400:
            message = "the output cannot be greater than 2400"
            return EvaluationResult(
                evaluator_id= self.name,
                reasoning= message,
                error= message,
            )

        model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

        embeddings = model.encode([output, config.golden_standard])

        dist = 1- distance(embeddings[0], embeddings[1])
        message = "The similarity between the standard and ai output is {}".format(dist)
        return EvaluationResult(
            evaluator_id=self.name,
            reasoning= message,
            normalised_score= dist,
        )