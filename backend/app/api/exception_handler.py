import logging

from fastapi import Request
from fastapi.responses import JSONResponse

from app.exceptions import EvaluationError

logger = logging.getLogger(__name__)


def evaluation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle EvaluationError exceptions by returning the error's status code and message.

    Args:
        request: The incoming FastAPI request.
        exc: The raised exception, expected to be an EvaluationError instance.

    Returns:
        A JSONResponse with the error's status code and detail message.
    """
    assert isinstance(exc, EvaluationError)
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )


def internal_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handle unexpected exceptions by logging them and returning a 500 response.

    Args:
        request: The incoming FastAPI request.
        exc: The unhandled exception.

    Returns:
        A JSONResponse with status code 500 and a generic error message.
    """
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
