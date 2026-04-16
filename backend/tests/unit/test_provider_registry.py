from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from backend.app.core.providers.provider_registry import (
    PROVIDER_REGISTRY,
    get_available_providers,
    get_provider,
    register_provider,
)
from backend.tests.conftest import ErrorProvider, MockProvider


@pytest.fixture(autouse=True)
def _clean_registry() -> Generator[TestClient, None]:
    """Save and restore the global PROVIDER_REGISTRY around every test."""
    snapshot = PROVIDER_REGISTRY.copy()
    PROVIDER_REGISTRY.clear()
    yield
    PROVIDER_REGISTRY.clear()
    PROVIDER_REGISTRY.update(snapshot)


def test_register_provider() -> None:
    register_provider("mock")(MockProvider)

    assert "mock" in PROVIDER_REGISTRY
    assert PROVIDER_REGISTRY["mock"] is MockProvider


def test_register_provider_returns_class_unchanged() -> None:
    result = register_provider("mock")(MockProvider)

    assert result is MockProvider


def test_register_duplicate_raises() -> None:
    register_provider("dup")(MockProvider)

    with pytest.raises(ValueError, match="already registered"):
        register_provider("dup")(MockProvider)


def test_register_multiple_providers() -> None:
    register_provider("first")(MockProvider)
    register_provider("second")(MockProvider)

    assert PROVIDER_REGISTRY["first"] is MockProvider
    assert PROVIDER_REGISTRY["second"] is MockProvider


def test_get_provider_found() -> None:
    register_provider("mock")(MockProvider)

    assert get_provider("mock") is MockProvider


def test_get_provider_missing_raises_key_error() -> None:
    with pytest.raises(KeyError):
        get_provider("nonexistent")


def test_get_available_providers_empty() -> None:
    assert get_available_providers() == []


def test_get_available_providers() -> None:
    register_provider("hmm1")(MockProvider)
    register_provider("hmm2")(ErrorProvider)

    available = get_available_providers()

    assert "hmm1" in available
    assert "hmm2" in available
    assert len(available) == 2
