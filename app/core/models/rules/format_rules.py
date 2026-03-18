import json
from typing import Literal

from pydantic import Field

from app.core.models.rules.base import BaseRuleConfig, Rule, RuleResultConfig


class FormatRuleConfig(BaseRuleConfig):
    name: Literal["format"]
    kind: Literal["valid_json", "max_length"]
    max_length: int | None = None


class FormatRule(Rule):
    config: FormatRuleConfig

    def __init__(self, config: FormatRuleConfig) -> None:
        super().__init__(config)
        self.config = config

    def evaluate(self, input: str) -> RuleResultConfig:
        if self.config.kind == "valid_json":
            return self._evaluate_valid_json(input)

        if self.config.kind == "max_length":
            return self._evaluate_max_length(input)

        return RuleResultConfig(
            rule_name=self.config.name,
            passed=False,
            weight=self.config.weight,
            score=0.0,
            reasoning=f"Unsupported format rule kind: {self.config.kind}",
        )

    def _evaluate_valid_json(self, output: str) -> RuleResultConfig:
        try:
            json.loads(output)
        except json.JSONDecodeError:
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=False,
                weight=self.config.weight,
                score=0.0,
                reasoning="Output is not valid JSON.",
            )

        return RuleResultConfig(
            rule_name=self.config.name,
            passed=True,
            weight=self.config.weight,
            score=1.0,
            reasoning="Output is valid JSON.",
        )

    def _evaluate_max_length(self, output: str) -> RuleResultConfig:
        if self.config.max_length is None:
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=False,
                weight=self.config.weight,
                score=0.0,
                reasoning="Format rule kind 'max_length' requires 'max_length' to be set.",
            )

        actual_length = len(output)

        if actual_length <= self.config.max_length:
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=True,
                weight=self.config.weight,
                score=1.0,
                reasoning=f"Output length {actual_length} is within max length {self.config.max_length}.",
            )

        return RuleResultConfig(
            rule_name=self.config.name,
            passed=False,
            weight=self.config.weight,
            score=0.0,
            reasoning=f"Output length {actual_length} exceeds max length {self.config.max_length}.",
        )
