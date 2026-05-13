import asyncio
from collections.abc import Callable, Generator
from datetime import UTC, date, datetime, timedelta
from typing import Any, Final
from uuid import UUID, uuid4

import pytest
from pydantic import BaseModel, SecretStr
from pydantic_settings import SettingsConfigDict
from starlette.testclient import TestClient

from app.api.dependencies import (
    get_job_state_lookup,
    get_persistence_service,
    get_result_repository,
)
from app.api.evaluate import get_registry
from app.config.settings import (
    DBConfig,
    EmbeddingConfig,
    JTWConfig,
    LLMConfig,
    LogLevelConfig,
    RedisConfig,
    Settings,
    SimilarityConfig,
    ThresholdConfig,
    get_settings,
)
from app.core.evaluators.base import BaseEvaluator
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluationResult,
    EvaluatorConfig,
)
from app.core.models.registry import EvaluationRegistry
from app.core.models.result_query import ResultQuery
from app.core.providers.base import (
    BaseProvider,
    Criterion,
    CriterionResult,
    LLMExceptionError,
    LLMResponse,
)
from app.core.repositories.i_result_repository import IResultRepository
from app.exceptions import ResultNotFoundError, ResultPersistenceError
from app.factory import create_app
from app.models import EvaluationStatus


def _fake_make_filter(
    start_date: date | None = None,
    end_date: date | None = None,
    min_score: float | None = None,
    max_score: float | None = None,
    evaluator_ids: list[str] | None = None,
    tags: list[str] | None = None,
    model_name: str | None = None,
    model_version: str | None = None,
) -> list[Callable[[AggregatedResultEntity], bool]]:

    predicates: list[Callable[[AggregatedResultEntity], bool]] = []
    if start_date is not None:
        # Converts date to datetime, setting time to midnight (start of day)
        start_dt = datetime.combine(start_date, datetime.min.time())
        predicates.append(lambda r, dt=start_dt: r.created_at >= dt)
    if end_date is not None:
        # Converts date to datetime, setting time to midnight (start of next day)
        end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())
        predicates.append(lambda r, dt=end_dt: r.created_at <= dt)
    if min_score is not None:
        predicates.append(lambda r, s=min_score: r.weighted_score is not None and r.weighted_score >= s)
    if max_score is not None:
        predicates.append(lambda r, s=max_score: r.weighted_score is not None and r.weighted_score <= s)
    if evaluator_ids:
        ids = set(evaluator_ids)
        predicates.append(lambda r, ids=ids: any(ev in ids for ev in getattr(r, "evaluator_ids", [])))
    if tags:
        required_tags = set(tags)
        predicates.append(lambda r, required_tags=required_tags: required_tags.issubset(set(r.tags)))
    if model_name is not None:
        predicates.append(lambda r, model_name=model_name: r.model_name == model_name)
    if model_version is not None:
        predicates.append(lambda r, model_version=model_version: r.model_version == model_version)
    return predicates


class FakeResultRepository(IResultRepository):
    def __init__(self) -> None:
        self.results: dict[UUID, AggregatedResultEntity] = {}

        # maps result_id -> list of evaluator_ids
        self.evaluations: dict[UUID, list[str]] = {}

    def insert(self, aggregated_result: AggregatedResultEntity) -> UUID:
        result_id = uuid4()
        aggregated_result.id = result_id
        aggregated_result.created_at = datetime.now(UTC)
        self.results[result_id] = aggregated_result
        self.evaluations[result_id] = getattr(aggregated_result, "evaluator_ids", [])
        return result_id

    def delete(self, result_id: UUID) -> None:
        self.results.pop(result_id, None)

    def get_result_by_id(self, result_id: UUID) -> AggregatedResultEntity:
        result = self.results.get(result_id)
        if result is None:
            raise ResultNotFoundError(result_id)
        return result

    def get_recent_results(self, limit: int = 5, offset: int = 0) -> list[AggregatedResultEntity]:
        sorted_results = sorted(self.results.values(), key=lambda r: (r.created_at, r.id), reverse=True)
        return sorted_results[offset : offset + limit]

    def update(self, result_id: UUID, result: EvaluationResponse) -> None:
        stored = self.results.get(result_id)
        if stored is None:
            raise ResultNotFoundError(result_id)

        stored.result = result

    def get_results(self, query: ResultQuery) -> list[AggregatedResultEntity]:

        # build filters
        predicates = _fake_make_filter(
            query.start_date,
            query.end_date,
            query.min_score,
            query.max_score,
            query.evaluator_ids,
            query.tags,
            query.model_name,
            query.model_version,
        )
        # build query
        filtered = [r for r in self.results.values() if all(p(r) for p in predicates)]
        # build sort
        reverse = query.sorting_direction == "desc"

        if query.sorting == "date":
            filtered.sort(key=lambda r: (r.created_at, r.id), reverse=reverse)
        elif query.sorting == "score":
            filtered.sort(key=lambda r: r.weighted_score or 0, reverse=reverse)

        # build pagination and return results
        return filtered[query.offset : query.offset + query.limit]


