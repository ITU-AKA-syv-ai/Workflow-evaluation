from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.factory import create_app


def test_ready_returns_200_when_all_components_are_available() -> None:
    app = create_app()

    with (
        patch("app.api.health.check_database", return_value=(True, None)),
        patch("app.api.health.check_llm_provider", new=AsyncMock(return_value=(True, None))),
        TestClient(app) as client,
    ):
        response = client.get("/ready")

    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert "uptime" in body

    assert body["components"]["database"]["status"] == "ok"
    assert body["components"]["llm_provider"]["status"] == "ok"


def test_ready_returns_503_when_database_is_down() -> None:
    app = create_app()

    with (
        patch("app.api.health.check_database", return_value=(False, "db error")),
        patch("app.api.health.check_llm_provider", new=AsyncMock(return_value=(True, None))),
        TestClient(app) as client,
    ):
        response = client.get("/ready")

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "down"

    assert body["components"]["database"]["status"] == "down"
    assert body["components"]["database"]["error"] == "db error"

    assert body["components"]["llm_provider"]["status"] == "ok"


def test_ready_returns_503_when_llm_provider_is_down() -> None:
    app = create_app()

    with (
        patch("app.api.health.check_database", return_value=(True, None)),
        patch(
            "app.api.health.check_llm_provider",
            new=AsyncMock(return_value=(False, "llm error")),
        ),
        TestClient(app) as client,
    ):
        response = client.get("/ready")

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "down"

    assert body["components"]["database"]["status"] == "ok"

    assert body["components"]["llm_provider"]["status"] == "down"
    assert body["components"]["llm_provider"]["error"] == "llm error"


def test_ready_returns_503_when_all_components_are_down() -> None:
    app = create_app()

    with (
        patch("app.api.health.check_database", return_value=(False, "db error")),
        patch(
            "app.api.health.check_llm_provider",
            new=AsyncMock(return_value=(False, "llm error")),
        ),
        TestClient(app) as client,
    ):
        response = client.get("/ready")

    assert response.status_code == 503

    body = response.json()
    assert body["status"] == "down"

    assert body["components"]["database"]["status"] == "down"
    assert body["components"]["llm_provider"]["status"] == "down"
