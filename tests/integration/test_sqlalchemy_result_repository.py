from app.core.repositories.sqlalchemy_result_repository import SQLAlchemyResultRepository
from app.core.models.aggregated_result_entity import AggregatedResultEntity
from app.model import Result

def test_init_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    assert repo.session == db_session

def test_insert_works_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    initial_count = db_session.query(Result).count()  # Check if the table is empty

    entityID = repo.insert(AggregatedResultEntity(request="test", result="test"))
    final_count = db_session.query(Result).count()
    agg_result = db_session.query(Result).first()  # Since we just inserted one row, we can fetch the first

    assert final_count == initial_count + 1
    assert entityID == agg_result.id
    assert agg_result.request == "test"
    assert agg_result.result == "test"

def test_insert_with_multiple_rows_should_have_unique_id_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    initial_count = db_session.query(Result).count()

    for i in range(5):
        repo.insert(AggregatedResultEntity(request=f"test{i}", result=f"test{i}"))

    final_count = db_session.query(Result).count()
    all_results = db_session.query(Result).all()
    all_ids = {r.id for r in all_results}  # cannot have duplicates due to it being a set

    assert final_count == initial_count + 5
    assert len(all_ids) == final_count

def test_get_result_by_id_happypath(db_session):
    repo = SQLAlchemyResultRepository(db_session)
    result = AggregatedResultEntity(request="test", result="test")

    entityID = repo.insert(result)

    retrieved_result = repo.get_result_by_id(entityID)

    assert retrieved_result is not None
    assert retrieved_result.id == entityID
    assert retrieved_result.request == "test"
    assert retrieved_result.result == "test"