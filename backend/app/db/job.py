import enum
import uuid
from datetime import UTC, datetime, timezone

from app.db.base import Base
from sqlalchemy import JSON, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class JobStatus(enum.StrEnum):
    """
    Lifecycle states for an evaluation job.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


def _utcnow() -> datetime:
    """Returns a timezone-aware UTC datetime."""
    return datetime.now(UTC)


class Job(Base):
    """
    Database model for an evaluation job. Tracks the lifecycle of an asynchronous evaluation,
    including its status, the original request, and the result once available.

    Attributes:
        id (UUID): Primary key. Used as the public job ID returned from POST.
        status (JobStatus): Current lifecycle state.
        request_payload (dict): The original EvaluationRequest serialized as JSON.
        result_payload (dict | None): The EvaluationResponse serialized as JSON, populated when status is COMPLETED.
        error (str | None): Error message, populated when status is FAILED.
        created_at (datetime): When the job row was inserted.
        started_at (datetime | None): When the worker began executing.
        completed_at (datetime | None): When the job reached a terminal state.
    """

    __tablename__ = "evaluation_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"),
        default=JobStatus.PENDING,
        nullable=False,
    )
    request_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    result_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)