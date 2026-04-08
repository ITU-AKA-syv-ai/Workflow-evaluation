from uuid import UUID

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.repositories.i_result_repository import IResultRepository
from app.model import Result
from app.core.models.evaluation_model import EvaluationRequest, EvaluationResult


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
        Inserts an AggregatedResultEntity into the database as a Result record.

       Converts the EvaluationRequest and EvaluationResult objects to dictionaries
       using Pydantic's `.model_dump()` before storing them in JSON columns.

        Args:
            aggregated_result (AggregatedResultEntity): The aggregated result entity object to be added to the database.

        Returns:
            result_id (UUID): The ID of the inserted Result record.
        """
        result = Result(
            request=aggregated_result.request.model_dump(),
            result=aggregated_result.result.model_dump(),
        )
        self.session.add(result)
        self.session.commit()
        return result.id

    def get_result_by_id(self, result_id: UUID) -> AggregatedResultEntity:
        """
        Retrieves a Result by its ID and converts it into an AggregatedResultEntity.

        The stored JSON fields (`request` and `result`) are deserialized from dictionaries
        into EvaluationRequest and EvaluationResult objects.

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

        req: dict = result.request
        res: dict = result.result

        return AggregatedResultEntity(
            request=EvaluationRequest(**req),
            result=EvaluationResult(**res),
            id=result.id,
            created_at=result.created_at,
        )

    def get_recent_results(self, limit:int, offset:int) -> list[AggregatedResultEntity]:
        """
        Retrieves a paginated list of the most recent results, ordered by creation time.

        Each database record is converted into an AggregatedResultEntity, where the JSON
        fields are deserialized into EvaluationRequest and EvaluationResult objects.
        If no results are found, an empty list is returned.

        Args:
            limit (int): the number of results to return
            offset (int): the number of results to skip

        Returns:
            list[AggregatedResultEntity]: A list of AggregatedResultEntity objects representing the results.

        """
        list_of_results = self.session.query(Result).order_by(Result.created_at.desc()).limit(limit).offset(offset).all()

        aggregated_results = []
        for result in list_of_results:
            req: dict = result.request
            res: dict = result.result
            aggregated_results.append(AggregatedResultEntity(
               request=EvaluationRequest(**req),
               result=EvaluationResult(**res),
               id=result.id,
               created_at=result.created_at,
            ))

        return aggregated_results



