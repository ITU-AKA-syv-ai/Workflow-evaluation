from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def index() -> dict[str, str]:
    return {"Message": "Hello, World!"}

def main() -> None:
    print("Hello from workflow-evaluation!")


if __name__ == "__main__":
    main()
