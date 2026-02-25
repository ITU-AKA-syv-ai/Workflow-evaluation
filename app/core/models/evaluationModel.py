from abc import abstractmethod
from typing import TypeVar, Any
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)

class BaseEvaluator:
    @abstractmethod
    def bind(self, config: dict[str, Any]) -> T | None:
        pass

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


# class EvaluationRegistry:
#    registry: dict[str, BaseEvaluator]
#
#    def get(self, id: str) -> BaseEvaluator | None:
#        if self.registry[id] is not None:
#            return self.registry[id]
#        else:
#            return None
#
#    def register(self, id: str, evaluator: BaseEvaluator) -> bool:
#        self.registry[id] = evaluator
#        return True
#
#
# registry = EvaluationRegistry()
# registry.register("length_evaluator", LengthEvaluator())