class EveryNthInsertionFailsRepository(FakeResultRepository):
    """
    Fails every Nth call to insert(), succeeds otherwise.

    n=1 means every insert fails.
    n=2 means every other insert fails (calls 2, 4, 6, ...).
    n=3 means every third insert fails (calls 3, 6, 9, ...).
    """

    def __init__(self, n: int = 1) -> None:
        if n < 1:
            raise ValueError("n must be >= 1")
        super().__init__()
        self.n = n
        self.call_count = 0

    def insert(self, aggregated_result: AggregatedResultEntity) -> UUID:
        self.call_count += 1
        if self.call_count % self.n == 0:
            raise ResultPersistenceError()
        return super().insert(aggregated_result)


class FakePersistenceService:
    """In-memory stand-in for ``ResultPersistenceService``.

    Writes into a shared ``FakeResultRepository`` so reads via ``get_result_repository``
    and writes via ``get_persistence_service`` see the same storage. Tests can keep
    asserting against ``fake_repo.results`` exactly as before.
    """

    def __init__(self, repo: FakeResultRepository) -> None:
        self.repo = repo

    def persist_completed(self, entity: AggregatedResultEntity) -> UUID:
        return self.repo.insert(entity)


class EveryNthPersistFails(FakePersistenceService):
    """Persistence service that fails every Nth call to persist_completed().

    n=1 means every call fails.
    n=2 means every other call fails (calls 2, 4, 6, ...).
    """

    def __init__(self, repo: FakeResultRepository, n: int = 1) -> None:
        if n < 1:
            raise ValueError("n must be >= 1")
        super().__init__(repo)
        self.n = n
        self.call_count = 0

    def persist_completed(self, entity: AggregatedResultEntity) -> UUID:
        self.call_count += 1
        if self.call_count % self.n == 0:
            raise ResultPersistenceError()
        return super().persist_completed(entity)


@pytest.fixture(scope="function")
def fake_repo() -> FakeResultRepository:
    return FakeResultRepository()


@pytest.fixture(scope="function")
def failing_repo() -> EveryNthInsertionFailsRepository:
    """Repository where every insert() fails."""
    return EveryNthInsertionFailsRepository(n=1)


@pytest.fixture(scope="function")
def occasional_fail_fake_repo() -> EveryNthInsertionFailsRepository:
    """Repository where every other insert() fails (calls 2, 4, 6, ...)."""
    return EveryNthInsertionFailsRepository(n=2)


@pytest.fixture(scope="function")
def fake_persistence_service(fake_repo: FakeResultRepository) -> FakePersistenceService:
    """A persistence service backed by the same fake_repo used for reads."""
    return FakePersistenceService(fake_repo)


@pytest.fixture(scope="function")
def failing_persistence_service(
    failing_repo: EveryNthInsertionFailsRepository,
) -> EveryNthPersistFails:
    """Persistence service whose every persist_completed() call fails."""
    return EveryNthPersistFails(failing_repo, n=1)


@pytest.fixture(scope="function")
def occasional_fail_persistence_service(
    occasional_fail_fake_repo: EveryNthInsertionFailsRepository,
) -> EveryNthPersistFails:
    """Persistence service that fails every other persist_completed() call."""
    return EveryNthPersistFails(occasional_fail_fake_repo, n=2)


