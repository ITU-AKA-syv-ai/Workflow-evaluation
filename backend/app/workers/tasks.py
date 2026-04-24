import asyncio
import logging

from celery import Task
from sqlalchemy.orm import Session

from app.api.dependencies import get_orchestrator_for_worker
from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import EvaluationRequest
from app.core.repositories.sqlalchemy_result_repository import SQLAlchemyResultRepository
from app.db import get_engine, get_sessionmaker
from app.logging.context import task_id_ctx
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="run_evaluation", bind=True)
def run_evaluation_task(self: Task, request_dict: dict) -> str:
    """
    Execute an evaluation request and persist the result.

    On success, persists the evaluation result as an AggregatedResultEntity and returns its
    ID. Celery stores this return value in the result backend, where it can later be
    retrieved via AsyncResult(task_id).result. On failure or timeout, the exception
    propagates and Celery records the task as FAILURE.

    Args:
        self: Task
        request_dict (dict): The EvaluationRequest serialized via model_dump().

    Returns:
        str: The UUID of the persisted AggregatedResultEntity, as a string so that Celery's
            JSON-serialized result backend can store it.

    """
    task_id_ctx.set(self.request.id)

    req = EvaluationRequest.model_validate(request_dict)
    orchestrator = get_orchestrator_for_worker()

    response = asyncio.run(orchestrator.evaluate(req))

    session_local = get_sessionmaker()

    with session_local.begin() as session:
        result_repo = SQLAlchemyResultRepository(session)
        entity = AggregatedResultEntity(request=req, result=response)
        result_id = result_repo.insert(entity)

    return str(result_id)
