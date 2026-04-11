### Database migrations
To run migrations, you need to configure a connection to a PostgreSQL server.
As the moment, everything runs locally so Postgres must be to be installed on your machine: https://www.postgresql.org/

You will need to complete the .env file using the .env.sample as a reference, filling in your local database server credentials accordingly.

#### Migrations
To apply migrations run
````
uv run alembic upgrade head
````

Remove one migration
````
uv run alembic downgrade -1
````

Generate new migrations after changes to models.py file
````
alembic revision --autogenerate -m "initial migration"
````