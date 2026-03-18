from abc import ABC, abstractmethod

from openai import RateLimitError, BadRequestError, AuthenticationError, PermissionDeniedError, NotFoundError, \
    ConflictError, UnprocessableEntityError, InternalServerError
from pydantic import BaseModel

from app.config.settings import Settings


class LLMException(Exception):
    def __init__(self, original_exception):
        self.original_exception = original_exception
        self.message = self._map_error(original_exception)
        super().__init__(self.message)

    def _map_error(self,e):
        exception_map = {
            BadRequestError: "Something was wrong with the request. Please try rephrasing your message or changing the structure.",
            UnprocessableEntityError: "The LLM couldn’t understand the request. Could you try asking in a different way?",
            AuthenticationError: "Your API key or token is invalid, expired, or revoked. Please check it and try again",
            PermissionDeniedError: "You don’t have access to the requested resource.",
            NotFoundError: "The requested resource could not be found. Please make sure you have the correct credentials.",
            ConflictError: "There was a temporary conflict while processing your request. Please try again.",
            RateLimitError: "You have hit your assigned rate limit. Please wait a moment and try again.",
            InternalServerError: "Something went wrong on our side. Please try again shortly.",
        }
        for error_type, message in exception_map.items():
            if isinstance(e,error_type):
                return message
        return f"Something unexpected happened. Please try again."

class CriterionResult(BaseModel):
    criterion_name: str
    score: int
    reasoning: str


class LLMResponse(BaseModel):
    results: list[CriterionResult]


class BaseProvider(ABC):
    def __init__(self, settings: Settings):
        self.model = settings.llm.model

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