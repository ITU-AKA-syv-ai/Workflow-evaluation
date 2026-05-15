FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Run as an unprivileged user (mostly to avoid Celery workers have sudo privileges).
# /app is pre-created with the right ownership so WORKDIR doesn't make it as
# root as that would force a recursive chown later, duplicating .venv into a
# new layer. --create-home is required because uv needs a writable $HOME.
RUN useradd --create-home --shell /bin/bash app \
    && mkdir /app \
    && chown app:app /app

WORKDIR /app
COPY --chown=app:app . /app

# Switch user before install so the venv is owned by app from the start.
USER app
RUN uv sync --frozen --no-cache

EXPOSE 8000

CMD ["/app/.venv/bin/fastapi", "run", "app/main.py", "--host", "0.0.0.0"]
