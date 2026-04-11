import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

TEST_DATABASE_URL = "postgresql+psycopg://test_user:password@localhost:5432/test_db"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="function")
def db_session():  # noqa: ANN201
    """Create a new database session for a test."""
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    yield session  # Wait for the test to finish

    session.close()
    Base.metadata.drop_all(bind=engine)
