
# sets base for rules

""" Som argument: tage tekst, rule og specification for rule"""
import string
from abc import abstractmethod
from typing import Literal

from pydantic import BaseModel, Field


class BaseRuleConfig(BaseModel):
    '''Configuration for what a user/evaluator must supply to a rule
        Used for all rules'''
    specification: str #todo: rename, should be some kind of user input for the rule
    weight: float = Field(default=1.0)


class RuleResultConfig(BaseModel):
    '''Result of a single rule check'''
    rule_name: str
    passed: bool
    weight: float = Field(default=1.0)
    score: float = Field(default=0.0)
    reasoning: str


class Rule(BaseModel):
    '''Base class for all rules'''
    rule_name: str


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