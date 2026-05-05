import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    """


class EvaluationStatus(enum.Enum):
    """
    API-facing lifecycle states for an evaluation job.

    The values map onto Celery's task states (see
    ``app.core.services.job_status_service._CELERY_STATE_TO_STATUS``). They are no
    longer persisted on the ``results`` table -- Celery's result backend is the source
    of truth for live status.
    """

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Result(Base):
    """
    Database model for a persisted evaluation. Holds the original request and the
    response payload. Lifecycle status is intentionally absent as
    that lives in Celery's result backend.
    """

    __tablename__ = "results"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
    weighted_score: Mapped[float] = mapped_column(Float)

    tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    model_name: Mapped[str | None] = mapped_column(String, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String, nullable=True)

    request: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON, nullable=True)


class Evaluation(Base):
    """
    Database model for containing a single evaluation that are a part of a Result.

    The attributes correspond to the ones of an EvaluationResult object.

    Attributes:
        id (UUID): The unique identifier of the evaluation.
        aggregated_result (Result): The connection to the result, which this evaluation is part of
        evaluator_id (str): The name of the evaluator
        passed (bool): Whether the evaluation is successful or not
        reasoning (JSON): The reasoning behind the score of the evaluation
        normalised_score (float): The normalised score of the evaluation
        execution_time (float): The execution time of the evaluation
        error(str): If something went wrong, this will contain an error message
    """
    __tablename__ = "evaluations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    aggregated_result: Mapped[UUID] = mapped_column(ForeignKey("results.id"), nullable=False)
    evaluator_id: Mapped[str] = mapped_column(String, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    reasoning: Mapped[JSON] = mapped_column(JSON, nullable=True)
    normalised_score: Mapped[float] = mapped_column(Float, nullable=False)
    execution_time: Mapped[float] = mapped_column(Float, nullable=True)
    error: Mapped[str] = mapped_column(String, nullable=True)
