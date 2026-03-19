from typing import Literal

from app.core.models.rules.base import BaseRuleConfig, Rule, RuleResultConfig


class KeywordRuleConfig(BaseRuleConfig):
    """
    Configuration for keyword rules.

    Attributes:
        name (str): The name of the rule.
        kind (str): The kind of keyword rule. Can be "required" or "forbidden".
        keyword (str): The keyword to look for in the output.
    """
    name: Literal["keyword"]
    kind: Literal["required", "forbidden"]
    keyword: str


class KeywordRule(Rule):
    """
    Keyword rule that checks if a keyword is present in the output.
    It can be configured to check if the keyword is required or forbidden.

    Attributes:
        config (KeywordRuleConfig): The configuration for the rule.
    """
    config: KeywordRuleConfig

    def __init__(self, config: KeywordRuleConfig) -> None:
        super().__init__(config)
        self.config = config

    def evaluate(self, output: str) -> RuleResultConfig:
        """
        Evaluate the rule based on the rule's kind.
        Supported kinds: "required" and "forbidden".

        Attributes:
            output (str): The output to evaluate.

        Returns:
            RuleResultConfig: The result of the evaluation with the rule name, passed status, weight, score, and reasoning.
        """
        if self.config.kind == "required":
            return self._evaluate_required(output)

        if self.config.kind == "forbidden":
            return self._evaluate_forbidden(output)

        return RuleResultConfig(
            rule_name=self.config.name,
            passed=False,
            weight=self.config.weight,
            score=0.0,
            reasoning=f"Unsupported keyword rule kind: {self.config.kind}",
        )

    def _evaluate_required(self, output: str) -> RuleResultConfig:
        """
        Evaluates whether the required keyword is present in the output.
        If the required string is present in the output, the score is 1.0, and the status is true.
            Otherwise, the score is 0.0 and the status is false.

        Attributes:
            output (str): The output to evaluate.

        Returns:
            RuleResultConfig: The result of the evaluation with the rule name, passed status, weight, score, and reasoning.
        """
        keyword = self.config.keyword

        if keyword == "":
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=True,
                weight=self.config.weight,
                score=1.0,
                reasoning="The empty string is a substring of all strings.",
            )

        if keyword.lower() in output.lower():
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=True,
                weight=self.config.weight,
                score=1.0,
                reasoning="The required keyword is present in the output.",
            )
        return RuleResultConfig(
            rule_name=self.config.name,
            passed=False,
            weight=self.config.weight,
            score=0.0,
            reasoning="The required keyword is not present in the output.",
        )

    def _evaluate_forbidden(self, output: str) -> RuleResultConfig:
        """
        Evaluates whether the required keyword is present in the input.
        If the forbidden string is not present in the output, the score is 1.0, and the status is true.
        Otherwise, the score is 0.0 and the status is false.

        Attributes:
            output (str): The output to evaluate.

        Returns:
            RuleResultConfig: The result of the evaluation with the rule name, passed status, weight, score, and reasoning.
        """
        keyword = self.config.keyword
        if keyword.lower() in output.lower():
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=False,
                weight=self.config.weight,
                score=0.0,
                reasoning="The forbidden keyword is present in the output.",
            )
        return RuleResultConfig(
            rule_name=self.config.name,
            passed=True,
            weight=self.config.weight,
            score=1.0,
            reasoning="The forbidden keyword is not present in the output.",
        )
    # todo: check for how close (algorithm)
    # todo: Should empty string be allowed and pass or be handled as an error/a fail?
    # todo: right now searching for cat in a text with concatenate would be handled as a match. Should it?