from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.config.settings import get_settings
from app.core.evaluators.length_evaluator import LengthEvaluator
from app.core.evaluators.llm_judge import LLMJudgeEvaluator
from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.evaluators.rouge_evaluator import RougeEvaluator
from app.core.evaluators.substring_evaluator import SubstringEvaluator
from app.core.models.registry import EvaluationRegistry
from app.core.providers.provider_registry import discover_providers, get_provider


@lru_cache
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

    registry = EvaluationRegistry()
    registry.register(LengthEvaluator().name, LengthEvaluator())
    registry.register(SubstringEvaluator().name, SubstringEvaluator())
    registry.register(RougeEvaluator().name, RougeEvaluator())

    llm = LLMJudgeEvaluator(provider)
    registry.register(llm.name, llm)

    return registry


@lru_cache
def get_orchestrator(reg: Annotated[EvaluationRegistry, Depends(get_registry)]) -> EvaluationOrchestrator:
    return EvaluationOrchestrator(reg)
