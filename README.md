# Workflow Evaluation

This application is a backend service built in Python using UV.
Its purpose is to evaluate AI-generated outputs using multiple evaluation strategies, accessed through a REST API.

The system supports both synchronous and asynchronous evaluation workflows,
allowing evaluations to either return immediately or be processed in the background.

The application is designed to be extensible, making it possible to add new evaluators, evaluation strategies, and providers.

Currently supported evaluator types include:

- **LLM as Judge.** Uses an LLM to assess the quality of AI output based on subjective criteria like clarity, correctness, and completeness.

- **Rule-Based Evaluator.** Checks AI outputs against simple, predefined rules.
These rules can enforce things like required keywords, allowed formats, or matching patterns.

- **Cosine Similarity Evaluator.** Measures how semantically similar an AI generated output is to a given reference text.

- **ROUGE Evaluator.** Measures how much overlap there is between an AI generated output and a reference text.

You can find a comprehensive example sheet for all evaluators [here](docs/evaluation-examples.md).

The system also has a simple frontend built with `Vite`, `React` and `TypeScript`,
that displays an overview, a dashboard and details about previous evaluations.


# Getting Started

## Prerequisites

This application requires [Docker](https://www.docker.com/get-started/). Make sure it is installed and running before proceeding.

Docker can be installed either as a CLI (Command Line Interface) or as the Docker Desktop application.

Either will work but if you're using Docker CLI, you'll also need to install the [Docker Compose plugin](https://docs.docker.com/compose/install).


## 1. Download zip or Clone the Repository

Either download the project as a zip file from [here](https://github.com/ITU-AKA-syv-ai/Workflow-evaluation/archive/refs/heads/main.zip) and unzip it.

Or clone the repository using [git](https://git-scm.com/):
```
git clone https://github.com/ITU-AKA-syv-ai/Workflow-evaluation
```

Then open a terminal window on your computer and navigate to the project folder. E.g. `cd Workflow-evaluation` or `cd Workflow-evaluation-main`.


## 2. Setup Environment Variables

In the root of the project directory, you'll find a file called `.env.example`.
Create a copy of that file in the same folder and rename the copy `.env`.

This file contains values and settings required to run the application.

Open `.env` in a text editor i.e. Notepad for Windows or TextEdit for Mac.

Then, fill out all the variables in the file. You can refer to [this](#environment-variables) table for more information.
When running the application locally for development, set the ENVIRONMENT variable to `dev` at the very top of the `.env` file.


## 3. Run the App Using Docker

To start the app, use the Docker compose command below in the root of the project `\Workflow-evaluation` / `\Workflow-evaluation-main`

```
docker compose up
```

That's it! You should see the app starting up. It will take a minute or so before the app is ready to be used.

Whenever you want to stop the application, you can do so with:

```
docker compose down
```

And if you want to empty the database of any evaluations you may have run, add the `-v` flag:

```
docker compose down -v
```


## Using the Application

*Note: `<HOST>` means the IP address of the machine the application is running on.
If you are running the app locally and accessing it on the same device, your `<HOST>` will simply be `localhost`.*

Once the app has started you can view the status of the application by typing the following into your web browser of choice:

`<HOST>:8000/ready`

To use the application i.e. send and view evaluations, you can use the docs page provided by Swagger UI:

`<HOST>:8000/docs`

If you want to browse an overview, dashboard and details about previous evaluations, you can do so here:

`<HOST>:5173`


### Swagger UI docs page

The `/docs` page is an excellent tool to help you get started using the application.
There, you will find an overview and documentation of all API endpoints,
and you can experiment with your own evaluation requests and results.

If you have been following the guide and are running the app locally in a `dev` environment,
you need to get authorised before you can send evaluations.

1. Open `http://localhost:8000/docs`.
2. Go to the `/dev/token` endpoint.
3. Click "Try it out" and "Execute"
4. In the response body, copy the value of `"access_token"` to your clipboard.
5. At the top of the page, click on the "Authorize" button and paste the value you just copied. 

Now you should be able to send and browse evaluations through Swagger directly.

*Note: If the token is rejected as invalid or the frontend doesn't load, try clearing your browser's
cache for localhost.*


#### How to Send an Evaluation Request

1. On the Swagger `/docs` page, expand the section with the POST `/evaluations` endpoint.
2. Click on the "Try it out" button.
3. An input field will appear. Here you can write your evaluation request. It comes pre-filled with an example.
4. Click "Execute".
5. Once the evaluation has completed, the result will be visible in the field called "Response body".

You can find examples on how to construct requests for all evaluators [here](docs/evaluation-examples.md).


#### How to Browse Previous Evaluations

1. On the Swagger `/docs` page, expand the section with the GET `/evaluations` endpoint.
2. Click on the "Try it out" button.
3. A "Parameters" section will appear with a wide range of filters and sorting to choose from.
4. Once you have applied the filters sorting you want, click "Execute".
5. The result(s) will be visible in the field called "Response body".


### Calling the API directly

It is generally recommended that you use the Swagger `/docs` page and [evaluation-examples.md](docs/evaluation-examples.md) to familiarise yourself with the API,
as shown in the previous section.
A direct call to the application from a terminal might look something like this:

```
curl -X 'POST' \
  'http://127.0.0.1:8000/evaluations' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer <your-token> \
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


# Development

## Ports Overview

Here is an overview of the ports that the application uses.

- `8000`: FastAPI backend
- `5173`: Frontend (dev mode)
- `8080`: Frontend (served with nginx in production)
- `5050`: pgAdmin (only accessible in dev mode)
- `9999`: Dozzle (only accessible in dev mode)


## Running the App Without Docker

You *can* run the backend and frontend in isolation without using Docker, but it is not recommended for most users.

If you wish to do so anyway e.g. for development purposes, you need to have Python and UV installed for the backend to work.
Project dependencies can be installed using `uv sync` in the `/backend` directory.
Then, run the backend with `uv run fastapi dev`.

For the frontend, you need to install bun and then run `bun install` in the `/frontend` directory to install dependencies.
Then use `bun run dev --hot` to run the frontend.

*Note: In production the frontend is served with nginx.*

Each containerised service should be available at different ports on the `localhost` domain.
This means that it is possible to stop a service and run it locally but still have it interact with the Docker container.
For example, you could stop the backend:
```
docker compose stop workflow-evaluation-backend-1
```
And then run
```
cd backend
uv run fastapi dev
```
Please note that this may require changing the environment variables.


## Docker Compose Override

During development, it is possible to change Docker Compose settings that wil only affect the local development environment
by updating the file [compose.override.yaml](./compose.override.yaml). Changes to this file will not have any effect on the deployment environment.


## Docker Hot Reloading

You can use the `--watch` flag to live-synchronise changes to the `/frontend/src` and `./backend` directory
directly into the container rather than having to re-run `docker compose up` for every small change.
Settings are specified in the [compose.override.yaml](./compose.override.yaml) file.

```
docker compose up --watch
```

## Logging and Monitoring

Logs are served through the Docker containers and can be inspected like so:

```
docker compose logs
docker compose logs <service_name>
```
*Replace <service_name> with the name of the container you wish to inspect.*

In dev mode, you can also utilize Dozzle on port `9999`.
A simple visualisation tool for logging and monitoring.

## Migrations

To run migrations you must start an interactive session in the backend container:
```
$ docker compose exec <name_of_backend_container> bash
```

After changing a model, inside the container, you can create the revision with:
```
uv run alembic revision --autogenerate -m "Added column to EasterEgg"
```

After creating the revision, run the migration in the database:
```
uv run alembic upgrade head
```

To remove a migration run:
```
uv run alembic downgrade -1
```

*PLEASE NOTE: The migrations folder inside the container is not mounted as a volume.  
This means changes made inside the container will **NOT** be reflected in the migrations folder on your local machine.*


# Testing

The project includes both unit and integration tests for the backend application,
which can be run with the command below from the `/backend` directory. 
```
uv run pytest
```


# System Architecture

The folder structure of the application is as follows:

```
Workflow-evaluation/
├─ backend/                 # Source code for the backend
│  ├─ app/
│  │  ├─ main.py            # Router setup
│  │  ├─ api/               # Handlers for each endpoint
│  │  ├─ core/              # The core app logic
│  │  │  ├─ services/       # Services which the endpoint handlers call
│  │  │  ├─ models/         # Data models which the services use
│  │  │  ├─ evaluators/     # Logic for evaluators
│  │  │  ├─ providers/      # LLM provider classes
│  │  ├─ config/            # Config files
│  ├─ tests/
├─ frontend/
│  ├─ src/                  # Source code for the frontend
```

## Architecture Diagrams

### Component diagram
![Component Diagram](docs/diagrams/abstractComponent.svg)

### Class diagram
![Overview of architecture](docs/diagrams/component.svg)

### Data Flow
![Data Flow Diagram](docs/diagrams/DataFlow.svg)


# Environment Variables 

All configurations are loaded via pydantic-settings. The app will fail at startup if any required variables are missing.
Please see [.env.example](.env.example) for an example `.env` file and refer to the table below for explanations and example/default values.

| Variable                 | Description                                                           | Example / Default                                  |
|--------------------------|-----------------------------------------------------------------------|----------------------------------------------------|
| `ENVIRONMENT`            | What environment the application should run in                        | `dev`, `staging`, or `production` (default: `dev`) |
| **LLM**                  |                                                                       |                                                    |
| `LLM_PROVIDER`           | LLM provider name (must match a registered provider)                  | `azure`                                            |
| `LLM_API_KEY`            | API key for the LLM provider                                          | Usually a long string of numbers and letters.      |
| `LLM_API_ENDPOINT`       | API endpoint URL                                                      | `https://api.openai.com/v1`                        |
| `LLM_MODEL`              | Model name                                                            | `gpt-4.1-mini`                                     |
| `LLM_API_VERSION`        | API version                                                           | `2024-02-01`                                       |
| **Embedding**            |                                                                       |                                                    |
| `EMBEDDING_API_KEY`      | API key for the embedding provider                                    | Usually a long string of numbers and letters.      |
| `EMBEDDING_API_ENDPOINT` | API endpoint URL                                                      | `https://api.openai.com/v1`                        |
| `EMBEDDING_MODEL`        | Model name                                                            | `text-embedding-3-small`                           |
| `EMBEDDING_API_VERSION`  | API version                                                           | `2024-02-01`                                       |
| **Similarity**           |                                                                       |                                                    |
| `SIMILARITY_MAX_LENGTH`  | Maximum character length for similarity inputs                        | `2400`                                             |
| **Default thresholds**   |                                                                       |                                                    |
| `THRESHOLD_ROUGE`        | Default pass threshold for ROUGE evaluator                            | `0.5`                                              |
| `THRESHOLD_COSINE`       | Default pass threshold for cosine evaluator                           | `0.7`                                              |
| `THRESHOLD_LLM_JUDGE`    | Default pass threshold for LLM judge evaluator                        | `1.0`                                              |
| `THRESHOLD_RULE_BASED`   | Default pass threshold for rule-based evaluator                       | `1.0`                                              |
| **Default timeouts**     |                                                                       |                                                    |
| `TIMEOUT_ROGUE`          | Default timeout for ROUGE evaluator in seconds                        | `5`                                                |
| `TIMEOUT_COSINE`         | Default timeout for cosine evaluator in seconds                       | `5`                                                |
| `TIMEOUT_LLM_JUDGE`      | Default timeout for LLM judge evaluator in seconds                    | `30`                                               |
| `TIMEOUT_RULE_BASED`     | Default timeout for rule-based evaluator in seconds                   | `3`                                                |
| **Logging**              |                                                                       |                                                    |
| `LOG_LEVEL`              | Controls how detailed the logs should be                              | `DEBUG`, `INFO`, `WARNING`, `ERROR`                |
| **Database**             |                                                                       |                                                    |
| `DB_DRIVER`              | Database driver                                                       | `postgresql+psycopg`                               |
| `DB_HOST`                | Hostname or IP address of the database server                         | `database`                                         |
| `DB_DATABASE`            | Name of the database                                                  | `postgres`                                         |
| `DB_USERNAME`            | Username used for autentication                                       | `postgres`                                         |
| `DB_PASSWORD`            | Password used for autentication                                       | `supersecurepassword3160`                          |
| **PGAdmin**              |                                                                       |                                                    |
| `PGADMIN_MAIL`           | Default email-adress for pgadmin                                      | `admin@example.com`                                |
| `PGADMIN_PW`             | Default password for pgadmin                                          | `admin`                                            |
| **Redis**                |                                                                       |                                                    |
| `REDIS_HOST`             | Hostname/IP of the Redis instance used as the Celery message broker   | `redis`                                            |
| `REDIS_PORT`             | The port exposed by the redis instance                                | `6379`                                             |
| **Celery**               |                                                                       |                                                    |
| `CELERY_BACKEND_URL`     | Optional override for Celery to use a different backend for testing   | `cache+memory://`                                  |
| **JWT Token**            |                                                                       |                                                    |
| `JWT_ISSUER`             | Identifier for who issued the JWT                                     | `my-auth-server`                                   |
| `JWT_AUDIENCE`           | Identifier for who the JWT is intended for                            | `my-api`                                           |
| `JWT_SECRET`             | String used to verify that the JWT has not been changed along the way | Usually a long string of numbers and letters.      |
| `JWT_JWKS_URL`           | Url to help verify signature of JWT                                   | `https://example.com/.well-known/jwks.json`        |
| `JWT_ALGORITHM`          | Algorithm used to encode JWT                                          | `HS256`                                            |
| **CORS**                 |                                                                       |                                                    |
| `CORS_ALLOWED_ORIGINS`   | A comma separated string of allowed origins                           | `http://localhost:8000, http://localhost:5173`     |


*Note: If you make changes to the `.env` file you must restart the application for the changes to take effect.*

## License
Licensed under the terms of the MIT license. Please see [LICENSE](./LICENSE).
