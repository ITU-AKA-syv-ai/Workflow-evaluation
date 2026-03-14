from fastapi import FastAPI

from app.api import evaluate, hello_world

app = FastAPI()
# Don't add endpoints in main directly
# Always add endpoints via the router
app.include_router(hello_world.router, prefix="/hello_world")
app.include_router(evaluate.router)


@app.get("/")
def index() -> dict[str, str]:
    return {"Message": "Use /hello_world/"}


def main() -> None:
    print("Hello from workflow-evaluation!")


if __name__ == "__main__":
    main()
