from collections.abc import Generator
from time import monotonic
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.concurrency import asynccontextmanager
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from app.api import evaluate, health
from app.api.exception_handler import evaluation_error_handler, internal_error_handler
from app.config.settings import get_settings
from app.db import get_engine
from app.exceptions import EvaluationError
from app.logging.logging_config import setup_logging


def get_db() -> Generator[Session, None, None]:
    """
    Provides a database session for a single request.

    This function is used to inject a SQLAlchemy session into route handlers.
    A new session will be created for each request and automatically closed after the request is completed.

    Yields:
        Session: SQLAlchemy session used to interact with the database.

    """
    with Session(get_engine()) as session:
        yield session


# Type alias for a database session dependency. Tells FastAPI to inject a SQLAlchemy Session (provided by get_db) into route handlers automatically using dependency injection
SessionDep = Annotated[Session, Depends(get_db)]


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa: ANN202, RUF029
        get_settings()  # We validate settings at startup to fail fast
        app.state.started_at = monotonic()  # time app started
        yield

    setup_logging()

    app = FastAPI(lifespan=lifespan)

    app.add_middleware(
            CORSMiddleware, allow_origins=["http://localhost:8000", "http://localhost:5173", "*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
    )

    app.include_router(evaluate.router)
    app.include_router(health.router)

    app.add_exception_handler(EvaluationError, evaluation_error_handler)
    app.add_exception_handler(Exception, internal_error_handler)

    return app
