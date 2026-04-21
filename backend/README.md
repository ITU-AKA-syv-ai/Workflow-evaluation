# Backend

## Requirements
- `Docker`
- `uv`

## Docker Compose
Start the local development environment with Docker Compose following the guide in [../development.md](../development.md)

## Workflow
Dependencies are managed with `uv`. From this directory you can install dependencies with
```
uv sync
```

## Docker Compose Override
During development it is possible to change Docker Compose settings that wil only affect the local development environment by updating the file [../compose.override.yaml](../compose.override.yaml). Changes to this file will not have any effect on the deployment environment.

## Tests
You can run the backend tests with the command:
```
uv run pytest
```

## Migrations
To run migrations you must start an interative session in the backend container:
```
$ docker compose exec <name_of_backend_container> bash
```
After changing a model, inside the container, you can create the revision with:
````
uv run alembic revision --autogenerate -m "Added column to EasterEgg"
````

After creating the revision, run the migration in the database:
````
uv run alembic upgrade head
````
To remove a migration run
````
uv run alembic downgrade -1
````
**PLEASE NOTE: ** The migrations folder inside the container is not mounted as a volume. This means changes done inside the container WILL **NOT** modify the migrations folder on your computer.
