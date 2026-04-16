from abc import ABC, abstractmethod
from uuid import UUID

from backend.app.core.models.aggregated_result_entity import AggregatedResultEntity


class IResultRepository(ABC):
    @abstractmethod
    def insert(self, aggregated_result: AggregatedResultEntity) -> UUID:
        """
        Inserts an AggregatedResultEntity into the database.

        Args:
            aggregated_result (AggregatedResultEntity): The aggregated result entity object to be added to the database.
        """

    @abstractmethod
    def get_result_by_id(self, result_id: UUID) -> AggregatedResultEntity | None:
        """
        Retrieves a single result by its unique ID.

        Args:
            result_id (UUID): The unique identifier of the result to retrieve.

        Returns:
            AggregatedResultEntity | None: The result if found, otherwise None.

        """

    @abstractmethod
    def get_recent_results(self, limit: int = 5, offset: int = 0) -> list[AggregatedResultEntity]:
        """
        Retrieves a list of recent results.
        Args:
            limit (int): The number of results to retrieve. Default is 5.
            offset (int): The number of results to skip. Default is 0.

        Returns: list[AggregatedResultEntity]: A list of result objects.
                                               If no results are found, it returns an empty list.

        """
