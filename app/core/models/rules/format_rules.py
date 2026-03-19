import json
from typing import Literal

from app.core.models.rules.base import BaseRuleConfig, Rule, RuleResultConfig


class FormatRuleConfig(BaseRuleConfig):
    """
    Configuration for format rules.

    Attributes:
        name (str): The name of the rule.
        kind (str): The kind of format rule. Can be "valid_json" or "max_length".
        max_length (int | None): The maximum length of the output. Required if kind is "max_length".
    """
    name: Literal["format"]
    kind: Literal["valid_json", "max_length"]
    max_length: int | None = None


class FormatRule(Rule):
    """
    Format rule that checks the format of the output based on the rule's kind.

    Attributes:
        config (FormatRuleConfig): The configuration for the rule.
    """
    config: FormatRuleConfig

    def __init__(self, config: FormatRuleConfig) -> None:
        super().__init__(config)
        self.config = config

    def evaluate(self, output: str) -> RuleResultConfig:
        """
        Evaluate the format rule based on the rule's kind.
        Supported kinds: "valid_json" and "max_length".

        Args:
            output (str): The output to evaluate.

        Returns:
            RuleResultConfig: The result of the evaluation with the rule name, passed status, weight, score, and reasoning.
        """
        if self.config.kind == "valid_json":
            return self._evaluate_valid_json(output)

        if self.config.kind == "max_length":
            return self._evaluate_max_length(output)

        return RuleResultConfig(
            rule_name=self.config.name,
            passed=False,
            weight=self.config.weight,
            score=0.0,
            reasoning=f"Unsupported format rule kind: {self.config.kind}",
        )

    def _evaluate_valid_json(self, output: str) -> RuleResultConfig:
        """
        Evaluates whether the output is valid JSON or not.

        Args:
            output (str): The output to evaluate.

        Returns:
            RuleResultConfig: The result of the evaluation with the rule name, passed status, weight, score, and reasoning.
            If the output is valid JSON, the score is 1.0, and the status is true.
            Otherwise, the score is 0.0 and the status is false.
        """
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
        """
        Evaluates whether the output length is within the specified maximum length.
        If the output is within the maximum length, the score is 1.0, and the status is true.
        Otherwise, the score is 0.0 and the status is false.

       Args:
            output (str): The output to evaluate.

        Returns:
        RuleResultConfig: The result of the evaluation with the rule name, passed status, weight, score, and reasoning.
        """
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
