from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config.settings import get_settings

settings = get_settings()

engine = create_engine(settings.db.sqlalchemy_database_uri)


def init_db(session: Session) -> None:
    pass
