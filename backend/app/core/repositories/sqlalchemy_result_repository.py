import logging
from datetime import date, datetime, timedelta
from uuid import UUID
from typing import Literal

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
            ResultPersistenceError: If the database refused the write operation.
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
        """Delete a Result row by id. No-op if the id does not exist.

        Args:
            result_id: Primary key of the Result row to delete.
        """
        result = self.session.query(Result).filter(Result.id == result_id).first()
        if result is not None:
            self.session.delete(result)
            self.session.commit()

    def get_result_by_id(self, result_id: UUID) -> AggregatedResultEntity:
        """
        Retrieve a Result by id and convert it into an AggregatedResultEntity.

        The stored JSON fields (`request` and `result`) are deserialized from dictionaries
        into EvaluationRequest and EvaluationResponse objects.

        Args:
        result_id (UUID): The ID of the result to retrieve.

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

    def get_recent_results(
        self,
        limit: int = 5,
        offset: int = 0,
    ) -> list[AggregatedResultEntity]:
        """
        Each database record is converted into an AggregatedResultEntity, where the JSON
        fields are deserialized into EvaluationRequest and EvaluationResponse objects.
        If no results are found, an empty list is returned.

        Args:
            limit (int): the number of results to return. Defaults to 5.
            offset (int): the number of results to skip. Defaults to 0.

        Returns:
            list[AggregatedResultEntity]: A list of AggregatedResultEntity objects representing the results.

        """
        query = self.session.query(Result).order_by(Result.created_at.desc(), Result.id.desc()).offset(offset).limit(limit)

        list_of_results = self.session.scalars(query).all()

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

    def update(self, result_id: UUID, result: EvaluationResponse) -> None:
        """Persist the final evaluation response for an existing row.

        Args:
            result_id: Primary key of the Result row to update.
            result: The evaluation response to persist into the row's ``result`` column.

        Raises:
            ResultNotFoundError: If no result with ``result_id`` exists.
        """
        query = self.session.query(Result).filter(Result.id == result_id).first()

        if query is None:
            raise ResultNotFoundError(result_id)

        query.result = result.model_dump()
        self.session.commit()

    def get_results(
            self,
            limit: int = 5,
            offset: int = 0,
            sorting: Literal["date", "score"] = "date",
            sorting_direction: Literal["asc", "desc"] = "desc",
            start_date: date | None = None,
            end_date: date | None = None,
            min_score: float | None = None,
            max_score: float | None = None,
    ) -> list[AggregatedResultEntity]:
        """
        Filters results based on the provided criteria and returns the list of AggregatedResultEntity
        objects in descending order of creation date.

        Args:
            limit (int): The number of results to return. Defaults to 5.
            offset (int): The number of results to skip. Defaults to 0.
            sorting (Literal["date", "score"]): The field to sort by. Defaults to "date".
            sorting_direction (Literal["asc", "desc"]): The sorting direction. Defaults to "desc".
            start_date (date | None): Earliest date a result can be from. If None, no lower bound is applied.
            end_date (date | None): The latest date a result can be from. If None, no upper bound is applied.
            min_score (float | None): The minimum score a result must have. If None, no lower bound is applied.
            max_score (float | None): The maximum score a result must have. If None, no upper bound is applied.

        Returns:
             list[AggregatedResultEntity]: A list of AggregatedResultEntity objects representing the results.

        """
        stmt = select(Result)  # Sets up the base query

        # Builds the SQLAlchemy filter expression based on the provided criteria
        filters = []
        if start_date is not None:
            start_dt = datetime.combine(start_date, datetime.min.time())  # Converts date to datetime, setting time to midnight (start of day)
            filters.append(Result.created_at >= start_dt)
        if end_date is not None:
            end_dt = datetime.combine(end_date + timedelta(days=1), datetime.min.time())  # Converts date to datetime, setting time to midnight (start of next day)
            filters.append(Result.created_at <= end_dt)
        if min_score is not None:
            filters.append(Result.weighted_score >= min_score)
        if max_score is not None:
            filters.append(Result.weighted_score <= max_score)

        if filters:
            stmt = stmt.where(*filters)

        # Builds the SQLAlchemy order_by expression based on the provided sorting criteria
        field_map = {
            "date": Result.created_at,
            "score": Result.weighted_score,
        }

        field = field_map[sorting]

        stmt = stmt.order_by(
            field.asc() if sorting_direction == "asc" else field.desc()
        )

        stmt = stmt.limit(limit).offset(offset)  # Applies the limit and offset to the query

        list_of_results = self.session.scalars(stmt).all() # Executes the query and retrieves the results

        # Converts the results to AggregatedResultEntity and returns
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


