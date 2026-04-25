import asyncio
import logging
from uuid import UUID

from celery import Task, shared_task

from app.api.dependencies import get_orchestrator_for_worker
from app.core.models.evaluation_model import EvaluationRequest
from app.core.services.job_status_service import update_evaluation_result, update_evaluation_status
from app.logging.context import task_id_ctx
from app.models import EvaluationStatus

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_evaluation_task(self: Task, job_id: UUID, request_dict: dict) -> None:
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
    request = EvaluationRequest.model_validate(request_dict)

    update_evaluation_status(job_id, status=EvaluationStatus.RUNNING)

    try:
        orchestrator = get_orchestrator_for_worker()
        response = asyncio.run(orchestrator.evaluate(request))
        update_evaluation_result(
            job_id, result=response
        )  # update_evaluation_result automatically sets the status to be completed, maybe this is a bad design decision, but leaving the comment here for confused souls

    except Exception as e:
        logger.error(f"Celery worker with task_id {self.request.id} failed while processing {job_id}: {e}")
        update_evaluation_status(job_id, status=EvaluationStatus.FAILED, error=str(e))

        raise e  # I think it's good to re-raise the error so Celery knows that the task has failed.
