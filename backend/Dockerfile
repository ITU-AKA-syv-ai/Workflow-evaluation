FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Run as an unprivileged user (mostly to avoid Celery workers running as root).
# /app is pre-created so WORKDIR doesn't make it root-owned -- a later recursive
# chown would duplicate .venv into a new layer. --create-home: uv needs $HOME.
RUN useradd --create-home --shell /bin/bash app \
    && mkdir /app \
    && chown app:app /app

WORKDIR /app
COPY --chown=app:app . /app

# Install as `app` so the venv is owned correctly from the start.
USER app
RUN uv sync --frozen --no-cache

EXPOSE 8000

CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--host", "0.0.0.0"]
