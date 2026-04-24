from charset_normalizer.md import lru_cache
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config.settings import get_settings


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """
    Create and return a SQLAlchemy engine.
    Used for managing database connections and interactions.
    Returns:
        Engine : SQLAlchemy engine configured with the application's database settings.
    """
    settings = get_settings()
    # Create the SQLAlchemy engine
    return create_engine(settings.db.sqlalchemy_database_uri)

@lru_cache(maxsize=1)
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def init_db(session: Session) -> None:
    """
    Initialise the database.

    Attributes:
        session (Session) : SQLAlchemy session
    """

