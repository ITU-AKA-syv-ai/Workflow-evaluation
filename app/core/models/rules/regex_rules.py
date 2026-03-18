import re
from typing import Literal
from pydantic import Field

from app.core.models.rules.base import BaseRule, BaseRuleConfig, RuleResult


class RegexRuleConfig(BaseRuleConfig):
    name: Literal["regex"]
    pattern: str = Field(..., description="Regex pattern to match")


class RegexRule(BaseRule):
    config: RegexRuleConfig

    def __init__(self, config: RegexRuleConfig):
        super().__init__(config)
        self.config = config

    def evaluate(self, output: str) -> RuleResult:
        try:
            matched = re.search(self.config.pattern, output) is not None
        except re.error as exc:
            return RuleResult(
                rule_name=self.config.name,
                passed=False,
                weight=self.config.weight,
                score=0.0,
                reasoning=f"Invalid regex pattern: {exc}",
            )

        if matched:
            return RuleResult(
                rule_name=self.config.name,
                passed=True,
                weight=self.config.weight,
                score=1.0,
                reasoning="Pattern matched",
            )

        return RuleResult(
            rule_name=self.config.name,
            passed=False,
            weight=self.config.weight,
            score=0.0,
            reasoning="Pattern not found",
        )