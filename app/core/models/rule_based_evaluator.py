#todo delete comments
# Accept a configurable list of rules, each with a name and a weight
# The score should reflect the weighted proportion of rules passed
# The reasoning field should include a per-rule breakdown so users can see exactly what passed and what failed

from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.evaluators.base import BaseEvaluator
from app.core.models.evaluation_model import EvaluationResult
from app.core.models.rules.base import BaseRuleConfig, Rule, RuleResultConfig
from app.core.models.rules.format_rules import FormatRule, FormatRuleConfig
from app.core.models.rules.regex_rules import RegexRule, RegexRuleConfig


# Validate top-level rule-based config
class RuleBasedEvaluatorConfig(BaseModel):
    '''Base class for rule based evaluators'''
    rules: list[FormatRuleConfig | RegexRuleConfig] #todo add keyword


class RuleBasedEvaluator(BaseEvaluator):
    @property
    def name(self) -> str:
        return "rule_based_evaluator"

    @property
    def description(self) -> str:
        return "Evaluates model input using deterministic rule-based checks."

    @property
    def config_schema(self) -> dict[str, Any]:
        return RuleBasedEvaluatorConfig.model_json_schema()

    def validate_config(self, config: dict[str, Any]) -> RuleBasedEvaluatorConfig | None:
        try:
            return RuleBasedEvaluatorConfig.model_validate(config)
        except ValidationError:
            return None

    @property
    def default_threshold(self) -> float:
        return 1.0

# Build/run each rulee
    def _evaluate(
        self, output: str, config: RuleBasedEvaluatorConfig
    ) -> EvaluationResult:
        rule_results: list[RuleResultConfig] = []

        for rule_config in config.rules:
            rule = self._build_rule(rule_config)
            result = rule.evaluate(output)
            rule_results.append(result)

        normalised_score = self._calculate_normalised_score(rule_results)
        reasoning = self._build_reasoning(rule_results)

        return EvaluationResult(
            evaluator_id=self.name,
            reasoning=reasoning,
            normalised_score=normalised_score,
            error=None,
        )

    def _build_rule(self, rule_config: FormatRuleConfig | RegexRuleConfig) -> Rule: #todo add keyword
        if isinstance(rule_config, RegexRuleConfig):
            return RegexRule(rule_config)
        '''todo add in when configured
        if isinstance(rule_config, KeywordRuleConfig):
            return KeywordRule(rule_config)'''
        if isinstance (rule_config, FormatRuleConfig):
            return FormatRule(rule_config)
        raise ValueError(f"Unknown rule config: {rule_config}")

# Aggregate score
    def _calculate_normalised_score(
        self, rule_results: list[RuleResultConfig]
    ) -> float:
        total_weight = sum(result.weight for result in rule_results)

        if total_weight == 0:
            return 0.0

        earned_score = sum(result.weight * result.score for result in rule_results)
        return earned_score / total_weight

# Build reasoning breakdown
    def _build_reasoning(self, rule_results: list[RuleResultConfig]) -> str:
        if not rule_results:
            return "No rules were configured."

        passed_count = sum(1 for result in rule_results if result.passed)
        total_count = len(rule_results)

        breakdown = "; ".join(
            f"{result.rule_name}: {'pass' if result.passed else 'fail'} ({result.reasoning})"
            for result in rule_results
        )

        return f"{passed_count}/{total_count} rules passed. {breakdown}"