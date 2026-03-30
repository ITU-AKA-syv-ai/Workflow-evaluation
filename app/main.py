from fastapi import FastAPI

from app.api import evaluate
from app.config.settings import get_settings

get_settings()  # We read the settings as the first thing to fail fast

app = FastAPI()

app.include_router(evaluate.router)
