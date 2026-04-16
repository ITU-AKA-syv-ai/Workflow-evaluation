import re
from typing import Literal

from pydantic import Field

from backend.app.core.models.rules.base import BaseRuleConfig, Rule, RuleResultConfig


class RegexRuleConfig(BaseRuleConfig):
    """
    Configuration for regex rules.

    Attributes:
        name (str): The name of the rule.
        pattern (str): The regex pattern to match.
    """

    name: Literal["regex"]
    pattern: str = Field(..., description="Regex pattern to match")


class RegexRule(Rule):
    """
    Regex rule that checks if an output matches a regex pattern.

    Attributes:
        config (RegexRuleConfig): The configuration for the rule.
    """

    config: RegexRuleConfig

    def __init__(self, config: RegexRuleConfig) -> None:
        super().__init__(config)
        self.config = config

    def evaluate(self, output: str) -> RuleResultConfig:
        """
        Evaluate whether the output matches the regex pattern.

        Args:
            output (str): The output to evaluate.

        Returns:
            RuleResultConfig: The result of the evaluation with the rule name, passed status, weight, score, and reasoning.

        """
        try:
            matched = re.search(self.config.pattern, output) is not None
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
