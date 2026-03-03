from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.models.base import BaseEvaluator


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
            return LengthEvaluatorConfig.model_validate(config)
        except ValidationError:
            return None

    def evaluate(self, output: str, config: LengthEvaluatorConfig) -> bool:
        return len(output) == config.expected_length
