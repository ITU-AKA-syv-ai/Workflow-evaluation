# Development

## Docker Compose
Start the application using docker compose:
```
docker compose up --watch
```
The `--watch` flags synchronizes changes to the [./frontend/src/](./frontend/src/) and [./backend/](./backend/) directly into the container enabling quicker development. These settings are specificed in the [./compose.override.yaml](./compose.override.yaml) file.

After entering the command you should be able to interact with the following links:

- `localhost:8000`: The fastapi backend
- `localhost:5173`: The frontend
- `localhost:5050`: Pgadmin

If you want to check the logs for a service or for the entire thing run either:
```
docker compose logs
docker compose logs <service_name>
```

## Local Development
Each service should be available at different ports on the `localhost` domain. This means that it is possible to stop a service and run it locally but still have it interact with the docker-container. As an example you could stop the backend:
```
docker compose stop workflow-evaluation-backend-1
```
And then run
```
cd backend
uv run fastapi dev
```
Please note that this may require changing things in the `.env` file.

## Environment variables 
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
| **PGAdmin                |                                                                        |
| `PGADMIN_MAIL`           | Default email-adress for pgadmin                                       | 
| `PGADMIN_PW  `           | Default password for pgadmin                                           |


If you make changes to the `.env` you must restart docker.
