from time import monotonic
from typing import Any

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db import get_engine

router = APIRouter(tags=["health"])


@router.get("/health")
async def health(request: Request) -> dict[str, str | float]:
    """Check if the application is running."""
    return {
        "status": "ok",
        "uptime": round(monotonic() - request.app.state.started_at, 2),
    }


@router.get("/ready")
async def ready(request: Request) -> dict[str, Any] | JSONResponse:
    """
    Check if the application is ready to receive traffic.
    Verifies database connectivity and returns component status.
    """
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok",
                "uptime": round(monotonic() - request.app.state.started_at, 2),
                "components": {
                    "database": {
                        "status": "ok",
                    }
                },
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,  # return 503 if DB cannot be reached
            content={
                "status": "error",
                "uptime": round(monotonic() - request.app.state.started_at, 2),
                "components": {
                    "database": {
                        "status": "down",
                        "error": str(e),
                    }
                },
            },

        )