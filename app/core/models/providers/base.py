from abc import ABC, abstractmethod

from pydantic import BaseModel


class CriterionResult(BaseModel):
    criterion_name: str
    score: int
    reasoning: str


class LLMResponse(BaseModel):
    results: list[CriterionResult]


class BaseProvider(ABC):
    @abstractmethod
    def generate_response(
        self, model: str, user_prompt: str, system_prompt: str
    ) -> LLMResponse:
        """Idk yet"""
