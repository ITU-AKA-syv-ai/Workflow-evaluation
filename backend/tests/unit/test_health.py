from unittest.mock import patch

from fastapi.testclient import TestClient

from app.factory import create_app


class WorkingConnection:
    def __enter__(self):  # noqa: ANN204
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001, ANN204
        return False

    def execute(self, _query) -> None:  # noqa: ANN001
        return None


class WorkingEngine:
    def connect(self):  # noqa: ANN201
        return WorkingConnection()


def test_health_returns_200_and_uptime() -> None:

    app = create_app()

    with TestClient(app) as client:

        response = client.get("/health")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"

    assert "uptime" in body


def test_ready_returns_200_when_database_is_available() -> None:
    app = create_app()

    with patch("app.api.health.get_engine", return_value=WorkingEngine()), TestClient(app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["components"]["database"]["status"] == "ok"


class FailingConnection:
    def __enter__(self):  # noqa: ANN204
        raise Exception("database unavailable")

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001, ANN204
        return False


class FailingEngine:
    def connect(self):  # noqa: ANN201
        return FailingConnection()


def test_ready_returns_503_when_database_is_unavailable() -> None:
    app = create_app()
    with patch("app.api.health.get_engine", return_value=FailingEngine()), TestClient(app) as client:
        response = client.get("/ready")
    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "down"
    assert body["components"]["database"]["status"] == "down"
    assert "error" in body["components"]["database"]