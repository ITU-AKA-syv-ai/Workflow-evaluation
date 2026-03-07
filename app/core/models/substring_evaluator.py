from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.models.base import BaseEvaluator


class SubstringEvaluatorConfig(BaseModel):
    substring: str


class SubstringEvaluator(BaseEvaluator):
    @property
    def name(self) -> str:
        return "substring_evaluator"

    @property
    def description(self) -> str:
        return "Evaluates whether a string contains a specific substring"

    @property
    def config_schema(self) -> dict[str, Any]:
        return SubstringEvaluatorConfig.model_json_schema()

    def bind(self, config: dict[str, Any]) -> SubstringEvaluatorConfig | None:
        try:
            return SubstringEvaluatorConfig.model_validate(config)
        except ValidationError:
            return None

    def evaluate(self, output: str, config: SubstringEvaluatorConfig) -> bool:
        """
        Evaluates whether the output contains the substring specified in the config.

        Args:
            output (str): The full string to evaluate if it contains the substring.
            config (SubstringEvaluatorConfig): The configuration specifying the substring to look for.

        Returns:
            bool: True if the output contains the substring, False otherwise.
        """
        return config.substring in output
