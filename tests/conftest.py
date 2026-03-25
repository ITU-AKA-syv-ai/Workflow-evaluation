import typing
from collections.abc import Callable, Generator

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from app.api.evaluate import get_registry
from app.core.evaluators.base import BaseEvaluator
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.evaluation_model import EvaluationResult
from app.core.models.registry import EvaluationRegistry
from app.core.providers.base import (
    BaseProvider,
    CriterionResult,
    LLMExceptionError,
    LLMResponse,
)
from app.main import app as fastapi_app


class MockEvaluatorConfig(BaseModel):
    ...


EvaluationFunction = typing.TypeVar("EvaluationFunction", bound=Callable[[str, BaseModel], EvaluationResult])


class MockEvaluator(BaseEvaluator):
    name_str: str
    description_str: str
    config_type: BaseModel
    evaluation: EvaluationResult | EvaluationFunction
    threshold: float

    def __init__(self,
                 evaluation: EvaluationResult | EvaluationFunction,
                 name: str = "mock_evaluator",
                 description: str = "Mock evaluator used for testing",
                 config_type: BaseModel = MockEvaluatorConfig,
                 threshold: float = 1
                ) -> None:
        self.name_str = name
        self.description_str = description
        self.config_type = config_type
        self.evaluation = evaluation
        self.threshold = threshold

    @property
    def name(self) -> str:
        return self.name_str

    @property
    def description(self) -> str:
        return self.description_str

    @property
    def default_threshold(self) -> float:
        return self.threshold

    @property
    def config_schema(self) -> dict[str, typing.Any]:
        return self.config_type.model_json_schema()

    def validate_config(self, config: dict[str, typing.Any]) -> BaseModel | None:
        return self.config_type.model_validate(config)

    async def _evaluate(self, output: str, config: BaseModel) -> EvaluationResult:
        if type(self.evaluation) is EvaluationResult:
            return self.evaluation
        return self.evaluation(output, config)


class MockProvider(BaseProvider):
    def __init__(self, response: LLMResponse | None = None, default_score: int = 3) -> None:
        self.model = "dummy"

        self.response = response
        self.default_score = default_score

    # This is never called, since the idea of this class is to mock the high level call that the judge calls
    async def _generate_response(self, model_output: str, prompt: str, rubric: list[str]) -> None:
        return None

    async def generate_response(self, model_output: str, prompt: str, rubric: list[str]) -> LLMResponse:
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

    # This is never called, since the idea of this class is to mock the high level call that the judge calls
    async def _generate_response(self, model_output: str, prompt: str, rubric: list[str]) -> None:
        return None

    async def generate_response(self, model_output: str, prompt: str, rubric: list[str]) -> LLMResponse:
        raise LLMExceptionError(self.exception)


@pytest.fixture(scope="function")
def mock_provider() -> MockProvider:
    return MockProvider()


@pytest.fixture(scope="function")
def error_provider() -> Callable[[Exception], ErrorProvider]:
    """Factory fixture for the error providers. It should be called with the exception that is wanted to be raised."""

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


@pytest.fixture(scope="function")
def orchestrator(registry: EvaluationRegistry) -> EvaluationOrchestrator:
    return EvaluationOrchestrator(registry)
