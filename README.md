# Workflow-evaluation

If you intend to use llm-as-judge evaluator, before running the app, add a .env file according to env.sample.
For now, only our own deployment is supported: gpt-5-nano-ITU-students

Run FastAPI app with
```
uv run --env-file .env fastapi dev
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
          "evaluator_id": "substring_evaluator",
          "weight": 0.8,
          "config": {
            "substring": "sum"
          }
        },
        {
          "evaluator_id": "length_evaluator",
          "weight": 0.4,
          "config": {
            "expected_length": 5
          }
        }
      ]
    },
    {
      "model_output": "Hello World",
      "configs": [
        {
          "evaluator_id": "substring_evaluator",
          "weight": 1,
          "config": {
            "substring": "Helloo"
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
