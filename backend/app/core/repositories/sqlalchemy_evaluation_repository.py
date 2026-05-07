from uuid import UUID

from sqlalchemy.orm import Session

from app.core.models.evaluation_model import EvaluationResult
from app.core.providers.base import LLMResponse
from app.core.repositories.i_evaluation_repository import IEvaluationRepository
from app.models import Evaluation


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

        This repo does not own the transaction. The caller (typically a service)
        is responsible for wrapping calls in ``with session.begin():`` and for
        translating ``SQLAlchemyError`` into a domain exception.

        Args:
            evaluation_result: The evaluation result entity to persist.
            aggregated_result_id: The id of the aggregated result entity the evaluation result belongs to.

        Returns:
            UUID: The id assigned to the persisted row.

        Raises:
            AttributeError: If entity is not an EvaluationResult entity.
            SQLAlchemyError: If the database refused the write operation. The
                caller is expected to translate this into a domain error.
        """

        # LLMResponse is a Pydantic model and must be converted to a dict
        # before it can be stored in the JSON column.
        if isinstance(evaluation_result.reasoning, LLMResponse):
            reasoning = evaluation_result.reasoning.model_dump()
        else:
            reasoning = evaluation_result.reasoning

        result = Evaluation(
            aggregated_result=aggregated_result_id,
            evaluator_id=evaluation_result.evaluator_id,
            passed=evaluation_result.passed,
            reasoning=reasoning,
            normalised_score=evaluation_result.normalised_score,
            execution_time=evaluation_result.execution_time,
            error=evaluation_result.error,
        )

        self.session.add(result)
        self.session.flush()

        return result.id
