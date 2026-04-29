from uuid import UUID

from celery.result import AsyncResult

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import EvaluationResponse
from app.core.repositories.sqlalchemy_result_repository import SQLAlchemyResultRepository
from app.db import get_sessionmaker
from app.exceptions import ResultNotFoundError
from app.models import EvaluationStatus
from app.workers.celery_app import get_celery_app

# Celery's task states are coarser-grained than the application's. This map converts
# them to the API-facing EvaluationStatus enum so callers don't need to know about
# Celery internals. Anything Celery reports that isn't in this map (REVOKED, RETRY,
# REJECTED etc.) collapses to PENDING by default.
_CELERY_STATE_TO_STATUS: dict[str, EvaluationStatus] = {
    "PENDING": EvaluationStatus.PENDING,
    "RECEIVED": EvaluationStatus.PENDING,
    "STARTED": EvaluationStatus.RUNNING,
    "SUCCESS": EvaluationStatus.COMPLETED,
    "FAILURE": EvaluationStatus.FAILED,
}


def get_result(task_id: UUID) -> AggregatedResultEntity | None:
    """Fetch the persisted aggregated result for a job, if one exists."""
    session_factory = get_sessionmaker()
    with session_factory.begin() as session:
        repo = SQLAlchemyResultRepository(session)
        try:
            return repo.get_result_by_id(task_id)
        except ResultNotFoundError:
            return None


def update_evaluation_result(job_id: UUID, result: EvaluationResponse) -> None:
    """Persist the evaluation response to the existing ``results`` row.

    Job lifecycle status is now tracked by Celery's result backend, so this function
    no longer touches a status column.
    """
    session_factory = get_sessionmaker()
    with session_factory.begin() as session:
        repo = SQLAlchemyResultRepository(session)
        repo.update_result(job_id, result=result)


def get_job_state(job_id: UUID) -> EvaluationStatus:
    """Return the current lifecycle status of a job, derived from Celery.

    The job_id is also the Celery task id (see ``evaluate.create_evaluation``), so we can
    query Celery's backend directly. Unknown task ids return PENDING because that's
    Celery's default for ids it has no record of.
    """
    async_result = AsyncResult(str(job_id), app=get_celery_app())
    return _CELERY_STATE_TO_STATUS.get(async_result.state, EvaluationStatus.PENDING)


def get_job_error(job_id: UUID) -> str | None:
    """Return the failure reason for a job, if Celery recorded one."""
    async_result = AsyncResult(str(job_id), app=get_celery_app())
    if async_result.state != "FAILURE":
        return None
    # AsyncResult.result holds the exception instance for failed tasks (with
    # result_extended=True the traceback is also available via .traceback).
    return str(async_result.result)
