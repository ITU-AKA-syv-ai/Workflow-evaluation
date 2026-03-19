from typing import Literal

from app.core.models.rules.base import BaseRuleConfig, Rule, RuleResultConfig


class KeywordRuleConfig(BaseRuleConfig):
    name: Literal["keyword"]
    kind: Literal["required", "forbidden"]
    keyword: str #todo: where will weight be put?


class KeywordRule(Rule):
    config: KeywordRuleConfig

    def __init__(self, config: KeywordRuleConfig) -> None:
        super().__init__(config)
        self.config = config

    def evaluate(self, input: str) -> RuleResultConfig:
        if self.config.kind == "required":
            return self._evaluate_required(input)

        if self.config.kind == "forbidden":
            return self._evaluate_forbidden(input)

        return RuleResultConfig(
            rule_name=self.config.name,
            passed=False,
            weight=self.config.weight,
            score=0.0,
            reasoning=f"Unsupported format rule kind: {self.config.kind}",
        )

    def _evaluate_required(self, input: str) -> RuleResultConfig:
        keyword = self.config.keyword

        if keyword == "":
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=True,
                weight=self.config.weight,
                score=1.0,
                reasoning="The empty string is a substring of all strings.",
            )

        if keyword.lower() in input.lower():
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=True,
                weight=self.config.weight,
                score=1.0,
                reasoning="The required keyword is present in the input.",
            )
        return RuleResultConfig(
            rule_name=self.config.name,
            passed=False,
            weight=self.config.weight,
            score=0.0,
            reasoning="The required keyword is not present in the input.",
        )

    def _evaluate_forbidden(self, input: str) -> RuleResultConfig:
        keyword = self.config.keyword
        if keyword.lower() in input.lower():
            return RuleResultConfig(
                rule_name=self.config.name,
                passed=False,
                weight=self.config.weight,
                score=0.0,
                reasoning="The forbidden keyword is present in the input.",
            )
        return RuleResultConfig(
            rule_name=self.config.name,
            passed=True,
            weight=self.config.weight,
            score=1.0,
            reasoning="The forbidden keyword is not present in the input.",
        )
    # todo: check for how close (algorithm)
    # todo: Should empty string be allowed and pass or be handled as an error/a fail?
    # todo: right now searching for cat in a text with concatenate would be handled as a match. Should it?