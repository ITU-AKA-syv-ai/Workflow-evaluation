from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.models.base import BaseEvaluator
from app.core.models.evaluation_model import EvaluationResult


class LengthEvaluatorConfig(BaseModel):
    expected_length: int


class LengthEvaluator(BaseEvaluator):
    @property
    def name(self) -> str:
        return "length_evaluator"

    @property
    def description(self) -> str:
        return "Evaluates whether a string matches an expected length"

    @property
    def config_schema(self) -> dict[str, Any]:
        return LengthEvaluatorConfig.model_json_schema()

    def bind(self, config: dict[str, Any]) -> LengthEvaluatorConfig | None:
        try:
            bound_config = LengthEvaluatorConfig.model_validate(config)
            if bound_config.expected_length < 0:
                return None
            return bound_config
        except ValidationError:
            return None

    @property
    def default_threshold(self) -> float:
        return 1

    def _evaluate(self, output: str, config: LengthEvaluatorConfig) -> EvaluationResult:
        normalised_score = 0

        if config.expected_length < 0:
            message = f"Expected length cannot be negative({config.expected_length})"
            return EvaluationResult(
                evaluator_id=self.name,
                passed=False,
                reasoning=message,
                normalised_score=0,
                execution_time=0,
                error=message,
            )

        if config.expected_length == 0:
            normalised_score = 1 / (len(output) + 1)
        else:
            normalised_score = 1 - (
                abs(len(output) - config.expected_length) / config.expected_length
            )
            # If the actual length is more than 2x the expected, then the score becomes negative
            normalised_score = max(0, normalised_score)

        reasoning = f"The length of the string({len(output)}) "
        if len(output) == config.expected_length:
            reasoning += f"matches the expected length({config.expected_length})"
        elif len(output) < config.expected_length:
            reasoning += f"is shorter the expected length({config.expected_length})"
        elif len(output) > config.expected_length:
            reasoning += f"is longer the expected length({config.expected_length})"

        return EvaluationResult(
            evaluator_id=self.name,
            reasoning=reasoning,
            normalised_score=normalised_score,
        )
