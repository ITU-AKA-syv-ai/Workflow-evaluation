from collections.abc import Callable, Generator
from typing import Any

import pytest
from pydantic import BaseModel
from starlette.testclient import TestClient

from app.api.evaluate import get_registry
from app.core.evaluators.base import BaseEvaluator
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.evaluation_model import EvaluationRequest, EvaluationResult, EvaluatorConfig
from app.core.models.registry import EvaluationRegistry
from app.core.providers.base import (
    BaseProvider,
    CriterionResult,
    LLMExceptionError,
    LLMResponse,
)
from app.main import app as fastapi_app


class MockEvaluatorConfig(BaseModel):
    pass


default_config = MockEvaluatorConfig()


class MockEvaluator(BaseEvaluator):
    """
    Used for mocking an evaluator.

    This can be setup to return a specific score, config or raise an exception.

    Attributes:
        name_str (str): The evaluator ID.
        description_str (str): A human readable description of the evaluator.
        config (BaseModel | None): The config to return when validate_config() is called. Can also return none. Defaults to an empty config.
        evaluation (EvaluationResult): The evaluation result this mock evaluator will return, assuming this evaluator isn't configured to raise an exception.
        threshold (float): The default threshold used to determine if this evaluator passed or not based on the output score.
        exception (Exception | None): The exception to raise when evaluate() is called. Note that evaluate catches exceptions and will gracefully return an EvaluationResult with the error inside.
    """

    name_str: str
    description_str: str
    config: BaseModel | None
    evaluation: EvaluationResult
    threshold: float
    exception: Exception | None

    def __init__(
        self,
        score: float = 0.8,
        config: BaseModel | None = default_config,
        raise_on_evaluate: Exception | None = None,
        name: str = "mock_evaluator",
        description: str = "Mock evaluator used for testing",
        threshold: float = 1,
    ) -> None:
        """
        Construct a Mock Evaluator

        Args:
            score (float): The normalised score which this mock evaluator should always output.
            config (BaseModel | None): The config this mock evaluator should always return when asked to validate a config. Can be set to None if the desired behaviour is that validate_config() always fails.
            raise_on_evaluate (Exception | None): If the desired behaviour is an error whenever evaluate() is called, an exception can be supplied. Otherwise None.
            name (str): The evaluator ID used by the registry to identify the evaluator.
            description (str): The textual description of the evaluator.
            threshold (float): The required score in order for this evaluator to be considered passing.
        """
        self.name_str = name
        self.description_str = description
        self.config = config
        self.evaluation = EvaluationResult(
            evaluator_id=name, reasoning="This is a mock evaluator", normalised_score=score
        )
        self.threshold = threshold
        self.raise_on_evaluate = raise_on_evaluate

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
    def config_schema(self) -> dict[str, Any]:
        return {"mock": "Mock evaluator doesn't have a config schema"}

    def validate_config(self, config: dict[str, Any]) -> BaseModel | None:
        """
        Arguments are ignored, always returns the hardcoded config.
        """
        return self.config

    async def _evaluate(self, output: str, config: BaseModel) -> EvaluationResult:
        """
        If self.raise_on_evaluate is set to an exception, this will always raise an exception.
        Note that _evaluate() is typically called form evaluate() which handles exceptions gracefully.
        If self.raise_on_evaluate is None, this will return self.evaluation.

        Args:
            output (str): LLM/Model output, this is ignored since this is a mock.
            config (BaseModel): Configuration for the evaluator, this is ignored since this is a mock.

        Returns:
            EvaluationResult: The hardcoded result or a result with an error if `self.raise_on_evaluate` contains an exception.
        """
        if self.raise_on_evaluate is not None:
            raise self.raise_on_evaluate
        return self.evaluation


def create_evaluation_request(configs: list[EvaluatorConfig], model_output: str = "Lorem Ipsum") -> EvaluationRequest:
    """
    Creates an EvaluationRequest with model_output being defaulted to "Lorem Ipsum".

    Args:
        configs (list[EvaluatorConfig]): The list of configs to store in the request.
        model_output (str): The string to use as model output in the request. Defauls to "Lorem Ipsum".
    Returns:
        EvaluationRequest: The request specified by the given arguments.
    """
    return EvaluationRequest(model_output=model_output, configs=configs)


default_evaluation_config = {}


def create_evaluation_config(
    evaluator_id: str, config: dict[str, Any] = default_evaluation_config, weight: float = 1.0
) -> EvaluatorConfig:
    """
    Creates an EvaluatorConfig. Defaults config to be ampty and the weight to 1.

    Args:
        evaluator_id (str): The evaluator ID which the registry uses the identify the evaluator.
        config (dict[str, Any]): The evaluator config to employ, defaults to an empty config.
        weight (float): The weight used when this evaluator's score is aggregated into a weighted sum. Defaults to 1.
    Returns:
        EvaluatorConfig: The econfig specified the given arguments.
    """
    return EvaluatorConfig(evaluator_id=evaluator_id, weight=weight, config=config)


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
    """
    Provides a Mock LLM provider.
    """
    return MockProvider()


@pytest.fixture(scope="function")
def error_provider() -> Callable[[Exception], ErrorProvider]:
    """Factory fixture for the error providers. It should be called with the exception that is wanted to be raised."""

    def _make(exception: Exception) -> ErrorProvider:
        return ErrorProvider(exception)

    return _make


@pytest.fixture(scope="function")
def registry() -> Generator:
    """
    Provides an empty evaluator registry.
    """
    yield EvaluationRegistry()


@pytest.fixture(scope="function")
def mock_evaluator_with_registry() -> Generator:
    """
    Provides an evaluator registry with the default mock evaluator.
    """
    registry = EvaluationRegistry()
    evaluator = MockEvaluator()
    registry.register(evaluator.name, evaluator)
    yield registry


@pytest.fixture(scope="function")
def client_with_registry(
    registry: EvaluationRegistry,
) -> Generator[TestClient, None, None]:
    """
    Provides a TestClient for testing the endpoints.
    An empty evaluator registry is included.
    """

    def override_get_registry() -> Generator[EvaluationRegistry]:
        yield registry

    fastapi_app.dependency_overrides[get_registry] = override_get_registry
    with TestClient(fastapi_app) as c:
        yield c

    fastapi_app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def orchestrator(registry: EvaluationRegistry) -> EvaluationOrchestrator:
    """
    Provides orchestartor with an empty evaluation registry
    """
    return EvaluationOrchestrator(registry)
