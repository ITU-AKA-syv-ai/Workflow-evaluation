import os

from openai import RateLimitError, BadRequestError, AuthenticationError, PermissionDeniedError, NotFoundError, \
    ConflictError, UnprocessableEntityError, InternalServerError
from openai.lib.azure import AzureOpenAI

from app.config.settings import Settings
from app.core.models.providers.base import BaseProvider, LLMResponse, LLMException
from app.core.models.providers.provider_registry import register_provider


@register_provider("azure")
class AzureOpenAIProvider(BaseProvider):
    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self.client = AzureOpenAI(
            api_version=settings.llm.api_version,
            azure_endpoint=settings.llm.api_endpoint,
            api_key=settings.llm.api_key.get_secret_value(),
        )

    def generate_response(self, user_prompt: str, system_prompt: str) -> LLMResponse:
        """
        Constructs the call to the LLM judge, sends it, and receives a response. Also handles errors.

        Args:
            user_prompt (str): The original prompt that the user gave to an LLM.
        	system_prompt (str): The prompt constructed for the LLM-judge, asking it to evaluate.

        Returns:
        	LLMResponse: The response from the LLM judge, containing the rubric scores and reasoning for each.
        """

        try:
            response = self.client.responses.parse(
                model=self.model,
                input=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                text_format=LLMResponse,
            )

            if response and response.output_parsed:
                return response.output_parsed

            raise ValueError("LLM failed to return a valid structured response.")
        except BadRequestError:
            raise LLMException("Something was wrong with the request. Please try rephrasing your message or changing the structure.")

        except UnprocessableEntityError:
            raise LLMException("The LLM couldn’t understand the request. Could you try asking in a different way?")

        except AuthenticationError:
            raise LLMException("Your API key or token is invalid, expired, or revoked. Please check it and try again")

        except PermissionDeniedError:
            raise LLMException("You don’t have access to the requested resource.")

        except NotFoundError:
            raise LLMException("The requested resource could not be found. Please make sure you have the correct credentials.")

        except ConflictError:
            raise LLMException("There was a temporary conflict while processing your request. Please try again.")

        except RateLimitError:
            raise LLMException("You have hit your assigned rate limit. Please wait a moment and try again.")

        except InternalServerError:
            raise LLMException("Something went wrong on our side. Please try again shortly.")

        except Exception:
            raise LLMException("Something unexpected happened. Please try again.")