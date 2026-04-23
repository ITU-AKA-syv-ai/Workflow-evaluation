import enum
from uuid import UUID

from celery import states
from celery.result import AsyncResult

from app.workers.celery_app import celery_app


class JobStatus(enum.StrEnum):
    """(enum.StrEnum)
    Application-level lifecycle states for an evaluation job, translated from Celery states.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobNotFoundError(Exception):
    """Raised when a task ID does not correspond to a known Celery task."""


class JobStatusService:
    """
    Translates Celery task state into application-level job status.
    """

    def get_status(self, task_id: UUID) -> tuple[JobStatus, UUID | None, str | None]:
        """
        Look up the status of a task by its Celery task ID.

        Args:
            task_id (UUID): The Celery task ID, returned by POST /evaluations.

        Returns:
            tuple[JobStatus, UUID | None, str | None]: The translated status, the result ID
                if the task completed successfully, and the error message if it failed.

        Raises:
            JobNotFoundError: If no task exists with the given ID. This distinguishes a
                typo'd or forgotten ID from a task that is genuinely pending.
        """
        result = AsyncResult(str(task_id), app=celery_app)

        # exists() returns False both for unknown IDs and for tasks whose results have
        # been expired by celery.backend_cleanup. Either way, we treat it as not found.
        if not result.exists():
            raise JobNotFoundError(f"Task {task_id} not found")

        status = _translate_state(result.state)

        result_id: UUID | None = None
        error: str | None = None
        if status == JobStatus.COMPLETED:
            # The task returns the UUID of the persisted AggregatedResultEntity as a string.
            result_id = UUID(result.result)
        elif status == JobStatus.FAILED:
            # result.result on failure is the exception instance stored by Celery.
            error = str(result.result)

        return status, result_id, error


def _translate_state(celery_state: str) -> JobStatus:
    """
    Maps a Celery task state to the application's JobStatus enum.

    Args:
        celery_state (str): One of Celery's built-in states.

    Returns:
        JobStatus: The application-level status.
    """
    if celery_state == states.PENDING:
        return JobStatus.PENDING
    if celery_state == states.STARTED:
        return JobStatus.RUNNING
    if celery_state == states.SUCCESS:
        return JobStatus.COMPLETED
    if celery_state in states.EXCEPTION_STATES:
        # FAILURE, RETRY, REVOKED are all treated as failed from the caller's perspective.
        return JobStatus.FAILED
    # Fallback for any custom or unexpected state.
    return JobStatus.PENDING

