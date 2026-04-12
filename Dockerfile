FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Copy the application into the container.
COPY . /app

# Install the application dependencies.
WORKDIR /app
RUN uv sync --frozen --no-cache

# Run the application.
CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--host", "0.0.0.0"]