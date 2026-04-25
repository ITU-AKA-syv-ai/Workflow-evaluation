from uuid import UUID

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import EvaluationResponse
from app.core.repositories.sqlalchemy_result_repository import SQLAlchemyResultRepository
from app.db import get_sessionmaker
from app.models import EvaluationStatus


def get_result(task_id: UUID) -> AggregatedResultEntity | None:
    session_factory = get_sessionmaker()
    with session_factory.begin() as session:
        repo = SQLAlchemyResultRepository(session)
        return repo.get_result_by_id(task_id)


def update_evaluation_status(job_id: UUID, status: EvaluationStatus, error: str | None = None) -> None:
    """
    Update the status of an existing job. Useful for 'RUNNING' and 'FAILED' states.
    """
    session_factory = get_sessionmaker()
    with session_factory.begin() as session:
        repo = SQLAlchemyResultRepository(session)
        repo.update_status(job_id, status=status, error=error)


def update_evaluation_result(job_id: UUID, result: EvaluationResponse) -> None:
    """
    Save the final result and automatically mark the job as COMPLETED.
    """
    session_factory = get_sessionmaker()
    with session_factory.begin() as session:
        repo = SQLAlchemyResultRepository(session)
        repo.update_result(job_id, result=result, status=EvaluationStatus.COMPLETED)
