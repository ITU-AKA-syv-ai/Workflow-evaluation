from collections.abc import Generator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.core.evaluators.cosine_evaluator import CosineEvaluator
from app.core.evaluators.llm_judge import LLMJudgeEvaluator
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.evaluators.rouge_evaluator import RougeEvaluator
from app.core.evaluators.rule_based_evaluator import RuleBasedEvaluator
from app.core.models.embeddings import AzureEmbeddingClient
from app.core.models.registry import EvaluationRegistry
from app.core.providers.provider_registry import discover_providers, get_provider
from app.core.repositories.i_result_repository import IResultRepository
from app.core.repositories.sqlalchemy_result_repository import SQLAlchemyResultRepository
from app.db import get_engine


def get_db() -> Generator[Session, None, None]:  # todo: doc string is missing
    """
    Creates a new session bound to the application engine and yields it
    for dependency injection. The session is automatically closed when
    the context exits.

    Yields:
        Session: An active SQLAlchemy session.
    """
    engine = get_engine()
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]
"""Type alias for a FastAPI-injected database session."""


@lru_cache
def get_repository(session: SessionDep) -> IResultRepository:
    """Return a cached result repository backed by the given session.

    Uses `lru_cache` so that repeated calls with the same session
    return the same repository instance rather than creating a new one.

    Args:
        session: The database session provided by `SessionDep`.

    Returns:
        An `IResultRepository` implementation
    """
    return SQLAlchemyResultRepository(session)


def get_registry() -> EvaluationRegistry:
    """
    Build and cache the application's evaluator registry.

    This function loads the current settings, discovers available LLM
    providers, resolves the configured provider, and creates an
    `EvaluationRegistry` containing all available evaluators.

    Returns:
        EvaluationRegistry: A registry containing all available evaluators.

    Raises:
        RuntimeError: If the configured LLM provider has not been registered.
    """
    settings = get_settings()
    discover_providers()

    provider = get_provider(settings.llm.provider)

    if provider is None:
        raise RuntimeError(f"Provider {settings.llm.provider} not registered")

    provider = provider(settings)

    thresholds = settings.threshold
    registry = EvaluationRegistry()

    rouge = RougeEvaluator(thresholds.rouge)
    registry.register(rouge.name, rouge)

    rule_based = RuleBasedEvaluator(thresholds.rule_based)
    registry.register(rule_based.name, rule_based)

    embedding = AzureEmbeddingClient(settings)
    cosine = CosineEvaluator(embedding, thresholds.cosine)
    registry.register(cosine.name, cosine)

    llm = LLMJudgeEvaluator(provider, thresholds.llm_judge)
    registry.register(llm.name, llm)

    return registry


def get_orchestrator(reg: Annotated[EvaluationRegistry, Depends(get_registry)]) -> EvaluationOrchestrator:
    return EvaluationOrchestrator(reg)


def get_orchestrator_for_worker() -> EvaluationOrchestrator:
    """
    Build an orchestrator for use inside Celery worker processes.

    Workers do not have FastAPI dependency injection, so this function constructs an
    orchestrator directly from the cached registry. Reuses get_registry() so that workers
    and the FastAPI app see identical evaluator sets.

    Returns:
        EvaluationOrchestrator: An orchestrator backed by the application's evaluator registry.
    """
    return EvaluationOrchestrator(get_registry())
