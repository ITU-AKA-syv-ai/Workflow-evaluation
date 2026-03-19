lint:
	uv run ruff check

fix:
	uv run ruff check --fix

format:
	uv run ruff format 

test:
	uv run pytest -v
    uv run pytest --cov
    uv run pytest --cov --cov-report=html:coverage_re

type:
	uv run ty check

run:
	uv run fastapi dev
