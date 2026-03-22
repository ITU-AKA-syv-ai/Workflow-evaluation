from typing import Annotated

from fastapi import Depends

from app.core.evaluators.orchestrator import EvaluationOrchestrator
from app.core.models.registry import EvaluationRegistry, registry

_orchestrator: EvaluationOrchestrator | None = None


def get_registry() -> EvaluationRegistry:
    return registry


def get_orchestrator(
    reg: Annotated[EvaluationRegistry, Depends(get_registry)],
) -> EvaluationOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = EvaluationOrchestrator(reg)
    return _orchestrator