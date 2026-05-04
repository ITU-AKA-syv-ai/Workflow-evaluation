from sqlalchemy.orm import Session

from app.core.repositories.i_result_repository import IResultRepository

# todo: add insert method that inserts EvaluationResults into the EvaluationResults table and the other queries here


class SQLAlchemyEvaluationRepository(IResultRepository):
    def __init__(self, session: Session) -> None:
        """
        Initialize the ResultRepository with the SQLAlchemy session.

        Args:
             session (Session): The SQLAlchemy session object.
        """
        self.session = session
