
from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field


class BaseRuleConfig(BaseModel):
    """
    Configuration for what a user/evaluator must supply to a rule.

    Attributes:
        name (Literal["regex", "format", "keyword"]): The type of rule this is.
        weight (float): How much this rule's result should be weighted in an aggreagted result.
    """
    name: Literal["regex", "format", "keyword"]
    weight: float = Field(default=1.0)


class RuleResultConfig(BaseModel):
    """
    Result of a single rule check.

    Attributes:
        rule_name (str): The name of the rule that was evaluated.
        passed (bool): Whether the rule passed or failed.
        weight (float): How much this rule's result should be weighted in an aggreagted result.
        score (float): The score given by the rule.
        reasoning (str): A message that explains why the rule passed or failed.
    """
    rule_name: str
    passed: bool
    weight: float = Field(default=1.0)
    score: float = Field(default=0.0)
    reasoning: str


class Rule(ABC):
    """
    Rule to evaluate a model output on.
    Subclasses must implement `evaluate()` which applies the rule logic to a given input.
    """

    def __init__(self, config: BaseRuleConfig) -> None:
        """
        Initialize the rule with a configuration.
        Args:
            config (BaseRuleConfig): The configuration for the rule
        """
        self.config = config

    @abstractmethod
    def evaluate(self, input: str) -> RuleResultConfig:
        """
        Evaluate the rule against the input

        Args:
            input (str): The input to evaluate against the rule

            Returns:
                RuleResultConfig: The result of the evaluation
        """
