# Workflow-evaluation

## Prerequisites
- `uv` (for local development and dependency management)
- `bun` (also for local development and dependency management)
- `Docker` (for containerized deployment)

## Configuration
Before running the aplication, you must configure your environment variables.
1. Copy the example environment file `.env.example` into a file named `.env`
2. Fill in the required values (please see the **environment variables** section below) 

## Running the Application
The recommended way of running the aplication is using `Docker`:
```
docker compose up --build
```
It is also possible to run the application outside of Docker, but naturally it requires you to have a `postgresql` server running locally on your machine.

## Local development
To run the application with hot-reloading enabled, use Docker Compose with the watch flag. This will automatically sync your code changes to the container:
```
docker compose up --build --watch
```
Please note that we use `compose.override.yaml` to spin up development-specific infrastructure (like pgadmin) and expose the ports to more containers than done in `compose.yaml`.

The test suite can be run both in and outside of `Docker` using the command:
```
uv run pytest
```

## Environment Variables
All configuration is loaded via pydantic-settings. The app will fail fast at startup if any required variable is missing.

| Variable                 | Description                                                            |
|--------------------------|------------------------------------------------------------------------|
| `ENVIRONMENT`            | `dev`, `staging`, or `production` (default: `dev`)                     |
| **LLM**                  |                                                                        |
| `LLM_PROVIDER`           | LLM provider name (must match a registered provider)                   |
| `LLM_API_KEY`            | API key for the LLM provider                                           |
| `LLM_API_ENDPOINT`       | API endpoint URL                                                       |
| `LLM_MODEL`              | Model name                                                             |
| `LLM_API_VERSION`        | API version                                                            |
| **Embedding**            |                                                                        |
| `EMBEDDING_API_KEY`      | API key for the embedding provider                                     |
| `EMBEDDING_API_ENDPOINT` | API endpoint URL                                                       |
| `EMBEDDING_MODEL`        | Model name                                                             |
| `EMBEDDING_API_VERSION`  | API version                                                            |
| **Similarity**           |                                                                        |
| `SIMILARITY_MAX_LENGTH`  | Maximum character length for similarity inputs                         |
| **Default thresholds**   |                                                                        |
| `THRESHOLD_ROUGE`        | Default pass threshold for ROUGE evaluator (default: `0.5`)            |
| `THRESHOLD_COSINE`       | Default pass threshold for cosine similarity evaluator (default: `0.7`) |
| `THRESHOLD_LLM_JUDGE`    | Default pass threshold for LLM judge evaluator (default: `1.0`)        |
| `THRESHOLD_RULE_BASED`   | Default pass threshold for rule-based evaluator (default: `1.0`)       |
| **Database**             |                                                                        |
| `DB_DRIVER`              | Database driver (e.g. `postgresql+psycopg`)                            |
| `DB_HOST`                | Hostname or IP address of the database server (e.g. `localhost`)       |
| `DB_DATABASE`            | Name of the database (default: `postgres`)                             |
| `DB_USERNAME`            | Username used for autentication (default: `postgres`)                  |
| `DB_PASSWORD`            | Password used for autentication                                        |
| **PGAdmin (Optional)**   |                                                                        |
| `PGADMIN_MAIL`           | Default email-adress for pgadmin                                       | 
| `PGADMIN_PW  `           | Default password for pgadmin                                           |


## API Usage Examples
### Run an Evaluation
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

### Run an Evaluation with the LLM as a judge strategy
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

### Get registered evaluators
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

## Architecture

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

## Architecture Diagrams
### Component diagram
![Component Diagram](docs/diagrams/abstractComponent.svg)
### Class diagram
![Overview of architecture](docs/diagrams/component.svg)
### Data Flow
![Data Flow Diagram](docs/diagrams/DataFlow.svg)

