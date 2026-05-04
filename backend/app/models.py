import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime
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

    request: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON, nullable=True)

# todo: add new a new class representing the EvaluationResult table
#  containing all or most of the fields of the object, an id and foreign key referring to the id of the aggregated result entity that the evaluation is a part of
#   make a new migration and apply it using the commands in the backend README.md
