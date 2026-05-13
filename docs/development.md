# Development

## Docker Compose
Start the application using docker compose:
```
docker compose up --watch
```
The `--watch` flags synchronizes changes to the [./frontend/src/](./frontend/src/) and [./backend/](./backend/) directly into the container enabling quicker development. These settings are specificed in the [./compose.override.yaml](../compose.override.yaml) file.

After entering the command you should be able to interact with the following links:

- `localhost:8000`: The fastapi backend
- `localhost:5173`: The frontend
- `localhost:5050`: Pgadmin

If you want to check the logs for a service or for the entire thing run either:
```
docker compose logs
docker compose logs <service_name>
```

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

## Environment Variables 

All configuration is loaded via pydantic-settings. The app will fail fast at startup if any required variable is missing. Please see [.env.example](../.env.example) for an example `.env` file. Below are the environment variables also:

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


*Note: If you make changes to the `.env` file you must restart docker.*
