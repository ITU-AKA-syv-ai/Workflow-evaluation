from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

from celery import Celery
from fastapi.testclient import TestClient

from app.config.settings import get_settings
from app.factory import create_app
from tests.conftest import TestSettings


@contextmanager
def _build_health_client(
    db_check: tuple[bool, str | None],
    llm_check: tuple[bool, str | None],
) -> Generator[TestClient, None, None]:
    """
    Yields a TestClient with the patches needed to exercise the /ready endpoint
    in isolation:

    - Factory/settings/celery patches so create_app() can run without real env
      vars or a real broker (mirrors the pattern in _build_test_client).
    - Health-check stubs for the database and LLM provider, returning the
      supplied (ok, error) tuples.
    """
    get_settings.cache_clear()
    test_settings = TestSettings()

    with (
        patch("app.factory.get_settings", return_value=test_settings),
        patch("app.factory.get_celery_app", return_value=Celery("test")),
        patch("app.api.health.get_settings", return_value=test_settings),
        patch("app.api.health.check_database", return_value=db_check),
        patch("app.api.health.check_llm_provider", new=AsyncMock(return_value=llm_check)),
    ):
        app = create_app()
        with TestClient(app) as client:
            yield client


def test_ready_returns_200_when_all_components_are_available() -> None:
    with _build_health_client(db_check=(True, None), llm_check=(True, None)) as client:
        response = client.get("/ready")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert "uptime" in body

    assert body["components"]["database"]["status"] == "ok"
    assert body["components"]["llm_provider"]["status"] == "ok"


def test_ready_returns_503_when_database_is_down() -> None:
    with _build_health_client(db_check=(False, "db error"), llm_check=(True, None)) as client:
        response = client.get("/ready")

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "down"

    assert body["components"]["database"]["status"] == "down"
    assert body["components"]["database"]["error"] == "db error"

    assert body["components"]["llm_provider"]["status"] == "ok"


def test_ready_returns_503_when_llm_provider_is_down() -> None:
    with _build_health_client(db_check=(True, None), llm_check=(False, "llm error")) as client:
        response = client.get("/ready")

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "down"

    assert body["components"]["database"]["status"] == "ok"

    assert body["components"]["llm_provider"]["status"] == "down"
    assert body["components"]["llm_provider"]["error"] == "llm error"


def test_ready_returns_503_when_all_components_are_down() -> None:
    with _build_health_client(db_check=(False, "db error"), llm_check=(False, "llm error")) as client:
        response = client.get("/ready")

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "down"

    assert body["components"]["database"]["status"] == "down"
    assert body["components"]["llm_provider"]["status"] == "down"
