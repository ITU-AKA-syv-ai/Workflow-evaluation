from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def hello_world() -> dict[str, Any]:
    return {"Message": "Hello, World!"}


@router.post("/")
async def echo(msg: str | None) -> dict[str, Any]:
    if msg is not None:
        return {"Echo": msg}
    return {"Echo": "<Nothing>"}
