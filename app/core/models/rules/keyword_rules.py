import re
from typing import Literal

from app.core.models.rules.base import BaseRuleConfig, Rule, RuleResultConfig
from app.utils.substring_matching_utils import find_longest_partial_substring


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

        Args:
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
            It will locate the closest match and return that as part of the reasoning.

        Args:
            output (str): The output to evaluate.

        Returns:
            RuleResultConfig: The result of the evaluation with the rule name, passed status, weight, score, and reasoning.
        """
        keyword = self.config.keyword

        if keyword == "":
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=False,
                weight=self.config.weight,
                score=0.0,
                reasoning="An empty string is not a valid keyword.",
            )

        # Check if the keyword is present in the output.
        # Ensures that the keyword is not a substring of another word and is not case-sensitive.
        pattern = rf"\b{re.escape(keyword)}\b"
        matched = re.search(pattern, output, flags=re.IGNORECASE) is not None

        if matched:
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=True,
                weight=self.config.weight,
                score=1.0,
                reasoning="The required keyword '" + keyword + "' is present in the output.",
            )

        # If the keyword is not present in the output, it is considered a failure and returns a score of 0.0.
        # It will locate the closest match and return that as part of the reasoning.
        partial_match = find_longest_partial_substring(keyword, output)
        if partial_match:  # A match was found
            reasoning_text = (
                f"The required keyword '{keyword}' is not present in the output. "
                f"A close match '{partial_match}' was found."
            )
        else:  # No match was found
            reasoning_text = f"The required keyword '{keyword}' is not present in the output. No close match was found."

        return RuleResultConfig(
            rule_name=self.config.name,
            passed=False,
            weight=self.config.weight,
            score=0.0,
            reasoning=reasoning_text,
        )

    def _evaluate_forbidden(self, output: str) -> RuleResultConfig:
        """
        Evaluates whether the required keyword is present in the input.
        If the forbidden string is not present in the output, the score is 1.0, and the status is true.
        Otherwise, the score is 0.0 and the status is false.

        Args:
            output (str): The output to evaluate.

        Returns:
            RuleResultConfig: The result of the evaluation with the rule name, passed status, weight, score, and reasoning.
        """
        keyword = self.config.keyword

        if keyword == "":
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=False,
                weight=self.config.weight,
                score=0.0,
                reasoning="An empty string will always fail the forbidden keyword rule.",
            )

        # Check if the keyword is present in the output.
        # Ensures that the keyword is not a substring of another word and is not case-sensitive.
        pattern = rf"\b{re.escape(keyword)}\b"
        matched = re.search(pattern, output, flags=re.IGNORECASE) is not None
        if matched:
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
