from fastapi import FastAPI
import asyncio

from app.api import hello_world

app = FastAPI()
# Don't add endpionts in main directly
# Always add endpoints via the router
app.include_router(hello_world.router, prefix="/hello_world")

@app.get("/")
def index() -> dict[str, str]:
    return {"Message": "Use /hello_world/"}

async def main() -> None:
    print("Hello from workflow-evaluation!")

if __name__ == "__main__":
    asyncio.run(main())
