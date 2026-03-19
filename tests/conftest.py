from collections.abc import Callable, Generator

import pytest
from starlette.testclient import TestClient

from app.api.evaluate import get_registry
from app.core.models.providers.base import (
    BaseProvider,
    CriterionResult,
    LLMExceptionError,
    LLMResponse,
)
from app.core.models.registry import EvaluationRegistry
from app.main import app as fastapi_app


class MockProvider(BaseProvider):
    def __init__(
        self, response: LLMResponse | None = None, default_score: int = 3
    ) -> None:
        self.model = "dummy"

        self.response = response
        self.default_score = default_score

    def generate_response(
        self, model_output: str, prompt: str, rubric: list[str]
    ) -> LLMResponse:
        if self.response:
            return self.response

        return LLMResponse(
            results=[
                CriterionResult(
                    criterion_name=criterion,
                    score=self.default_score,
                    reasoning=f"Mock reasoning for {criterion}",
                )
                for criterion in rubric
            ]
        )


class ErrorProvider(BaseProvider):
    def __init__(self, exception: Exception) -> None:
        self.model = "mock-model"
        self.exception = exception

    def generate_response(
        self, model_output: str, prompt: str, rubric: list[str]
    ) -> LLMResponse:
        raise LLMExceptionError(self.exception)


@pytest.fixture(scope="function")
def mock_provider() -> MockProvider:
    return MockProvider()


@pytest.fixture(scope="function")
def error_provider() -> Callable[[Exception], ErrorProvider]:
    """Factory fixture — call with the exception you want raised."""

    def _make(exception: Exception) -> ErrorProvider:
        return ErrorProvider(exception)

    return _make


@pytest.fixture(scope="function")
def registry() -> Generator:
    yield EvaluationRegistry()


@pytest.fixture(scope="function")
def client_with_registry(
    registry: EvaluationRegistry,
) -> Generator[TestClient, None, None]:
    def override_get_registry() -> Generator[EvaluationRegistry]:
        yield registry

    fastapi_app.dependency_overrides[get_registry] = override_get_registry
    with TestClient(fastapi_app) as c:
        yield c

    fastapi_app.dependency_overrides.clear()
