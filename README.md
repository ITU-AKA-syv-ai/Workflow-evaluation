# Workflow-evaluation

Run FastAPI app with
```
uv run fastapi dev
```

Run unit tests with
```
uv run pytest
```

# Example evaluation request

```

curl -X 'POST' \
  'http://127.0.0.1:8000/evaluate/' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "output": "Lorem Ipsum",
  "evaluator_id": "length_evaluator",
  "config": {
    "expected_length": 11
  }
}'

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
