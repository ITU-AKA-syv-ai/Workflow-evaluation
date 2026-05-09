import logging
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.repositories.i_evaluation_repository import IEvaluationRepository
from app.core.repositories.i_result_repository import IResultRepository
from app.exceptions import ResultPersistenceError

logger = logging.getLogger(__name__)


class ResultPersistenceService:
    """
    Owns the unit of work for persisting a completed evaluation.

    The service writes the aggregated result row and its per-evaluator breakdown
    rows inside a single SQLAlchemy transaction, so a failure in either insert
    rolls the entire write back. Repos used by this service must NOT call
    ``commit`` themselves; they are expected to ``add`` and optionally ``flush``,
    leaving transaction management to this layer.

    Translation of low-level ``SQLAlchemyError`` into the domain-level
    ``ResultPersistenceError`` also lives here, so callers (endpoints, workers)
    only have to handle the domain exception.
    """

    def __init__(
        self,
        session: Session,
        result_repo: IResultRepository,
        eval_repo: IEvaluationRepository,
    ) -> None:
        self.session = session
        self.result_repo = result_repo
        self.eval_repo = eval_repo

    def persist_completed(self, entity: AggregatedResultEntity) -> UUID:
        """
        Persist an aggregated result and its per-evaluator breakdown rows
        atomically.

        The ``with session.begin()`` context manager commits on clean exit and
        rolls back if any exception escapes the block.

        Args:
            entity: The aggregated result entity to persist. ``entity.result``
                must be populated; the per-evaluator rows are taken from
                ``entity.result.results``.

        Returns:
            UUID: The id assigned to the aggregated result row.

        Raises:
            ResultPersistenceError: If any underlying database operation fails.
                The transaction has been rolled back by the time this is raised.
        """
        try:
            with self.session.begin():
                job_id = self.result_repo.insert(entity)
                if entity.result is not None:
                    for single in entity.result.results:
                        self.eval_repo.insert(single, job_id)
                return job_id
        except SQLAlchemyError as e:
            logger.exception("Failed to persist evaluation result")
            raise ResultPersistenceError() from e
