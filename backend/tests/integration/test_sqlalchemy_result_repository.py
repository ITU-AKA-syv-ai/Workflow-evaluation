import uuid
from datetime import date, datetime, timedelta
from time import sleep
from typing import cast

import pytest
from sqlalchemy.orm import Session

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import EvaluationRequest, EvaluationResponse, EvaluationResult, EvaluatorConfig
from app.core.repositories.sqlalchemy_result_repository import SQLAlchemyResultRepository
from app.exceptions import ResultNotFoundError
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
    return AggregatedResultEntity(request=request, result=result, weighted_score=result.weighted_average_score)


def test_init_happypath(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    assert repo.session == db_session


def test_insert_works_happypath(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    initial_count = db_session.query(Result).count()
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

    entityID = repo.insert(entity)  # noqa: N806
    final_count = db_session.query(Result).count()
    agg_result = db_session.query(Result).first()

    assert agg_result is not None

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
    assert agg_result.weighted_score is not None


def test_insert_with_multiple_rows_should_have_unique_id_happypath(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    initial_count = db_session.query(Result).count()

    for i in range(5):
        repo.insert(make_dummy_aggregated_result(i))

    final_count = db_session.query(Result).count()
    all_results = db_session.query(Result).all()
    all_ids = {r.id for r in all_results}

    assert final_count == initial_count + 5
    assert len(all_ids) == final_count


def test_insert_invalid_entity_raises_attributeerror_errorpath(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)

    with pytest.raises(AttributeError):
        repo.insert(cast(AggregatedResultEntity, None))  # type: ignore[arg-type]

    with pytest.raises(AttributeError):
        repo.insert(cast(AggregatedResultEntity, "This is not an entity"))  # type: ignore[arg-type]


def test_get_result_by_id_happypath(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    entity = make_dummy_aggregated_result(1)

    entityid = repo.insert(entity)
    retrieved_result = repo.get_result_by_id(entityid)

    assert retrieved_result is not None
    assert retrieved_result.id == entityid
    assert retrieved_result.request == entity.request
    assert retrieved_result.result == entity.result
    assert retrieved_result.weighted_score == entity.weighted_score


def test_get_result_by_id_nonexistent_raises_edgecase(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    fake_id = uuid.uuid4()

    with pytest.raises(ResultNotFoundError):
        repo.get_result_by_id(fake_id)


def test_get_recent_results_happypath(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    limit = 3
    offset = 1
    entities = [make_dummy_aggregated_result(i) for i in range(5)]
    subset_reversed = list(reversed(entities))
    subset_reversed = subset_reversed[offset : offset + limit]

    for entity in entities:
        repo.insert(entity)
        sleep(0.1)
    results = repo.get_recent_results(limit, offset)

    for r in results:
        print(r.id, r.created_at)
    assert len(results) == limit
    for fetched, inserted in zip(results, subset_reversed, strict=True):
        assert fetched.request == inserted.request
        assert fetched.result == inserted.result


def test_get_recent_results_default_happypath(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    entities = [make_dummy_aggregated_result(i) for i in range(5)]
    for entity in entities:
        repo.insert(entity)
        sleep(0.1)

    results = repo.get_recent_results()

    assert len(results) == 5
    for fetched, inserted in zip(results, reversed(entities), strict=True):
        assert fetched.request == inserted.request
        assert fetched.result == inserted.result


def test_get_recent_results_empty_table_edgecase(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    results = repo.get_recent_results()
    assert len(results) == 0
    assert results == []


def test_get_recent_results_big_offset_and_limit_edgecase(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    limit = 5
    offset = 4

    entities = [make_dummy_aggregated_result(i) for i in range(5)]
    subset_reversed = list(reversed(entities))
    subset_reversed = subset_reversed[offset : offset + limit]

    for entity in entities:
        repo.insert(entity)
        sleep(0.1)
    results = repo.get_recent_results(limit, offset)

    assert len(results) == 1
    for fetched, inserted in zip(results, subset_reversed, strict=True):
        assert fetched.request == inserted.request
        assert fetched.result == inserted.result


def test_get_recent_results_too_big_offset_and_limit_empty_edgecase(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    limit = 10
    offset = 10
    entities = [make_dummy_aggregated_result(i) for i in range(5)]

    for entity in entities:
        repo.insert(entity)
    results = repo.get_recent_results(limit, offset)

    assert len(results) == 0
    assert results == []


def test_update_happypath(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    entity = make_dummy_aggregated_result(1)

    result_id = repo.insert(entity)

    new_response = EvaluationResponse(
        weighted_average_score=0.5,
        results=[
            EvaluationResult(
                evaluator_id="updated_eval",
                passed=False,
                reasoning="Updated reasoning",
                normalised_score=0.5,
                execution_time=5,
                error=None,
            )
        ],
        is_partial=True,
        failure_count=1,
    )

    repo.update(result_id, new_response)

    updated = db_session.query(Result).filter(Result.id == result_id).first()

    assert updated is not None
    retrieved_result = EvaluationResponse(**updated.result)
    assert retrieved_result == new_response


def test_update_nonexistent_id_raises(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    fake_id = uuid.uuid4()

    new_response = EvaluationResponse(
        weighted_average_score=0.5,
        results=[],
        is_partial=False,
        failure_count=0,
    )

    with pytest.raises(ResultNotFoundError):
        repo.update(fake_id, new_response)

    result = db_session.query(Result).filter(Result.id == fake_id).first()
    assert result is None


def test_delete_removes_row(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    entity = make_dummy_aggregated_result(1)
    result_id = repo.insert(entity)

    repo.delete(result_id)

    assert db_session.query(Result).filter(Result.id == result_id).first() is None


def test_delete_nonexistent_id_is_noop(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    repo.delete(uuid.uuid4())  # should not raise


def test_get_results_default_happypath(db_session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    entities = [make_dummy_aggregated_result(i) for i in range(5)]
    for entity in entities:
        repo.insert(entity)
        sleep(0.1)

    results = repo.get_results()

    assert len(results) == 5
    for fetched, inserted in zip(results, reversed(entities), strict=True):
        assert fetched.request == inserted.request
        assert fetched.result == inserted.result


def test_get_results_with_limit_and_offset_happypath(db_session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    limit = 3
    offset = 1
    entities = [make_dummy_aggregated_result(i) for i in range(5)]
    subset_reversed = list(reversed(entities))
    subset_reversed = subset_reversed[offset: offset + limit]

    for entity in entities:
        repo.insert(entity)
        sleep(0.1)
    results = repo.get_results(limit, offset)

    for r in results:
        print(r.id, r.created_at)
    assert len(results) == limit
    for fetched, inserted in zip(results, subset_reversed, strict=True):
        assert fetched.request == inserted.request
        assert fetched.result == inserted.result


def test_get_results_filter_by_valid_times(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    limit = 5
    start = date.today() - timedelta(days=1)
    end = date.today() + timedelta(days=1)

    entities = [make_dummy_aggregated_result(i) for i in range(5)]

    for entity in entities:
        repo.insert(entity)
        sleep(0.001)
    results = repo.get_results(limit=limit, offset=0, start_date=start, end_date=end)

    assert len(results) == limit
    for e in results:
        assert e.created_at is not None
        assert e.created_at.date() >= start
        assert e.created_at.date() <= end


def test_get_results_filter_by_invalid_times_edge_case(db_session: Session) -> None:
    # As the service-layer (evaluate.py) takes care of exceptions, if the start_date is after the end_date,
    #  the repository should just return an empty list as there can be no results matching the criteria, rather than raising an exception.
    #  This test checks that this is the case.
    repo = SQLAlchemyResultRepository(db_session)
    limit = 5
    start = date.today() + timedelta(days=10)
    end = date.today() + timedelta(days=20)

    entities = [make_dummy_aggregated_result(i) for i in range(5)]

    for entity in entities:
        repo.insert(entity)
        sleep(0.001)
    results = repo.get_results(limit=limit, offset=0, start_date=start, end_date=end)

    assert len(results) == 0


def test_get_results_sort_asc_on_date(db_session: Session) -> None:
    repo = SQLAlchemyResultRepository(db_session)
    limit = 5
    entities = [make_dummy_aggregated_result(i) for i in range(5)]

    for entity in entities:
        repo.insert(entity)
        sleep(0.001)
    results = repo.get_results(limit=limit, sorting_direction = "asc")

    assert len(results) == limit

    for i in range(1, len(results)):
        assert results[i - 1].created_at is not None
        assert results[i].created_at is not None
        # ty is complaining about the possibility of these being None and that None cannot be compared with datetime
        assert results[i - 1].created_at <= results[i].created_at  # ty:ignore[unsupported-operator]


