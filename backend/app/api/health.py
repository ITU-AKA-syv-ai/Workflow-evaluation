from time import monotonic

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config.settings import get_settings
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


@router.get(
    "/ready",
    summary="Check application readiness",
    description="""
    Checks whether the application is ready to receive traffic.
    
    This endpoint performs health checks on required external dependencies:
    
    - Database connectivity via a simple test query (`SELECT 1`).
    - LLM provider availability via provider-specific health check.
    
    Returns:
    - status: "ok" if all components are available, otherwise "down".
    - uptime: Time in seconds since application startup.
    - components: Status of individual dependencies:
      - database: Connection status and optional error message if unavailable.
      - llm_provider: Provider availability status and optional error message if unavailable.
    """,
    response_model=dict[str, object],
    tags=["System"],
    responses={
        200: {
            "description": "All components are healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "uptime": 170.67,
                        "components": {"database": {"status": "ok"}, "llm_provider": {"status": "ok"}},
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "uptime": {"type": "number"},
                            "components": {
                                "type": "object",
                                "properties": {
                                    "database": {"type": "object", "properties": {"status": {"type": "string"}}},
                                    "llm_provider": {"type": "object", "properties": {"status": {"type": "string"}}},
                                },
                            },
                        },
                    },
                }
            },
        },
        500: {"description": "Unexpected error"},
        503: {"description": "One or more components are unavailable"},
    },
)
async def ready(request: Request) -> JSONResponse:
    """
    Check if the application is ready to receive traffic.
    Verifies database connectivity and returns component status.
    Verifies configured LLM provider is reachable.
    Args:
        request (Request): The incoming FastAPI request.
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
    llm_ok, llm_error = await check_llm_provider()

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


async def check_llm_provider() -> tuple[bool, str | None]:
    """Check if the LLM provder is reachable.
    Returns:
        tuple[bool, str | None]:
        - True and None if the LLM provider is reachable
        - False and an error message if the provider check fails
    """
    try:
        settings = get_settings()  # read config
        discover_providers()
        provider_class = get_provider(settings.llm.provider)
        provider = provider_class(settings)
        await provider.check_health()
        return True, None
    except Exception as e:
        return False, str(e)


@router.get(
    "/health",
    summary="Check application liveness",
    description="""
    Returns basic liveness information about the application.
    
    This endpoint is used to verify that the application is running.
    
    It does not perform any dependency checks (such as database or LLM provider health).
    
    Returns:
    - status: Always "ok" when the application is running.
    - uptime: Time in seconds since the application started.
    """,
    response_model=dict[str, str | float],
    tags=["System"],
    responses={
        200: {
            "description": "Application is running",
            "content": {
                "application/json": {
                    "example": {"status": "ok", "uptime": 136.09},
                    "schema": {
                        "type": "object",
                        "properties": {"status": {"type": "string"}, "uptime": {"type": "number"}},
                        "required": ["status", "uptime"],
                    },
                }
            },
        },
        500: {"description": "Unexpected error"},
    },
)
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
