from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def hello_world() -> dict[str, str]:
    return {"Message": "Hello, World!"}


@router.post("/")
async def echo(msg: str | None) -> dict[str, str]:
    if msg is not None:
        return {"Echo": msg}
    return {"Echo": "<Nothing>"}
