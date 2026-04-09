from collections.abc import Generator

from fastapi import Depends, FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlalchemy.orm import Session
from sqlalchemy.sql.annotation import Annotated

from app.api import evaluate
from app.config.settings import get_settings
from app.db import engine


def get_db() -> Generator[Session, None, None]:  # todo: doc string is missing
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_db)]


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa: ANN202, RUF029
        get_settings()  # We validate settings at startup to fail fast
        yield

    app = FastAPI(lifespan=lifespan)

    app.include_router(evaluate.router)

    return app
