from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config.settings import get_settings

settings = get_settings()

# Create the SQLAlchemy engine
engine = create_engine(settings.db.sqlalchemy_database_uri)


def init_db(session: Session) -> None:
    """
    Initialise the database.

    Attributes:
        session (Session) : SQLAlchemy session
    """
