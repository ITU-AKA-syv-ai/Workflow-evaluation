from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.evaluators.base import BaseEvaluator
from app.core.models.evaluation_model import EvaluationResult
from app.core.models.rules.base import Rule, RuleResultConfig
from app.core.models.rules.format_rules import FormatRule, FormatRuleConfig
from app.core.models.rules.keyword_rules import KeywordRule, KeywordRuleConfig
from app.core.models.rules.regex_rules import RegexRule, RegexRuleConfig

# todo delete comments


# Validate top-level rule-based config
class RuleBasedEvaluatorConfig(BaseModel):
    """ Configuration for the rule-based evaluator.

    Attributes:
        rules (list[FormatRuleConfig | RegexRuleConfig | KeywordRuleConfig]):
                List of rule configurations with each rule having a unique name and a weight.

    """
    rules: list[FormatRuleConfig | RegexRuleConfig | KeywordRuleConfig]


class RuleBasedEvaluator(BaseEvaluator):
    """ Evaluator that applies multiple rules to a model output.

        - builds rule objects from configs
        - runs each rule
        - aggregates results into one score and reasoning """
    @property
    def name(self) -> str:
        return "rule_based_evaluator"

    @property
    def description(self) -> str:
        return "Evaluates model input using deterministic rule-based checks."

    @property
    def config_schema(self) -> dict[str, Any]:
        return RuleBasedEvaluatorConfig.model_json_schema()  # returns a JSON schema describing what config this evaluator expects. To be discoverable for get_evaluators

    def validate_config(self, config: dict[str, Any]) -> RuleBasedEvaluatorConfig | None:
        # Validate incoming config (structure and type) and convert it into a typed config object.
        try:
            return RuleBasedEvaluatorConfig.model_validate(config)
        except ValidationError:
            return None  # evaluation_service handles the error

    @property
    def default_threshold(self) -> float:
        # Normalised score must be 1 for this evaluator to pass.
        return 1.0

    def _evaluate(
        self, output: str, config: RuleBasedEvaluatorConfig
    ) -> EvaluationResult:
        """
        Steps:
        1. Build rule objects from configs
        2. Run each rule on the output
        3. Collect per-rule results
        4. Aggregate into a single score and reasoning
        """
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

    def _build_rule(self, rule_config: FormatRuleConfig | RegexRuleConfig | KeywordRuleConfig) -> Rule:
        """ turns a rule config into a concrete rule object. This allows the evaluator to support multiple rule types."""
        if isinstance(rule_config, RegexRuleConfig):
            return RegexRule(rule_config)
        if isinstance(rule_config, KeywordRuleConfig):
            return KeywordRule(rule_config)
        if isinstance(rule_config, FormatRuleConfig):
            return FormatRule(rule_config)
        raise ValueError(f"Unknown rule config: {rule_config}")

# Aggregate score
    def _calculate_normalised_score(
        self, rule_results: list[RuleResultConfig]
    ) -> float:
        """
        Compute weighted average score across all rules.
        Each rule contributes: weight * score
        Final score = sum(weighted scores) / sum(weights)
        """
        total_weight = sum(result.weight for result in rule_results)

        if total_weight == 0:
            return 0.0

        earned_score = sum(result.weight * result.score for result in rule_results)
        return earned_score / total_weight

# Build reasoning breakdown
    def _build_reasoning(self, rule_results: list[RuleResultConfig]) -> str:
        """
        Build explanation of results.

        Includes:
        - number of rules passed
        - per-rule breakdown (pass/fail + reasoning)
        """
        if not rule_results:
            return "No rules were configured."

        passed_count = sum(1 for result in rule_results if result.passed)  # Counts number of rules passed
        total_count = len(rule_results)  # Counts number of rules total

        breakdown = "; ".join(  # Per-rule breakdown, then joined together
            f"{result.rule_name}: {'pass' if result.passed else 'fail'} ({result.reasoning})"
            for result in rule_results
        )

        return f"{passed_count}/{total_count} rules passed. {breakdown}"