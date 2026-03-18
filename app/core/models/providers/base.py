from abc import ABC, abstractmethod
from typing import Annotated

from openai import RateLimitError, BadRequestError, AuthenticationError, PermissionDeniedError, NotFoundError, \
    ConflictError, UnprocessableEntityError, InternalServerError
from pydantic import BaseModel, Field

from app.config.settings import Settings


class LLMException(Exception):
    """
    Maps possible errors received regarding LLM API calls to messages that are more readable.
    """

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
    """
    Represents the user defined criteria contained in the rubric.
    These criteria are what the LLM bases its evaluation upon.

    Attributes:
        criterion_name (str): The name of the criterion. E.g. "Politeness"
        score (int): To what degree the LLM judges the model_output fulfills the criterion on a scale of 1-4.
        reasoning (str): The LLM's reasoning behind the assigned score.
    """

    criterion_name: str
    score: Annotated[int, Field(gt=0, lt=5)]
    reasoning: str


class LLMResponse(BaseModel):
    """
    Represents the response of the LLM judge. Necessary to impose structure on the LLM's response.

    Attributes:
        results (list[CriterionResult]): Contains a list of Criterion results. These describe the results of the evaluation.
    """

    results: list[CriterionResult]


class BaseProvider(ABC):
    """
    Abstract base class for all providers. A provider is for example Azure OpenAI.

    Is responsible for constructing an evaluation prompt, contacting the LLM and constructing and returning a structured response.
    """

    def __init__(self, settings: Settings):
        self.model = settings.llm.model

    @abstractmethod
    def generate_response(self, model_output: str, prompt: str, rubric: list[str]) -> LLMResponse:
        """
        Abstract method to generate an evaluation response.
        """