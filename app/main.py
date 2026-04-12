from fastapi import FastAPI

from app.api import evaluate, hello_world
from app.api.exception_handler import evaluation_error_handler, internal_error_handler
from app.exceptions import EvaluationError

app = FastAPI()
# Don't add endpoints in main directly
# Always add endpoints via the router
app.include_router(hello_world.router, prefix="/hello_world")
app.add_exception_handler(EvaluationError, evaluation_error_handler)
app.add_exception_handler(Exception, internal_error_handler)
app.include_router(evaluate.router)
