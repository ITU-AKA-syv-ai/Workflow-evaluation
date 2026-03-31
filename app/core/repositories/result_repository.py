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
        Initialize the ResultRepository with a SQLAlchemy session.

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
