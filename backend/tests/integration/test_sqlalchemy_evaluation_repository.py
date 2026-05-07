from app.core.providers.base import CriterionResult
import uuid
from typing import cast

import pytest
from sqlalchemy.orm import Session

from app.core.models.evaluation_model import EvaluationResult
from app.core.providers.base import LLMResponse
from app.exceptions import ResultPersistenceError
from app.models import Evaluation
from app.core.repositories.sqlalchemy_evaluation_repository import SQLAlchemyEvaluationRepository


def make_dummy_evaluation_result(i: int) -> EvaluationResult:
    """
    Helper to quickly generate EvaluationResult objects for tests.

    Args:
        i (int): a number used to generate unique evaluator_id / model_output

    Returns:
        EvaluationResult: A dummy entity ready for insertion
    """

    return EvaluationResult(
        evaluator_id=f"eval_{i}",
        passed=True,
        reasoning=f"Reasoning {i}",
        normalised_score=1.0,
        execution_time=10,
        error=None,
    )


def test_init_happypath(db_session: Session) -> None:
    repo = SQLAlchemyEvaluationRepository(db_session)
    assert repo.session == db_session


def test_insert_works_happypath(db_session: Session) -> None:
    repo = SQLAlchemyEvaluationRepository(db_session)
    initial_count = db_session.query(Evaluation).count()
    entity = EvaluationResult(
        evaluator_id="eval",
        passed=True,
        reasoning="Reasoning",
        normalised_score=1.0,
        execution_time=10,
        error=None,
    )

    agg_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

    entityID = repo.insert(entity, agg_id)  # noqa: N806
    final_count = db_session.query(Evaluation).count()
    evaluation_result = db_session.query(Evaluation).first()

    assert evaluation_result is not None

    assert final_count == initial_count + 1
    assert entityID == evaluation_result.id

    assert evaluation_result.aggregated_result == agg_id
    assert evaluation_result.evaluator_id == entity.evaluator_id
    assert evaluation_result.passed == entity.passed
    assert evaluation_result.reasoning == entity.reasoning
    assert evaluation_result.normalised_score == entity.normalised_score
    assert evaluation_result.execution_time == entity.execution_time
    assert evaluation_result.error is None


def test_insert_works_with_LLMResponse(db_session: Session) -> None:  # noqa: N802
    repo = SQLAlchemyEvaluationRepository(db_session)
    initial_count = db_session.query(Evaluation).count()

    criterion_list = []
    criterion_list.append(
        CriterionResult(
            criterion_name="Test",
            reasoning="Reasoning",
            score=2
        )
    )
    criterion_list.append(
        CriterionResult(
            criterion_name="Test2",
            reasoning="Reasoning",
            score=3
        )
    )

    llm_reasoning = LLMResponse(
        results=criterion_list,
    )

    entity = EvaluationResult(
        evaluator_id="eval",
        passed=True,
        reasoning=llm_reasoning,
        normalised_score=1.0,
        execution_time=10,
        error=None,
    )

    agg_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

    entityID = repo.insert(entity, agg_id)  # noqa: N806
    final_count = db_session.query(Evaluation).count()
    evaluation_result = db_session.query(Evaluation).first()

    # Reasoning gets converted to a dict in the insert method
    # Therefore the same is done here for the reasoning assertion
    if isinstance(entity.reasoning, LLMResponse):
        entity_reasoning = entity.reasoning.model_dump()
    else:
        entity_reasoning = entity.reasoning

    assert evaluation_result is not None

    assert final_count == initial_count + 1
    assert entityID == evaluation_result.id

    assert evaluation_result.aggregated_result == agg_id
    assert evaluation_result.evaluator_id == entity.evaluator_id
    assert evaluation_result.passed == entity.passed
    assert evaluation_result.reasoning == entity_reasoning
    assert evaluation_result.normalised_score == entity.normalised_score
    assert evaluation_result.execution_time == entity.execution_time
    assert evaluation_result.error is None


def test_insert_with_multiple_rows_should_have_unique_id_happypath(db_session: Session) -> None:
    repo = SQLAlchemyEvaluationRepository(db_session)
    initial_count = db_session.query(Evaluation).count()

    for i in range(5):
        agg_id = uuid.uuid4()
        repo.insert(make_dummy_evaluation_result(i), agg_id)

    final_count = db_session.query(Evaluation).count()
    all_results = db_session.query(Evaluation).all()
    all_ids = {r.id for r in all_results}

    assert final_count == initial_count + 5
    assert len(all_ids) == final_count


def test_insert_invalid_entity_raises_attributeerror_errorpath(db_session: Session) -> None:
    repo = SQLAlchemyEvaluationRepository(db_session)

    with pytest.raises(AttributeError):
        repo.insert(cast(EvaluationResult, cast(object, "This is not an entity")), uuid.UUID("00000000-0000-0000-0000-000000000000"))  # type: ignore[arg-type]

    with pytest.raises(ResultPersistenceError):
        repo.insert(make_dummy_evaluation_result(1), cast(uuid.UUID, cast(object, 0)))
