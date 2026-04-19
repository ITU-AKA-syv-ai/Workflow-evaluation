#!/usr/bin/env bash
set -e
set -x

echo "Lmao"

uv run backend_prestart.py

uv run alembic upgrade head
