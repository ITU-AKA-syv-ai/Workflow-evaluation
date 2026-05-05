from abc import ABC, abstractmethod
from uuid import UUID

from app.core.models.evaluation_model import EvaluationResult


class IEvaluationRepository(ABC):
    @abstractmethod
    def insert(self, evaluation_result: EvaluationResult, aggregated_result_id: UUID) -> UUID:
        """
        Insert an EvaluationResult into the database.

        Args:
            evaluation_result: The evaluation result entity to persist.
            aggregated_result_id: The id of the aggregated result entity the evaluation result belongs to.

        Returns:
            UUID: The id assigned to the persisted row.

        Raises:
            ResultPersistenceError: If the row could not be persisted (database error).
        """

    # todo: update
