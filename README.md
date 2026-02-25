# Workflow-evaluation

Run FastAPI app with
```
uv run fastapi dev
```

Run unit tests with
```
uv run pytest
```

# Architecture

```
Workflow-evaluation/
├── app/
│ ├── main.py # Router setup
│ ├── api/ # Handlers for each endpoint
│ ├── core/ # The core app logic
│ │ ├── services/ # Services which the endpoint handlers call
│ │ └── models/ # Data models which the services use
│ └── config/ # Config files
```
