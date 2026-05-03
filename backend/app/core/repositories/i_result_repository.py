from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import EvaluationResponse


class IResultRepository(ABC):
    @abstractmethod
    def insert(self, aggregated_result: AggregatedResultEntity) -> UUID:
        """
        Insert an AggregatedResultEntity into the database.

        Args:
            aggregated_result: The aggregated result entity to persist.

        Returns:
            UUID: The id assigned to the persisted row.

        Raises:
            ResultPersistenceError: If the row could not be persisted (database error).
        """

    @abstractmethod
    def delete(self, result_id: UUID) -> None:
        """
        Delete a result row by id. No-op if the id does not exist.

        Used to roll back a Result row when queueing the corresponding Celery task fails,
        so we don't leave orphaned rows that map to no task.
        """

    @abstractmethod
    def get_result_by_id(self, result_id: UUID) -> AggregatedResultEntity:
        """
        Retrieve a single result by its unique ID.

        Raises:
            ResultNotFoundError: If no result with the given id exists.
        """

    @abstractmethod
    def get_recent_results(
        self,
        limit: int = 5,
        offset: int = 0,
        start: date | None = None,
        end: date | None = None,
        ascending: bool = False,
    ) -> list[AggregatedResultEntity]:
        """
        Retrieves a list of recent results.
        Args:
            limit (int): The number of results to retrieve. Default is 5.
            offset (int): The number of results to skip. Default is 0.
            start (date | None): Earliest date a result can be from.
            end (date | None): The latest date a result can be from.
            ascending (bool): Sort the elements in ascending order
        """

    @abstractmethod
    def update_result(self, result_id: UUID, result: EvaluationResponse) -> None:
        """Persist the final evaluation response for an existing row."""
