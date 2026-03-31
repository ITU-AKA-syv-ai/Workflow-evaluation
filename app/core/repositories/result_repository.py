from sqlalchemy.orm import Session

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.model import Result


class ResultRepository:
    """
    Repository for storing and retrieving aggregated results in the database.

    Attributes:
        session (Session): The SQLAlchemy session object.
    """

    def __init__(self, session: Session) -> None:
        """
        Constructor for the ResultRepository.

        Args:
             session (Session): The SQLAlchemy session object.
        """
        self.session = session

    def insert(self, aggregated_result: AggregatedResultEntity) -> None:
        result = Result(
            request=aggregated_result.request,
            result=aggregated_result.result,
        )
        self.session.add(result)
        self.session.commit()
