from abc import ABC, abstractmethod
from typing import Any, TypeVar

from pydantic import BaseModel

from app.core.models.evaluation_model import EvaluationResult
from app.utils.time_utils import time_in_ms, time_passed_since_ms

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

    @property
    @abstractmethod
    def default_threshold(self) -> float:
        """
        The default threshold used if none is given to evaluate

        Returns:
            float: The default threshold
        """

    @abstractmethod
    def _evaluate(self, output: str, config: T) -> EvaluationResult:
        """
        Evaluate an AI output using a specific config

        Args:
            output (str): The AI output to be evaluated
            config (T): The config which the evaluation is based upon

        Returns:
            EvaluationResult: Result which contains the normalised score, pass/fail status, execution time, error status and reasoning behind the score
        """

    def evaluate(
        self, output: str, config: T, threshold: float | None = None
    ) -> EvaluationResult:
        if threshold is None:
            threshold = self.default_threshold

        t0 = time_in_ms()
        result = self._evaluate(output, config)
        result.passed = result.normalised_score >= threshold
        result.execution_time = time_passed_since_ms(t0)
        return result
