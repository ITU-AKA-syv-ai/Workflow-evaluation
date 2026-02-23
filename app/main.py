from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def index():
    return {"Message": "Hello, World!"}

def main():
    print("Hello from workflow-evaluation!")


if __name__ == "__main__":
    main()
