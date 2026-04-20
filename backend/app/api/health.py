from time import monotonic

from fastapi import APIRouter, Request

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health(request: Request) -> dict[str, str | float]:
    return {
        "status": "ok",
        "uptime": round(monotonic() - request.app.state.started_at, 2),
    }

@router.get("/ready")
async def readiness() -> dict:
    try:
        # something with DB here
        await db.async_execute("SELECT 1")
        return {"status" : "ok"}
    except Exception:
        return {"status" : "error"}