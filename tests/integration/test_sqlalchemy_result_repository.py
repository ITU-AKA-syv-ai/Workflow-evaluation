import uuid

import pytest

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import EvaluationRequest, EvaluationResult, EvaluatorConfig, EvaluationResponse
from app.core.repositories.sqlalchemy_result_repository import SQLAlchemyResultRepository
from app.models import Result


def make_dummy_aggregated_result(i: int) -> AggregatedResultEntity:
    """
    Helper to quickly generate AggregatedResultEntity objects for tests.

    Args:
        i (int): a number used to generate unique evaluator_id / model_output

    Returns:
        AggregatedResultEntity: A dummy entity ready for insertion
    """
    request = EvaluationRequest(model_output=f"some output {i}", configs=[])
    result = EvaluationResponse(
        weighted_average_score=1.0,
        results=[
            EvaluationResult(
                evaluator_id=f"eval_{i}",
                passed=True,
                reasoning=f"Reasoning {i}",
                normalised_score=1.0,
                execution_time=10,
                error=None,
            )
        ],
        is_partial=False,
        failure_count=0,
    )
    return AggregatedResultEntity(request=request, result=result)


def test_init_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    assert repo.session == db_session


def test_insert_works_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    initial_count = db_session.query(Result).count()  # Check if the table is empty
    request = EvaluationRequest(
        model_output="some output",
        configs=[
            EvaluatorConfig(evaluator_id="eval_1", config={"param": 123}),
            EvaluatorConfig(evaluator_id="eval_2", config={"param": 456}),
        ],
    )
    result = EvaluationResponse(
        weighted_average_score=1.0,
        results=[
            EvaluationResult(
                evaluator_id="eval",
                passed=True,
                reasoning="Reasoning",
                normalised_score=1.0,
                execution_time=10,
                error=None,
            )
        ],
        is_partial=False,
        failure_count=0,
    )
    entity = AggregatedResultEntity(request=request, result=result)

    entityID = repo.insert(entity)
    final_count = db_session.query(Result).count()
    agg_result = db_session.query(Result).first()  # Since we just inserted one row, we can fetch the first

    # Deserialize JSON/dict back into Pydantic objects
    retrieved_request = EvaluationRequest(**agg_result.request)
    retrieved_result = EvaluationResponse(**agg_result.result)

    assert final_count == initial_count + 1
    assert entityID == agg_result.id
    assert retrieved_request == entity.request
    assert retrieved_result == entity.result

    assert entity.id is None
    assert entity.created_at is None
    assert agg_result.id is not None
    assert agg_result.created_at is not None


def test_insert_with_multiple_rows_should_have_unique_id_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    initial_count = db_session.query(Result).count()

    for i in range(5):
        repo.insert(make_dummy_aggregated_result(i))

    final_count = db_session.query(Result).count()
    all_results = db_session.query(Result).all()
    all_ids = {r.id for r in all_results}  # cannot have duplicates due to it being a set

    assert final_count == initial_count + 5
    assert len(all_ids) == final_count


def test_insert_invalid_entity_raises_attributeError_errorpath(db_session):
    repo = SQLAlchemyResultRepository(db_session)

    with pytest.raises(AttributeError):
        repo.insert(None)

    with pytest.raises(AttributeError):
        repo.insert("This is not an entity")


def test_get_result_by_id_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    entity = make_dummy_aggregated_result(1)

    entityID = repo.insert(entity)
    retrieved_result = repo.get_result_by_id(entityID)

    assert retrieved_result is not None
    assert retrieved_result.id == entityID
    assert retrieved_result.request == entity.request
    assert retrieved_result.result == entity.result


def test_get_result_by_id_nonexistent_None_edgecase(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    fake_id = uuid.uuid4()

    result = repo.get_result_by_id(fake_id)

    assert result is None


def test_get_recent_results_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    limit = 3
    offset = 1
    entities = [make_dummy_aggregated_result(i) for i in range(5)]
    subset_reversed = list(reversed(entities))
    subset_reversed = subset_reversed[offset : offset + limit]  # reversed to get the most recent first

    for entity in entities:
        repo.insert(entity)
    results = repo.get_recent_results(limit, offset)

    assert len(results) == limit
    for fetched, inserted in zip(results, subset_reversed):
        assert fetched.request == inserted.request
        assert fetched.result == inserted.result


def test_get_recent_results_default_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    entities = [make_dummy_aggregated_result(i) for i in range(5)]
    for entity in entities:
        repo.insert(entity)

    results = repo.get_recent_results()

    assert len(results) == 5
    for fetched, inserted in zip(results, reversed(entities)):  # reversed to get the most recent first
        assert fetched.request == inserted.request
        assert fetched.result == inserted.result


def test_get_recent_results_empty_table_edgecase(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    results = repo.get_recent_results()
    assert len(results) == 0
    assert results == []


def test_get_recent_results_big_offset_and_limit_edgecase(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    limit = 5
    offset = 4

    entities = [make_dummy_aggregated_result(i) for i in range(5)]
    subset_reversed = list(reversed(entities))
    subset_reversed = subset_reversed[offset : offset + limit]  # reversed to get the most recent first

    for entity in entities:
        repo.insert(entity)
    results = repo.get_recent_results(limit, offset)

    assert len(results) == 1  # if the list has five elements and the offset is 4, it should only return one element
    for fetched, inserted in zip(results, subset_reversed):
        assert fetched.request == inserted.request
        assert fetched.result == inserted.result


def test_get_recent_results_too_big_offset_and_limit_empty_edgecase(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    limit = 10
    offset = 10
    entities = [make_dummy_aggregated_result(i) for i in range(5)]

    for entity in entities:
        repo.insert(entity)
    results = repo.get_recent_results(limit, offset)

    assert len(results) == 0
    assert results == []
