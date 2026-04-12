import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions import EvaluationError

logger = logging.getLogger(__name__)


def evaluation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, EvaluationError)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