class MockEvaluatorConfig(BaseModel):
    pass


DEFAULT_CONFIG: Final[MockEvaluatorConfig] = MockEvaluatorConfig()


class MockEvaluator(BaseEvaluator):
    """
    Used for mocking an evaluator.

    This can be setup to return a specific score, config or raise an exception.

    Attributes:
        name_str (str): The evaluator ID.
        description_str (str): A human readable description of the evaluator.
        config (Base _Model | None): The config to return when validate_config(
        ) is called. Can also return none. Defaults to an empty config.
        evaluation (EvaluationResult): The evaluation result this mock evaluator will return, assuming this evaluator isn't configured to raise an exception.
        threshold (float): The default threshold used to determine if this evaluator passed or not based on the output score.
        exception (Exception | None): The exception to raise when evaluate() is called. Note that evaluate catches exceptions and will gracefully return an EvaluationResult with the error inside.
    """

    name_str: str
    description_str: str
    config: BaseModel | None
    evaluation: EvaluationResult
    threshold: float
    delay: float
    timeout: float
    raise_on_evaluate: Exception | None

    def __init__(
        self,
        score: float = 0.8,
        config: BaseModel | None = DEFAULT_CONFIG,
        raise_on_evaluate: Exception | None = None,
        name: str = "mock_evaluator",
        description: str = "Mock evaluator used for testing",
        threshold: float = 1,
        timeout: float = 30,
        delay: float = 0,
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
        self.delay = delay
        self.timeout = timeout

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
        if self.delay > 0:
            await asyncio.sleep(self.delay)
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


def create_evaluation_config(
    evaluator_id: str, config: dict[str, Any] | None = None, weight: float = 1.0
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
    if config is None:
        config = {}
    return EvaluatorConfig(evaluator_id=evaluator_id, weight=weight, config=config)


class MockProvider(BaseProvider):
    def __init__(self, response: LLMResponse | None = None, default_score: int = 3) -> None:
        self.model = "dummy"

        self.response = response
        self.default_score = default_score

    async def check_health(self) -> None:
        """
        Mock health check for the provider.

        Returns:
            None: Always succeeds for tests that do not focus on provider readiness.
        """
        return

    # This is never called, since the idea of this class is to mock the high level call that the judge calls
    async def _generate_response(self, model_output: str, prompt: str, rubric: list[Criterion]) -> None:
        return None

    async def generate_response(self, model_output: str, prompt: str, rubric: list[Criterion]) -> LLMResponse:
        if self.response:
            return self.response

        return LLMResponse(
            results=[
                CriterionResult(
                    criterion_id=criterion.id,
                    score=self.default_score,
                    reasoning=f"Mock reasoning for {criterion.id}",
                )
                for criterion in rubric
            ]
        )


class ErrorProvider(BaseProvider):
    def __init__(self, exception: Exception) -> None:
        self.model = "mock-model"
        self.exception = exception

    async def check_health(self) -> None:
        """
        Mock health check for the provider.

        Returns:
            None: Always succeeds for tests that focus on provider response errors rather than readiness.
        """
        return

    # This is never called, since the idea of this class is to mock the high level call that the judge calls
    async def _generate_response(self, model_output: str, prompt: str, rubric: list[Criterion]) -> None:
        return None

    async def generate_response(self, model_output: str, prompt: str, rubric: list[Criterion]) -> LLMResponse:
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
def registry() -> EvaluationRegistry:
    """
    Provides an empty evaluator registry.
    """
    return EvaluationRegistry(settings=TestSettings())


@pytest.fixture(scope="function")
def mock_evaluator_with_registry() -> EvaluationRegistry:
    """
    Provides an evaluator registry with the default mock evaluator.
    """
    registry = EvaluationRegistry(settings=TestSettings())
    evaluator = MockEvaluator()
    registry.register(evaluator.name, evaluator)
    return registry


class TestSettings(Settings):
    __test__ = False
    model_config = SettingsConfigDict(
        env_file=None,
        env_prefix="",
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )

    def __init__(self) -> None:
        super().__init__(
            environment="dev",
            llm=LLMConfig(
                provider="test",
                api_key=SecretStr("test"),
                api_endpoint="http://test.com",
                model="test-model",
                api_version="idk",
            ),
            embedding=EmbeddingConfig(
                api_key=SecretStr("test"),
                api_endpoint="http://test-embedding",
                model="test-model",
                api_version="v1",
            ),
            similarity=SimilarityConfig(
                max_length=128,
            ),
            threshold=ThresholdConfig(
                rouge=0.5,
                cosine=0.7,
                llm_judge=1.0,
                rule_based=1.0,
            ),
            log=LogLevelConfig(level="INFO"),
            db=DBConfig(
                driver="sqlite",
                host="",
                port=0,
                database=":memory:",
                username="",
                password=SecretStr(""),
            ),
            redis=RedisConfig(host="yoo"),
            jwt=JTWConfig(
                issuer="test",
                audience="test",
                secret="testing",
                algorithm="HS256",
                jwks_url="",
            ),
        )


def _build_test_client(
    registry: EvaluationRegistry,
    repo: IResultRepository,
    persistence: FakePersistenceService,
) -> Generator[TestClient, None, None]:
    """
    Build a TestClient with test-specific settings, registry, repository,
    persistence service, and job-state lookup wired in as FastAPI dependency
    overrides.

    Notes:
        - ``app.dependency_overrides[get_settings]`` only affects code paths that
          consume ``get_settings`` via ``Depends(...)``. Direct callers (factory
          lifespan, ``get_engine``, the Celery factory) fall back to the real
          ``get_settings``, which works because pytest-env (in ``pyproject.toml``)
          populates placeholder values before any imports.
        - Both ``get_result_repository`` and ``get_persistence_service`` are
          overridden. The sync ``POST /evaluations`` writes through the service;
          read endpoints and the async ``POST /async/evaluations`` read/write
          through the repo. Tests share a single ``fake_repo`` instance behind
          both overrides so writes through one are visible to reads through the
          other.
        - ``get_job_state_lookup`` is overridden so handlers don't reach into
          Celery's real result backend during tests.
    """
    test_settings = TestSettings()

    app = create_app()
    app.dependency_overrides[get_settings] = lambda: test_settings
    app.dependency_overrides[get_registry] = lambda: registry
    app.dependency_overrides[get_result_repository] = lambda: repo
    app.dependency_overrides[get_persistence_service] = lambda: persistence
    app.dependency_overrides[get_job_state_lookup] = lambda: lambda _id: EvaluationStatus.PENDING
    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client_with_registry(
    registry: EvaluationRegistry,
    fake_repo: FakeResultRepository,
    fake_persistence_service: FakePersistenceService,
) -> Generator[TestClient, None, None]:
    """
    Provides a TestClient for testing the endpoints.
    An empty evaluator registry is included.
    """
    yield from _build_test_client(registry, fake_repo, fake_persistence_service)


@pytest.fixture(scope="function")
def client_with_failing_repo(
    registry: EvaluationRegistry,
    failing_repo: EveryNthInsertionFailsRepository,
    failing_persistence_service: EveryNthPersistFails,
) -> Generator[TestClient, None, None]:
    """
    Provides a TestClient whose repository and persistence service both fail on
    every write. Async-endpoint tests exercise the failing repo directly; sync
    tests exercise the failing service. An empty evaluator registry is included.
    """
    yield from _build_test_client(registry, failing_repo, failing_persistence_service)


@pytest.fixture(scope="function")
def client_with_occasional_failing_repo(
    registry: EvaluationRegistry,
    occasional_fail_fake_repo: EveryNthInsertionFailsRepository,
    occasional_fail_persistence_service: EveryNthPersistFails,
) -> Generator[TestClient, None, None]:
    """
    Provides a TestClient whose repository and persistence service fail every
    other write (calls 2, 4, 6, ...). Useful for testing partial-success
    behavior in batch endpoints.
    """
    yield from _build_test_client(registry, occasional_fail_fake_repo, occasional_fail_persistence_service)


@pytest.fixture(scope="function")
def orchestrator(registry: EvaluationRegistry) -> EvaluationOrchestrator:
    """
    Provides orchestartor with an empty evaluation registry
    """
    return EvaluationOrchestrator(registry)
