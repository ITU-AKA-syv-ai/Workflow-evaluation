# Workflow-evaluation

If you intend to use llm-as-judge evaluator, before running the app, add a .env file according to env.sample.
For now, only our own deployment is supported: gpt-5-nano-ITU-students

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
    "model_output": "hello",
    "configs": [
      {
        "evaluator_id": "rule_based_evaluator",
        "weight": 1.0,
        "config": {
          "rules": [
            {
              "name": "format",
              "kind": "max_length",
              "max_length": 10,
              "weight": 1.0
            }
          ]
        }
      }
    ]
  }
]'
```

# Example LLM request
```
[
  {
    "model_output": "Peel the banana from the bottom tip, pull the peel down in strips, and eat it in a few large bites for the fastest and least messy consumption.",
    "configs": [
      {
        "evaluator_id": "llm_judge",
        "config": {
          "prompt": "How can I eat bananas most efficiently?",
          "rubric" : [
            "correctness: is it correct?",
            "politeness: is it polite?"
          ]
        }
      }
    ]
  }
]
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

# Environment variables

All configuration is loaded from environment variables via `pydantic-settings`. For local development, copy `.env.example` to `.env` and fill in the values. The `.env` file is gitignored and must never be committed.

The app will fail fast at startup if any required variable is missing.

## Required variables

| Variable                 | Description                                                             |
|--------------------------|-------------------------------------------------------------------------|
| `ENVIRONMENT`            | `dev`, `staging`, or `production` (default: `dev`)                      |
| **LLM**                  |                                                                         |
| `LLM_PROVIDER`           | LLM provider name (must match a registered provider)                    |
| `LLM_API_KEY`            | API key for the LLM provider                                            |
| `LLM_API_ENDPOINT`       | API endpoint URL                                                        |
| `LLM_MODEL`              | Model name                                                              |
| `LLM_API_VERSION`        | API version                                                             |
| **Embedding**            |                                                                         |
| `EMBEDDING_API_KEY`      | API key for the embedding provider                                      |
| `EMBEDDING_API_ENDPOINT` | API endpoint URL                                                        |
| `EMBEDDING_MODEL`        | Model name                                                              |
| `EMBEDDING_API_VERSION`  | API version                                                             |
| **Similarity**           |                                                                         |
| `SIMILARITY_MAX_LENGTH`  | Maximum character length for similarity inputs                          |
| **Default thresholds**   |                                                                         |
| `THRESHOLD_ROUGE`        | Default pass threshold for ROUGE evaluator (default: `0.5`)             |
| `THRESHOLD_COSINE`       | Default pass threshold for cosine similarity evaluator (default: `0.7`) |
| `THRESHOLD_LLM_JUDGE`    | Default pass threshold for LLM judge evaluator (default: `1.0`)         |
| `THRESHOLD_RULE_BASED`   | Default pass threshold for rule-based evaluator (default: `1.0`)        |
| **Database**             |                                                                         |
| `DB_DRIVER`              | Database driver (e.g. postgresql+psycopg2)                              |
| `DB_HOST`                | Hostname or IP address of the database server                           |
| `DB_DATABASE`            | Name of the database                                                    |
| `DB_USERNAME`            | Username used for autentication                                         |
| `DB_PASSWORD`            | Passwork used for autentication                                         |

For production, set these variables directly in your deployment environment rather than using a `.env` file.
