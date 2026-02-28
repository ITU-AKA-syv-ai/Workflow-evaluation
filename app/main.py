from api import hello_world
from fastapi import FastAPI

app = FastAPI()
# Don't add endpionts in main directly
# Always add endpoints via the router
app.include_router(hello_world.router, prefix="/hello_world")


@app.get("/")
def index() -> dict[str, str]:
    return {"Message": "Use /hello_world/"}


def main() -> None:
    print("Hello from workflow-evaluation!")


if __name__ == "__main__":
    main()
