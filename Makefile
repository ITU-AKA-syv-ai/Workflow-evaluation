lint:
	uv run ruff check

fix:
	uv run ruff check --fix

format:
	uv run ruff format 

test:
	uv run pytest -v

type:
	uv run ty check

run:
	uv run fastapi dev
