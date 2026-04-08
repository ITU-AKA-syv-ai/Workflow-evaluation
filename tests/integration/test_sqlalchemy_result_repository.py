from app.core.repositories.sqlalchemy_result_repository import SQLAlchemyResultRepository
from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.model import Result
from app.core.models.evaluation_model import EvaluationRequest, EvaluationResult

from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.core.models.evaluation_model import EvaluationRequest, EvaluationResult

def make_dummy_aggregated_result(i: int) -> AggregatedResultEntity:
    """
    Helper to quickly generate AggregatedResultEntity objects for tests.

    Args:
        i (int): a number used to generate unique evaluator_id / model_output

    Returns:
        AggregatedResultEntity: A dummy entity ready for insertion
    """
    request = EvaluationRequest(
        model_output=f"some output {i}",
        configs=[]
    )
    result = EvaluationResult(
        evaluator_id=f"eval_{i}",
        passed=True,
        reasoning=f"Reasoning {i}",
        normalised_score=1.0,
        execution_time=10,
        error=None
    )
    return AggregatedResultEntity(request=request, result=result)

def test_init_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    assert repo.session == db_session

def test_insert_works_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    initial_count = db_session.query(Result).count()  # Check if the table is empty
    entity = make_dummy_aggregated_result(1)

    entityID = repo.insert(entity)
    final_count = db_session.query(Result).count()
    agg_result = db_session.query(Result).first()  # Since we just inserted one row, we can fetch the first

    # Deserialize JSON/dict back into Pydantic objects
    retrieved_request = EvaluationRequest(**agg_result.request)
    retrieved_result = EvaluationResult(**agg_result.result)

    assert final_count == initial_count + 1
    assert entityID == agg_result.id
    assert retrieved_request == entity.request
    assert retrieved_result == entity.result

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

def test_get_result_by_id_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    entity = make_dummy_aggregated_result(1)

    entityID = repo.insert(entity)

    retrieved_result = repo.get_result_by_id(entityID)

    assert retrieved_result is not None
    assert retrieved_result.id == entityID
    assert retrieved_result.request == entity.request
    assert retrieved_result.result == entity.result