import asyncio
import logging
from uuid import UUID

from celery import Task

from app.api.dependencies import get_orchestrator_for_worker
from app.core.models.evaluation_model import EvaluationRequest
from app.core.services.job_status_service import update_evaluation_result
from app.logging.context import task_id_ctx
from app.workers.celery_app import app

logger = logging.getLogger(__name__)


@app.task(bind=True)
def run_evaluation_task(self: Task, job_id: UUID, request_dict: dict) -> None:
    """
    Execute an evaluation request and persist the result.

    Task lifecycle (PENDING -> STARTED -> SUCCESS/FAILURE) is handled entirely by Celery's
    result backend (see ``celery_app.py``). On success, the evaluation response is written
    to the ``results`` table via ``update_evaluation_result``. On failure, the exception is
    re-raised so Celery records FAILURE plus the traceback in ``celery_taskmeta``.

    Args:
        self: The Celery Task instance (injected by ``bind=True``).
        job_id: The UUID of the pre-existing ``Result`` row to update with the response.
        request_dict: The EvaluationRequest serialized via ``model_dump()``.
    """
    task_id_ctx.set(self.request.id)
    request = EvaluationRequest.model_validate(request_dict)

    try:
        orchestrator = get_orchestrator_for_worker()
        response = asyncio.run(orchestrator.evaluate(request))
        update_evaluation_result(job_id, result=response)

    except Exception as e:
        logger.error(f"Celery worker with task_id {self.request.id} failed while processing {job_id}: {e}")
        # Re-raise so Celery records FAILURE in the result backend along with the
        # exception type, message, and traceback (result_extended=True).
        raise
