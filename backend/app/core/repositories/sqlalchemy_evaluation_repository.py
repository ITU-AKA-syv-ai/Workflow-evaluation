import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.models.evaluation_model import EvaluationResult
from app.core.repositories.i_evalution_repository import IEvaluationRepository
from app.exceptions import ResultPersistenceError
from app.models import Evaluation

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
        """
        Insert an EvaluationResult into the database.

        Args:
            evaluation_result: The evaluation result entity to persist.
            aggregated_result_id: The id of the aggregated result entity the evaluation result belongs to.

        Returns:
            UUID: The id assigned to the persisted row.

        Raises:
            AttributeError: If entity is not an EvaluationResult entity.
            ResultPersistenceError: If the database refused the write operation.
        """

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
