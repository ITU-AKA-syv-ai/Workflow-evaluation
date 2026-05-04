import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import EvaluationRequest, EvaluationResponse
from app.core.repositories.i_result_repository import IResultRepository
from app.exceptions import ResultNotFoundError, ResultPersistenceError
from app.models import Result

logger = logging.getLogger(__name__)


class SQLAlchemyResultRepository(IResultRepository):
    """
    Implements IResultRepository to insert and retrieve aggregated results in the database.

    Provides an abstraction layer over the SQLAlchemy session for adding and retrieving
    AggregatedResultEntity objects as Result records.

    Attributes:
        session (Session): The SQLAlchemy session object.
    """

    def __init__(self, session: Session) -> None:
        """
        Initialize the ResultRepository with the SQLAlchemy session.

        Args:
             session (Session): The SQLAlchemy session object.
        """
        self.session = session

    def insert(self, aggregated_result: AggregatedResultEntity) -> UUID:
        """
        Insert an AggregatedResultEntity into the database as a Result record.

        The EvaluationRequest / EvaluationResponse are stored as JSON. The job's
        lifecycle status is *not* stored here — Celery's result backend owns it.

        Args:
            aggregated_result: The aggregated result entity to persist.

        Returns:
            UUID: The ID of the inserted Result record.

        Raises:
            AttributeError: If entity is not an AggregatedResultEntity.
            ResultPersistenceError: If the database refused the write.
        """
        result = Result(
            request=aggregated_result.request.model_dump(),
            result=aggregated_result.result.model_dump() if aggregated_result.result else None,
            weighted_score=aggregated_result.weighted_score,
        )

        try:
            self.session.add(result)
            self.session.commit()
        except SQLAlchemyError as e:
            logger.exception("Failed to persist aggregated result")
            self.session.rollback()
            raise ResultPersistenceError() from e

        return result.id

    def delete(self, result_id: UUID) -> None:
        """Delete a Result row by id. No-op if the id does not exist."""
        result = self.session.query(Result).filter(Result.id == result_id).first()
        if result is not None:
            self.session.delete(result)
            self.session.commit()

    def get_result_by_id(self, result_id: UUID) -> AggregatedResultEntity:
        """
        Retrieve a Result by id and convert it into an AggregatedResultEntity.

        ``status`` is left unset on the returned entity; the API layer populates it
        from Celery's result backend before responding.

        Raises:
            ResultNotFoundError: If no result with ``result_id`` exists.
        """
        stmt = select(Result).where(Result.id == result_id)
        result = self.session.scalars(stmt).one_or_none()
        if result is None:
            raise ResultNotFoundError(result_id)

        req: dict = result.request
        res: dict = result.result

        return AggregatedResultEntity(
            request=EvaluationRequest(**req),
            result=EvaluationResponse(**res) if res else None,
            id=result.id,
            created_at=result.created_at,
            updated_at=result.updated_at,
            weighted_score=result.weighted_score,
        )

    def get_recent_results(self, limit: int = 5, offset: int = 0) -> list[AggregatedResultEntity]:
        """Retrieve a paginated list of the most recent results, ordered by creation time."""
        stmt = select(Result).order_by(Result.created_at.desc(), Result.id.desc()).limit(limit).offset(offset)
        list_of_results = self.session.scalars(stmt).all()

        aggregated_results = []
        for result in list_of_results:
            req: dict = result.request
            res: dict = result.result
            aggregated_results.append(
                AggregatedResultEntity(
                    request=EvaluationRequest(**req),
                    result=EvaluationResponse(**res) if res else None,
                    id=result.id,
                    created_at=result.created_at,
                    updated_at=result.updated_at,
                    weighted_score=result.weighted_score,
                )
            )

        return aggregated_results

    def update_result(self, result_id: UUID, result: EvaluationResponse) -> None:
        """Persist the final evaluation response for an existing row."""
        query = self.session.query(Result).filter(Result.id == result_id).first()

        if query:
            query.result = result.model_dump()
            self.session.flush()
