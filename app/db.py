from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import settings

engine = create_engine(str(settings.DBConfig.sqlalchemy_database_uri))


def init_db(session: Session) -> None:
    pass
