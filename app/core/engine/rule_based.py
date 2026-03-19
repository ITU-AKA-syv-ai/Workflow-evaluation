from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.evaluators.base import BaseEvaluator
from app.core.models.evaluation_model import EvaluationResult
from app.core.models.rules.base import Rule, RuleResultConfig
from app.core.models.rules.format_rules import FormatRule, FormatRuleConfig
from app.core.models.rules.keyword_rules import KeywordRule, KeywordRuleConfig
from app.core.models.rules.regex_rules import RegexRule, RegexRuleConfig

# todo: check all outputs are renamed to inputs in all relevant files in our pull request (or if not okay'ed from daily, then change input to output
# todo: check that all important logic from length_evaluator and substring_evalautor, then delete those files


class RuleBasedEvaluatorConfig(BaseModel):
    """
    Configuration for the rule-based evaluator.
    Contains a list of rules and their parameters (name, weight, etc.).

    Attributes:
        rules (list[FormatRuleConfig | RegexRuleConfig | KeywordRuleConfig]):
                List of rule configurations with each rule having a unique name and a weight.

    """
    rules: list[FormatRuleConfig | RegexRuleConfig | KeywordRuleConfig]


class RuleBasedEvaluator(BaseEvaluator):
    """
    Evaluator that applies multiple rules to a model input.

    Builds a list of rules from the config, then runs each rule on the input.
    Aggregates the results into a single score and reasoning.
    """
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
        # Validate the incoming config (structure and type) and convert it into a typed config object.
        try:
            return RuleBasedEvaluatorConfig.model_validate(config)
        except ValidationError:
            return None  # evaluation_service handles the error

    @property
    def default_threshold(self) -> float:
        """
        Returns:
            float: 1.0 as it must be 100% correct to pass.
        """
        return 1.0

    def _evaluate(
        self, output: str, config: RuleBasedEvaluatorConfig
    ) -> EvaluationResult:
        """
        Evaluates the input against the listed rules.

        Builds rule objects from the config, then runs each rule on the input.
        Collects the results into a single score and reasoning.

        Args:
            output (str): The input to evaluate.
            config (RuleBasedEvaluatorConfig): The configuration specifying the rules to apply.

        Returns:
            EvaluationResult: The evaluation result containing the evaluator ID, normalised score, reasoning, and error status.
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
        """
        Turns a rule config into a concrete rule object.
        This allows the evaluator to support multiple rule types.

        Args:
            rule_config (FormatRuleConfig | RegexRuleConfig | KeywordRuleConfig): The rule config to be converted.

        Returns:
            Rule: The concrete rule object.
        """
        if isinstance(rule_config, RegexRuleConfig):
            return RegexRule(rule_config)
        if isinstance(rule_config, KeywordRuleConfig):
            return KeywordRule(rule_config)
        if isinstance(rule_config, FormatRuleConfig):
            return FormatRule(rule_config)
        raise ValueError(f"Unknown rule config: {rule_config}")

    def _calculate_normalised_score(
        self, rule_results: list[RuleResultConfig]
    ) -> float:
        """
        Compute weighted average score across all rules.
        Each rule contributes: weight * score
        Final score = sum(weighted scores) / sum(weights)

        Args:
            rule_results (list[RuleResultConfig]): List of rule results to aggregate.

        Returns:
            float: Normalised score.
        """
        total_weight = sum(result.weight for result in rule_results)

        if total_weight == 0:
            return 0.0

        earned_score = sum(result.weight * result.score for result in rule_results)
        return earned_score / total_weight

    def _build_reasoning(self, rule_results: list[RuleResultConfig]) -> str:
        """
        Build explanation of results including the number of rules passed and per-rule breakdown (pass/fail + reasoning).

        Args:
            rule_results (list[RuleResultConfig]): List of rule results to build explanation for.

        Returns:
            str: Explanation of results.
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
