from time import monotonic
from fastapi import APIRouter, Request

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health(request: Request) -> dict:[str, str | float]:
    return {
        "status": "ok"
        "uptime": round(monotonic() - request.app.state.started_at, 2), #this will not work until added in app
    }