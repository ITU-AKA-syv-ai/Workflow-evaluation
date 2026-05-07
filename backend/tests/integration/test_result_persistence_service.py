"""
Service-level tests for ``ResultPersistenceService``.

These tests live at the service layer because the SQLAlchemyError → domain
exception translation, and the unit-of-work atomicity guarantee, are now the
service's responsibilities (the repos themselves no longer translate or own a
transaction). For pure mechanics around the translation and rollback we use
mock repos; the happy path uses real repos against the in-memory session
provided by ``db_session`` to confirm the wiring also works end-to-end.
"""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import EvaluationRequest, EvaluationResponse, EvaluationResult
from app.core.repositories.i_evaluation_repository import IEvaluationRepository
from app.core.repositories.i_result_repository import IResultRepository
from app.core.repositories.sqlalchemy_evaluation_repository import SQLAlchemyEvaluationRepository
from app.core.repositories.sqlalchemy_result_repository import SQLAlchemyResultRepository
from app.core.services.result_persistence_service import ResultPersistenceService
from app.exceptions import ResultPersistenceError
from app.models import Evaluation, Result


def _make_entity(num_evaluators: int = 1) -> AggregatedResultEntity:
    """Build a minimal but valid AggregatedResultEntity with `num_evaluators` breakdown rows."""
    results = [
        EvaluationResult(
            evaluator_id=f"eval_{i}",
            passed=True,
            reasoning=f"reasoning {i}",
            normalised_score=1.0,
            execution_time=10,
            error=None,
        )
        for i in range(num_evaluators)
    ]
    return AggregatedResultEntity(
        request=EvaluationRequest(model_output="some output", configs=[]),
        result=EvaluationResponse(
            weighted_average_score=1.0,
            results=results,
            is_partial=False,
            failure_count=0,
        ),
        weighted_score=1.0,
    )


def test_persist_completed_writes_aggregate_and_breakdown_rows(db_session: Session) -> None:
    """End-to-end: service writes the parent row plus one breakdown row per evaluator."""
    service = ResultPersistenceService(
        db_session,
        SQLAlchemyResultRepository(db_session),
        SQLAlchemyEvaluationRepository(db_session),
    )
    entity = _make_entity(num_evaluators=3)

    job_id = service.persist_completed(entity)

    assert db_session.query(Result).filter(Result.id == job_id).count() == 1
    assert db_session.query(Evaluation).filter(Evaluation.aggregated_result == job_id).count() == 3


def test_persist_completed_with_no_breakdown_rows_only_writes_parent(db_session: Session) -> None:
    """An EvaluationResponse with an empty results list should still produce the aggregate row."""
    service = ResultPersistenceService(
        db_session,
        SQLAlchemyResultRepository(db_session),
        SQLAlchemyEvaluationRepository(db_session),
    )
    entity = _make_entity(num_evaluators=0)

    job_id = service.persist_completed(entity)

    assert db_session.query(Result).filter(Result.id == job_id).count() == 1
    assert db_session.query(Evaluation).filter(Evaluation.aggregated_result == job_id).count() == 0


def test_persist_completed_translates_sqlalchemy_error_from_result_repo(db_session: Session) -> None:
    """A SQLAlchemyError raised by the result repo should surface as ResultPersistenceError."""
    failing_result_repo = MagicMock(spec=IResultRepository)
    failing_result_repo.insert.side_effect = SQLAlchemyError("simulated failure")
    eval_repo = MagicMock(spec=IEvaluationRepository)

    service = ResultPersistenceService(db_session, failing_result_repo, eval_repo)

    with pytest.raises(ResultPersistenceError) as exc_info:
        service.persist_completed(_make_entity())

    # The original cause must be chained so logs and debuggers can recover the underlying error.
    assert isinstance(exc_info.value.__cause__, SQLAlchemyError)
    eval_repo.insert.assert_not_called()


def test_persist_completed_translates_sqlalchemy_error_from_eval_repo(db_session: Session) -> None:
    """Same translation requirement when the eval repo is the one that fails."""
    result_repo = MagicMock(spec=IResultRepository)
    result_repo.insert.return_value = uuid4()
    failing_eval_repo = MagicMock(spec=IEvaluationRepository)
    failing_eval_repo.insert.side_effect = SQLAlchemyError("simulated failure")

    service = ResultPersistenceService(db_session, result_repo, failing_eval_repo)

    with pytest.raises(ResultPersistenceError) as exc_info:
        service.persist_completed(_make_entity(num_evaluators=2))

    assert isinstance(exc_info.value.__cause__, SQLAlchemyError)


def test_persist_completed_does_not_translate_unrelated_exceptions(db_session: Session) -> None:
    """Only SQLAlchemyError is translated. Programming errors propagate untranslated."""
    result_repo = MagicMock(spec=IResultRepository)
    result_repo.insert.side_effect = ValueError("not a DB error")
    eval_repo = MagicMock(spec=IEvaluationRepository)

    service = ResultPersistenceService(db_session, result_repo, eval_repo)

    with pytest.raises(ValueError):
        service.persist_completed(_make_entity())


def test_persist_completed_rolls_back_parent_when_breakdown_fails(db_session: Session) -> None:
    """
    If the eval repo fails AFTER the result repo successfully
    inserted the parent row, the parent row must NOT be present in the DB after
    the call.
    """
    real_result_repo = SQLAlchemyResultRepository(db_session)

    failing_eval_repo = MagicMock(spec=IEvaluationRepository)
    failing_eval_repo.insert.side_effect = SQLAlchemyError("simulated failure")

    service = ResultPersistenceService(db_session, real_result_repo, failing_eval_repo)

    initial_count = db_session.query(Result).count()

    with pytest.raises(ResultPersistenceError):
        service.persist_completed(_make_entity(num_evaluators=2))

    db_session.expire_all()

    final_count = db_session.query(Result).count()
    assert final_count == initial_count, (
        "Parent Result row leaked after eval insert failed — atomicity is broken"
    )
