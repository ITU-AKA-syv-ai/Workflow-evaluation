### How to configure your database
1. Install PostgresSQL from: https://www.postgresql.org/
2. Run `uv sync`
3. Fill out .env file according to the `.env.sample` and `README.md`
   4. Credentials can be found by opening pgAdmin which was installed alongside PostgresSQL 
   5. Go to servers -> PostgreSQL and under the `connection` heading to the right you will be able to view the servers credentials
6. Run `uv run alembic upgrade head`
   7. You should now in pgAdmin be able to find the table(s) defined in `models.py`. Go to Server -> PostgreSQL -> Databases -> [your username] -> Tables

### Database migrations
To run migrations, you need to configure a connection to a PostgreSQL server.
As the moment, everything runs locally so Postgres must be to be installed on your machine (see above)

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
uv run alembic revision --autogenerate -m "initial migration"
````