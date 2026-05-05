from abc import ABC, abstractmethod
from datetime import date
from uuid import UUID
from typing import Literal

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
    ) -> list[AggregatedResultEntity]:
        """
        Retrieves a list of recent results.

        Args:
            limit (int): The number of results to retrieve. Default is 5.
            offset (int): The number of results to skip. Default is 0.

        Returns:
            list[AggregatedResultEntity]: A list of AggregatedResultEntity objects representing the recent results.

        """

    @abstractmethod
    def update(self, result_id: UUID, result: EvaluationResponse) -> None:
        """Persist the final evaluation response for an existing row.

        Args:
            result_id: Primary key of the Result row to update.
            result: The evaluation response to persist into the row's ``result`` column.

        Raises:
            ResultNotFoundError: If no result with ``result_id`` exists.
        """

    @abstractmethod
    def get_results(
            self,
            limit: int = 5,
            offset: int = 0,
            sorting: Literal["date", "score"] = "date",
            sorting_direction: Literal["asc", "desc"] = "desc",
            start_date: date | None = None,
            end_date: date | None = None,
            min_score: float | None = None,
            max_score: float | None = None,
    ) -> list[AggregatedResultEntity]:
        """
                Filters results based on the provided criteria and returns the list of AggregatedResultEntity
                objects in descending order of creation date.

                Args:
                    limit (int): The number of results to return. Defaults to 5.
                    offset (int): The number of results to skip. Defaults to 0.
                    sorting (Literal["date", "score"]): The field to sort by. Defaults to "date".
                    sorting_direction (Literal["asc", "desc"]): The sorting direction. Defaults to "desc".
                    start_date (date | None): Earliest date a result can be from. If None, no lower bound is applied.
                    end_date (date | None): The latest date a result can be from. If None, no upper bound is applied.
                    min_score (float | None): The minimum score a result must have. If None, no lower bound is applied.
                    max_score (float | None): The maximum score a result must have. If None, no upper bound is applied.

                Returns:
                     list[AggregatedResultEntity]: A list of AggregatedResultEntity objects representing the results.

                """
