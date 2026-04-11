### Database migrations
You need to have Postgres installed locally: https://www.postgresql.org/
And filled out the .env file according to the .env.sample and your local database server

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