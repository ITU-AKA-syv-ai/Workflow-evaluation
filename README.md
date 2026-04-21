# Workflow-evaluation

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

## Backend Development
Please see [./backend/README.md](./backend/README.md)

## Frontend Development
Please see [./frontend/README.md](./frontend/README.md)

## Development
Please see [./development.md](./development.md)

## Deployment
Currently there is no guide to deploying the application.

## License
Licensed under the terms of the MIT license. Please see [./LICENSE](./LICENSE).
