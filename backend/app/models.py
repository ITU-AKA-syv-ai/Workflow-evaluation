from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    """


class Result(Base):
    """
    Database model for representing an evaluation result.
    """

    __tablename__ = "results"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    request: Mapped[dict] = mapped_column(JSON)
    result: Mapped[dict] = mapped_column(JSON)

# todo: add new a new class representing the EvaluationResult table
#  containing all or most of the fields of the object, an id and foreign key referring to the id of the aggregated result entity that the evaluation is a part of
#   make a new migration and apply it using the commands in the backend README.md
