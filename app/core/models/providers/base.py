from abc import ABC, abstractmethod

from pydantic import BaseModel

class LLMException(Exception):
    pass

class CriterionResult(BaseModel):
    criterion_name: str
    score: int
    reasoning: str


class LLMResponse(BaseModel):
    results: list[CriterionResult]


class BaseProvider(ABC):
    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    def generate_response(
        self, user_prompt: str, system_prompt: str
    ) -> LLMResponse:
        """Idk yet"""


class ProviderNotSupportedException(Exception):
    def __init__(self, msg=None):
        super().__init__(msg or "The system does not support this provider.")

class ProviderMissingEnvVariablesException(Exception):
    def __init__(self, msg=None):
        super().__init__(msg or "Could not find env variables")

class IllegalProviderException(Exception):
    def __init__(self, msg=None):
        super().__init__(msg or "You are not allowed to use this provider")