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
Currently the _api key_, _provider_, _model_, _api version_ and _api endpoint_ for the LLM set up is configured inside a `.env` file. This file is loaded by the `Settings` class, and all the environmental variables can be accessed through a settings instance. Please populate the following things in a `.env` file (otherwise refer to `.env.example`):
```
LLM_API_KEY="your_api_key"
LLM_PROVIDER="your_registered_provider"
LLM_MODEL="the_model"
LLM_API_ENDPOINT="the_api_endpoint"
LLM_API_VERSION="the_api_version"
```
