lint:
	uv run ruff check

fix:
	uv run ruff check --fix

format:
	uv run ruff format 

test:
	uv run pytest -v

test-with-coverage:
    uv run pytest --cov

test-with-coverage-report:
    uv run pytest --cov --cov-report=html:coverage_re

type:
	uv run ty check

run:
	uv run fastapi dev
