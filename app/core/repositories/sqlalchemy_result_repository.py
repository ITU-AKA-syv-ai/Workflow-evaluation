from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import EvaluationRequest, EvaluationResponse
from app.core.repositories.i_result_repository import IResultRepository
from app.models import Result


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

        Converts the EvaluationRequest and EvaluationResponse objects to dictionaries
        using Pydantic's `.model_dump()` before storing them in JSON columns.

         Args:
             aggregated_result (AggregatedResultEntity): The aggregated result entity object to be added to the database.

         Returns:
             result_id (UUID): The ID of the inserted Result record.

        Raises:
            AttributeError: If entity is not an AggregatedResultEntity
        """
        result = Result(
            request=aggregated_result.request.model_dump(),
            result=aggregated_result.result.model_dump(),
        )
        self.session.add(result)
        self.session.commit()
        return result.id

    def get_result_by_id(self, result_id: UUID) -> AggregatedResultEntity | None:
        """
        Retrieves a Result by its ID and converts it into an AggregatedResultEntity.

        The stored JSON fields (`request` and `result`) are deserialized from dictionaries
        into EvaluationRequest and EvaluationResponse objects.

        Args:
            result_id (UUID): The ID of the result to retrieve.

        Returns:
            AggregatedResultEntity | None: The result if found, otherwise None.

        """
        result = self.session.query(Result).filter(Result.id == result_id).first()
        if result is None:
            return None

        req: dict = result.request
        res: dict = result.result

        return AggregatedResultEntity(
            request=EvaluationRequest(**req),
            result=EvaluationResponse(**res),
            id=result.id,
            created_at=result.created_at,
        )

    def get_recent_results(self, limit: int = 5, offset: int = 0) -> list[AggregatedResultEntity]:
        """
        Retrieves a paginated list of the most recent results, ordered by creation time.

        Each database record is converted into an AggregatedResultEntity, where the JSON
        fields are deserialized into EvaluationRequest and EvaluationResponse objects.
        If no results are found, an empty list is returned.

        Args:
            limit (int): the number of results to return. Defaults to 5.
            offset (int): the number of results to skip. Defaults to 0.

        Returns:
            list[AggregatedResultEntity]: A list of AggregatedResultEntity objects representing the results.

        """
        list_of_results = (
            self.session.query(Result)
            .order_by(
                Result.created_at.desc(),
                Result.id.desc()
            )
            .limit(limit)
            .offset(offset)
            .all()
        )

        aggregated_results = []
        for result in list_of_results:
            req: dict = result.request
            res: dict = result.result
            aggregated_results.append(
                AggregatedResultEntity(
                    request=EvaluationRequest(**req),
                    result=EvaluationResponse(**res),
                    id=result.id,
                    created_at=result.created_at,
                )
            )

        return aggregated_results
