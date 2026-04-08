from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager

from app.api import evaluate
from app.config.settings import get_settings
from app.logging.logging_config import setup_logging


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):  # noqa: ANN202, RUF029
        get_settings()  # We validate settings at startup to fail fast
        yield

    setup_logging()

    app = FastAPI(lifespan=lifespan)

    app.include_router(evaluate.router)

    return app
