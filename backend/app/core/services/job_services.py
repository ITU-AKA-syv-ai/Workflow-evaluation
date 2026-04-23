import uuid
from datetime import UTC, datetime, timezone

from sqlalchemy.orm import Session

from app.db.job import Job, JobStatus


class JobNotFoundError(Exception):
    """Raised when a job ID does not exist in the database."""


class JobService:
    """
    Manages the lifecycle of evaluation jobs in the database.

    All status transitions go through this service. Each transition method commits its own transaction.

    Attributes:
        session (Session): The SQLAlchemy session used for all DB operations.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize the job service with a SQLAlchemy session.

        Args:
            session (Session): The SQLAlchemy session used for all DB operations.
        """
        self._session = session

    def create_pending(self, request_payload: dict) -> Job:
        """
        Create a new job in PENDING status.

        Args:
            request_payload (dict): The serialized EvaluationRequest to be stored on the job row.

        Returns:
            Job: The newly created job, with its generated ID populated.
        """
        job = Job(
            id=uuid.uuid4(),
            status=JobStatus.PENDING,
            request_payload=request_payload,
        )
        self._session.add(job)
        self._session.commit()
        self._session.refresh(job)
        return job

    def get(self, job_id: uuid.UUID) -> Job:
        """
        Retrieve a job by its unique ID.

        Args:
            job_id (UUID): The unique identifier of the job.

        Returns:
            Job: The job associated with the given ID.

        Raises:
            JobNotFoundError: If no job exists with the given ID.
        """
        job = self._session.get(Job, job_id)
        if job is None:
            raise JobNotFoundError(f"Job {job_id} not found")
        return job

    def mark_running(self, job_id: uuid.UUID) -> None:
        """
        Transition a job to RUNNING and record the start time.

        Args:
            job_id (UUID): The unique identifier of the job to update.
        """
        job = self.get(job_id)
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(UTC)
        self._session.commit()

    def mark_completed(self, job_id: uuid.UUID, result_payload: dict) -> None:
        """
        Transition a job to COMPLETED and store the result.

        Args:
            job_id (UUID): The unique identifier of the job to update.
            result_payload (dict): The serialized EvaluationResponse to store on the job.
        """
        job = self.get(job_id)
        job.status = JobStatus.COMPLETED
        job.result_payload = result_payload
        job.completed_at = datetime.now(UTC)
        self._session.commit()

    def mark_failed(self, job_id: uuid.UUID, error: str) -> None:
        """
        Transition a job to FAILED with an error message.

        Args:
            job_id (UUID): The unique identifier of the job to update.
            error (str): The error message to store on the job.
        """
        job = self.get(job_id)
        job.status = JobStatus.FAILED
        job.error = error
        job.completed_at = datetime.now(UTC)
        self._session.commit()
