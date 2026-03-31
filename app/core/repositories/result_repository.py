import json
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.model import Result


class ResultRepository:
    """
    Repository for storing and retrieving aggregated results in the database.

    This class provides an abstraction layer over the SQLAlchemy session for adding and retrieving
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

    def insert(self, aggregated_result: AggregatedResultEntity) -> None:
        """
        Inserts an AggregatedResultEntity into the database as a Result record.

        Maps the attributes of AggregatedResultEntity (request, result) to a Result object,
        adds it to the current session, and commits the transaction.

        Args:
            aggregated_result (AggregatedResultEntity): The aggregated result entity object to be added to the database.
        """
        result = Result(
            request=aggregated_result.request,
            result=aggregated_result.result,
        )
        self.session.add(result)
        self.session.commit()

    def get_result_by_id(self, result_id: UUID) -> AggregatedResultEntity:
        """
       Queries the database for a Result with the given ID.
        If found, it converts the Result to an AggregatedResultEntity, serializing
        the `request` and `result` fields to JSON strings.
        If the result is not found, it raises an HTTPException.

        Args:
            result_id (UUID): The ID of the result to retrieve.

        Returns:
            AggregatedResultEntity: The AggregatedResultEntity object representing the result.

        Raises:
            HTTPException: If the result is not found, it raises an HTTPException with status code 404.
        """
        result = self.session.query(Result).filter(Result.id == result_id).first()
        if result is None:
            raise HTTPException(status_code=404, detail=f"Result {result_id} not found")

        return AggregatedResultEntity(
            request=json.dumps(result.request),
            result=json.dumps(result.result),
            id=result.id,
            created_at=result.created_at,
        )
