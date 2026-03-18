from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter
from fastapi.params import Depends

from app.config.settings import get_settings
from app.core.models.evaluation_model import (
    EvaluationRequest,
    EvaluationResponse,
    EvaluatorInfo,
)
from app.core.models.length_evaluator import LengthEvaluator
from app.core.models.llm_judge import LLMJudgeEvaluator
from app.core.models.providers.provider_registry import discover_providers, get_provider
from app.core.models.registry import EvaluationRegistry
from app.core.models.substring_evaluator import SubstringEvaluator
from app.core.services.evaluation_service import evaluate, get_evaluators

settings = get_settings()
router = APIRouter()

@lru_cache
def get_registry() -> EvaluationRegistry:
    discover_providers()

    provider = get_provider(settings.llm.provider)

    if provider is None:
        # Todo: Change to better exception
        raise RuntimeError(f"Provider {settings.llm.provider} not registered")

    provider = provider(settings)

    registry = EvaluationRegistry()
    registry.register(LengthEvaluator().name, LengthEvaluator())
    registry.register(SubstringEvaluator().name, SubstringEvaluator())

    llm = LLMJudgeEvaluator(provider)
    registry.register(llm.name, llm)

    return registry



@router.post("/evaluate")
def evaluate_endpoint(requests: list[EvaluationRequest], registry: Annotated[EvaluationRegistry, Depends(get_registry)]) -> list[EvaluationResponse]:
    """
    Evaluate one or more evaluation requests using their respective evaluator configurations.

    Args:
        req (list[EvaluationRequest]):
            A list of evaluation requests. Each request contains
            the input data and evaluator configuration to apply.

    Returns:
        list[EvaluationResponse]:
            A list of evaluation results, one for each request,
            containing the outcome of the applied evaluator configuration.
    """
    result = []
    for request in requests:
        result.append(evaluate(request, registry))

    return result


@router.get("/evaluators", response_model=list[EvaluatorInfo])
def evaluators(registry: Annotated[EvaluationRegistry, Depends(get_registry)]) -> list[EvaluatorInfo]:
    """
    Retrieve all available evaluators from the registry.

    Returns:
        list[EvaluatorInfo]: A list of evaluators, each including the evaluator ID,
        description, and expected configuration schema.
    """
    return get_evaluators(registry)
