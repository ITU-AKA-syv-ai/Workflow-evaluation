# Workflow-evaluation

Run FastAPI app with
```
uv run fastapi dev
```

Run tests with
```
uv run pytest
```

# Example evaluation request

```
curl -X 'POST' \
  'http://127.0.0.1:8000/evaluate' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '[
    {
      "model_output": "Lorem Ipsum",
      "configs": [
        {
          "evaluator_id": "rule_based_evaluator",
          "weight": 1.0,
          "config": {
            "rules": [
              {
                "name": "keyword_check",
                "kind": "required",
                "keyword": "Ipsum",
                "weight": 1.0
              },
              {
                "name": "length_check",
                "kind": "max_length",
                "max_length": 20,
                "weight": 1.0
              }
            ]
          }
        }
      ]
    },
    {
      "model_output": "Hello World",
      "configs": [
        {
          "evaluator_id": "rule_based_evaluator",
          "weight": 1.0,
          "config": {
            "rules": [
              {
                "name": "keyword_forbidden",
                "kind": "forbidden",
                "keyword": "Helloo",
                "weight": 1.0
              },
              {
                "name": "regex_check",
                "pattern": "Hello",
                "weight": 1.0
              }
            ]
          }
        }
      ]
    }
]'
```

# Request to get all registered evaluators and their config schema
```
curl -X 'GET' \
  'http://127.0.0.1:8000/evaluators' \
  -H 'accept: application/json'
```
It will generate a response like:
```
[
  {
    "evaluator_id": "length_evaluator",
    "description": "Evaluates whether a string matches an expected length",
    "config_schema": {
      "properties": {
        "expected_length": {
          "title": "Expected Length",
          "type": "integer"
        }
      },
      "required": [
        "expected_length"
      ],
      "title": "LengthEvaluatorConfig",
      "type": "object"
    }
  }
]
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

# Architecture Diagrams
## Component diagram
![Component Diagram](docs/diagrams/abstractComponent.svg)
## Class diagram
![Overview of architecture](docs/diagrams/component.svg)
## Data Flow
![Data Flow Diagram](docs/diagrams/DataFlow.svg)
