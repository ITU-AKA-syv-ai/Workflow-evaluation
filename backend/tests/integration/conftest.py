from collections.abc import Generator

import pytest
import sqlalchemy.orm
from sqlalchemy import create_engine

from models import Base

# In-memory SQLite engine for tests
engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sqlalchemy.orm.sessionmaker(bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[sqlalchemy.orm.Session, None, None]:
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)
