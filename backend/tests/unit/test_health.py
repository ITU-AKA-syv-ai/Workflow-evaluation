from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

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

    - ``get_settings`` is overridden via FastAPI DI so the route handler injects
      a TestSettings instance instead of reading the real config.
    - ``check_database`` and ``check_llm_provider`` are stubbed at module level
      because they're free functions called directly by the route, not DI
      dependencies.
    """
    test_settings = TestSettings()

    with (
        patch("app.api.health.check_database", return_value=db_check),
        patch("app.api.health.check_llm_provider", new=AsyncMock(return_value=llm_check)),
    ):
        app = create_app()
        app.dependency_overrides[get_settings] = lambda: test_settings
        with TestClient(app) as client:
            yield client
        app.dependency_overrides.clear()


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
