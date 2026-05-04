import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.models.evaluation_model import EvaluationResult
from app.core.repositories.i_evalution_repository import IEvaluationRepository
from app.exceptions import ResultPersistenceError
from app.models import Evaluation

# todo: add insert method that inserts EvaluationResults into the EvaluationResults table and the other queries here

logger = logging.getLogger(__name__)


class SQLAlchemyEvaluationRepository(IEvaluationRepository):
    def __init__(self, session: Session) -> None:
        """
        Initialize the ResultRepository with the SQLAlchemy session.

        Args:
             session (Session): The SQLAlchemy session object.
        """
        self.session = session

    def insert(self, evaluation_result: EvaluationResult, aggregated_result_id: UUID) -> UUID:
        result = Evaluation(
            aggregated_result=aggregated_result_id,
            evaluator_id=evaluation_result.evaluator_id,
            passed=evaluation_result.passed,
            reasoning=evaluation_result.reasoning,
            normalised_score=evaluation_result.normalised_score,
            execution_time=evaluation_result.execution_time,
            error=evaluation_result.error,
        )

        try:
            self.session.add(result)
            self.session.commit()
        except SQLAlchemyError as e:
            logger.exception("Failed to persist evaluation result")
            self.session.rollback()
            raise ResultPersistenceError() from e

        return result.id
