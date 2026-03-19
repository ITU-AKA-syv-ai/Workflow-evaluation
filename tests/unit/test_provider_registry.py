import pytest
from tests.conftest import MockProvider

from app.core.models.providers import (
    provider_registry
)

from app.core.models.providers.provider_registry import register_provider

def test_register_provider() -> None:
    register_provider("azure")
    print(provider_registry.get_available_providers())
    assert "test" in provider_registry.get_available_providers()

