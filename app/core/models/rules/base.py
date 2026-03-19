
from abc import ABC, abstractmethod
from typing import Literal

from pydantic import BaseModel, Field


class BaseRuleConfig(BaseModel):
    '''Configuration for what a user/evaluator must supply to a rule
        Used for all rules'''
    name: Literal["regex", "format", "keyword"]
    weight: float = Field(default=1.0)


class RuleResultConfig(BaseModel):
    '''Result of a single rule check'''
    rule_name: str
    passed: bool
    weight: float = Field(default=1.0)
    score: float = Field(default=0.0)
    reasoning: str


class Rule(ABC):
    '''Base class for all rules'''
    def __init__(self, config: BaseRuleConfig) -> None:
        self.config = config


    #todo: name & description as in evaluators/base.py

    @abstractmethod
    def evaluate(self, input: str) -> RuleResultConfig:
        """
        Evaluate the rule against the input

        Args:
            input (str): The input to evaluate against the rule

            Returns:
        """
       #Something for base setup.