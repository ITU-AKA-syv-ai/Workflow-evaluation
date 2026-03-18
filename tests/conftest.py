from typing import Generator

import pytest
from starlette.testclient import TestClient

from app.api.evaluate import get_registry
from app.core.models.registry import EvaluationRegistry
from app.main import app as fastapi_app

@pytest.fixture(scope="function")
def registry() -> Generator:
    yield EvaluationRegistry()

@pytest.fixture(scope="function")
def client_with_registry(registry: EvaluationRegistry) -> Generator[TestClient, None, None]:
    def override_get_registry():
        yield registry

    fastapi_app.dependency_overrides[get_registry] = override_get_registry
    with TestClient(fastapi_app) as c:
        yield c

    fastapi_app.dependency_overrides.clear()