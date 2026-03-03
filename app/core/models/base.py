from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseEvaluator(ABC):
    """
    Abstract base class for all evaluation strategies.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        A short, unique identifier for this evaluation strategy.

        This will be used for logging, registration, strategy lookup etc. The name should        be lowercase and un        derscore-seperated (e.g. "length_evaluator")

        Returns:
            str: The strategy's unique name.
        """

    @property
    @abstractmethod
    def description(self) -> str:
        """
        An explanation of what this strategy evaluates in plain language.

        Returns:
            str: A description of the strategy.
        """

    @property
    @abstractmethod
    def config_schema(self) -> dict[str, Any]:
        """
        JSON Schema describing the expected config structure for this strategy. The idea is to use this to expose
        config requirements to callers.

        Returns:
            dict: JSON Schema dict (use ``YourConfig.model_json_schema()``).
        """

    @abstractmethod
    def bind(self, config: dict[str, Any]) -> T | None:
        """
        Bind(parse) a dict[str, Any] to a concrete evaluator config

        Args:
            config (dict[str, Any]): The config to be binded

        Returns:
            T | None: A bound config or None if the config was invalid
        """

    @abstractmethod
    def evaluate(self, output: str, config: T) -> bool:
        """
        Evaluate an AI output using a specific config

        Args:
            output (str): The AI output to be evaluated
            config (T): The config which the evaluation is based upon

        Returns:
            bool: Whether if the evaluation passed according to the config or failed
        """
