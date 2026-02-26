from abc import abstractmethod
from typing import TypeVar, Any
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

class BaseEvaluator:
    """
    Bind(parse) a dict[str, Any] to a concrete evaluator config

    Args:
        config (dict[str, Any]): The config to be binded

    Returns:
        T | None: A bound config or None if the config was invalid
    """
    @abstractmethod
    def bind(self, config: dict[str, Any]) -> T | None:
        pass

    """
    Evaluate an AI output using a specific config

    Args:
        output (str): The AI output to be evaluated
        config (T): The config which the evaluation is based upon

    Returns:
        bool: Whether if the evaluation passed according to the config or failed
    """
    @abstractmethod
    def evaluate(self, output: str, config: T) -> bool:
        pass


class LengthEvaluatorConfig(BaseModel):
    expected_length: int

class LengthEvaluator(BaseEvaluator):
    def bind(self, config: dict[str, Any]) -> LengthEvaluatorConfig | None:
        try:
            return LengthEvaluatorConfig.model_validate(config)
        except ValidationError:
            return None

    def evaluate(self, output: str, config: LengthEvaluatorConfig) -> bool:
        return len(output) == config.expected_length


class EvaluationRequest(BaseModel):
    output: str
    evaluator_id: str
    config: dict[str, Any]


class EvaluationRegistry:
    """
    A registry system for storing and retrieving evaluators using unique ids

    Attributes:
        registry (dict[str, BaseEvaluator]): Dictionary which maps evaluator ID to an instance of that evaluator 
    """
    registry: dict[str, BaseEvaluator]
 
    def __init__(self):
         self.registry = {}
 
    def get(self, id: str) -> BaseEvaluator | None:
        if self.registry[id] is not None:
            return self.registry[id]
        else:
            return None
 
    def register(self, id: str, evaluator: BaseEvaluator) -> bool:
        self.registry[id] = evaluator
        return True


registry = EvaluationRegistry()
registry.register("length_evaluator", LengthEvaluator())
