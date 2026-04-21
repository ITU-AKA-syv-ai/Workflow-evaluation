from backend.app.core.providers.provider_registry import discover_providers
from backend.app.config.settings import get_settings
from time import monotonic

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db import get_engine

router = APIRouter(tags=["health"])


def check_database() -> tuple[bool, str | None]:
    """Check if the database is up and running."""  # todo: update docstring
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        return False, str(e)


def check_llm_provder() -> tuple[bool, str | None]:
    """Check if the LLM provder is up and running.""" # todo:update docstronmg
    try:
        settings = get_settings()
        discover_providers()
        provider_cls = get_provider(settings.llm.provider)
        provider = provider_cls(settings)
        return True, None
    except Exception as e:
        return False, str(e)


@router.get("/health")
async def health(request: Request) -> dict[str, str | float]:
    """
    Check if the application is running.

    Args:
        request: The incoming FastAPI request.
    Returns:
        response: health information including status and uptime.
        """
    return {
        "status": "ok",  # return 200 OK when application is running
        "uptime": round(monotonic() - request.app.state.started_at, 2),  # time application was started subtracted from present time rounded to  2 digits
    }


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    """
    Check if the application is ready to receive traffic.
    Verifies database connectivity and returns component status.
    Args:
        request: The incoming FastAPI request.
    Returns:
        response: health information including status and uptime. #todo: update
    """

    db_ok, db_error = check_database()
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return JSONResponse({
            "status": "ok",  # return 200 OK when database is available
                "uptime": round(monotonic() - request.app.state.started_at, 2),
                "components": {
                    "database": {
                        "status": "ok",  # todo: add component of LLM provider
                    }
                },
        },
        )
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,  # return 503 if DB or external dependencies cannot be reached
            content={
                "status": "down",
                "uptime": round(monotonic() - request.app.state.started_at, 2),
                "components": {
                    "database": {
                        "status": "down",
                        "error": str(e),
                    }
                },
            },

        )