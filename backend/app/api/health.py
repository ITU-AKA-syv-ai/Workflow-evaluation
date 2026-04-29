from time import monotonic
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config.settings import Settings, get_settings
from app.core.providers.provider_registry import discover_providers, get_provider
from app.db import get_engine

router = APIRouter()


def check_database() -> tuple[bool, str | None]:
    """Check if the database is reachable.
    Returns:
        tuple[bool, str | None]:
        - True and None if the database is reachable
        - False and an error message if the connection fails
    """
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        return False, str(e)


async def check_llm_provider(settings: Settings) -> tuple[bool, str | None]:
    """Check if the LLM provider is reachable.
    Returns:
        tuple[bool, str | None]:
        - True and None if the LLM provider is reachable
        - False and an error message if the provider check fails
    """
    try:
        discover_providers()
        provider_class = get_provider(settings.llm.provider)
        provider = provider_class(settings)
        await provider.check_health()
        return True, None
    except Exception as e:
        return False, str(e)


@router.get("/health")
async def health(request: Request) -> dict[str, str | float]:
    """
    Check if the application is running.

    Args:
        request (Request): The incoming FastAPI request.
    Returns:
        dict[str, str | float]:
        A JSON response containing information about the health of the application:
        - status: "ok" if the application is running
        - uptime: time since application startup
    """
    return {
        "status": "ok",  # return 200 OK when application is running
        "uptime": round(
            monotonic() - request.app.state.started_at, 2
        ),  # time application was started subtracted from present time rounded to  2 digits
    }


@router.get("/ready")
async def ready(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> JSONResponse:
    """
    Check if the application is ready to receive traffic.
    Verifies database connectivity and returns component status.
    Verifies configured LLM provider is reachable.
    Args:
        request (Request): The incoming FastAPI request.
        settings (Settings): Application settings, injected via DI so tests can
            override them.
    Returns:
        JSONResponse:
        - 200 OK if all components are available
        - 503 Service Unavailable if all or some components are unavailable

        Response body contains:
        - status: "ok" or "down"
        - uptime: time since application startup
        - components: status of individual components
    """

    db_ok, db_error = check_database()
    llm_ok, llm_error = await check_llm_provider(settings)

    payload = {
        "status": "ok" if db_ok and llm_ok else "down",  # return 200 OK when database and llm provider is ok
        "uptime": round(monotonic() - request.app.state.started_at, 2),
        "components": {
            "database": {
                "status": "ok" if db_ok else "down",
                **({"error": db_error} if db_error else {}),
            },
            "llm_provider": {
                "status": "ok" if llm_ok else "down",
                **({"error": llm_error} if llm_error else {}),
            },
        },
    }
    return JSONResponse(
        status_code=200 if db_ok and llm_ok else 503,
        content=payload,
    )
