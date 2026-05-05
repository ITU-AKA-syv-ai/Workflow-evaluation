import logging
from uuid import UUID

from pydantic import json
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.models.evaluation_model import EvaluationResult
from app.core.providers.base import LLMResponse
from app.core.repositories.i_evalution_repository import IEvaluationRepository
from app.exceptions import ResultNotFoundError, ResultPersistenceError
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

    def serialize(self, value: str | LLMResponse | None) -> dict:
        if isinstance(value, LLMResponse):
            value: dict = value.to_dict()
        return json.dumps(value)

    def insert(self, evaluation_result: EvaluationResult, aggregated_result_id: UUID) -> UUID:
        result = Evaluation(
            aggregated_result=aggregated_result_id,
            evaluator_id=evaluation_result.evaluator_id,
            passed=evaluation_result.passed,
            reasoning=self.serialize(evaluation_result.reasoning),
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

    def get_evaluation_by_id(self, evaluation_id: UUID) -> EvaluationResult:
        query: Evaluation | None = self.session.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
        if query is None:
            raise ResultNotFoundError(evaluation_id)

        if query.reasoning is None:
            reasoning = None
        else:
            reasoning = json.loads(query.reasoning)
            if query.evaluator_id == "LLM_judge":
                reasoning = LLMResponse(results=reasoning["results"])

        return EvaluationResult(
            evaluator_id=query.evaluator_id,
            passed=query.passed,
            reasoning=reasoning,
            normalised_score=query.normalised_score,
            execution_time=query.execution_time,
            error=query.error,
        )

    # def update_aggregated_result_id(self, evaluation_result_id: UUID, aggregated_result_id: UUID) -> UUID:
