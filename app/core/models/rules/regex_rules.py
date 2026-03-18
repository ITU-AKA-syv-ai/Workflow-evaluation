import re
from typing import Literal

from pydantic import Field

from app.core.models.rules.base import BaseRuleConfig, Rule, RuleResultConfig


class RegexRuleConfig(BaseRuleConfig):
    name: Literal["regex"]
    pattern: str = Field(..., description="Regex pattern to match")


class RegexRule(Rule):
    config: RegexRuleConfig

    def __init__(self, config: RegexRuleConfig) -> None:
        super().__init__(config)
        self.config = config

    def evaluate(self, input: str) -> RuleResultConfig:
        try:
            matched = re.search(self.config.pattern, input) is not None
        except re.error as exc:
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=False,
                weight=self.config.weight,
                score=0.0,
                reasoning=f"Invalid regex pattern: {exc}",
            )

        if matched:
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=True,
                weight=self.config.weight,
                score=1.0,
                reasoning="Pattern matched",
            )

        return RuleResultConfig(
            rule_name=self.config.name,
            passed=False,
            weight=self.config.weight,
            score=0.0,
            reasoning="Pattern not found",
        )