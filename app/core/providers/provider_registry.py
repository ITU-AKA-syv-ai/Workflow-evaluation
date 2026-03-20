from collections.abc import Callable
from typing import TypeVar

from app.core.providers.base import BaseProvider

T = TypeVar("T", bound=type[BaseProvider])

PROVIDER_REGISTRY: dict[str, type[BaseProvider]] = {}


def register_provider(name: str) -> Callable[[T], T]:
    """
    Decorator to register a provider in the provider registry.
    This will be caught when discover_providers() is called.

    Args:
        name (str): The name of the provider.

    Returns:
        Callable[[T], T]: The decorated function.
    """

    def decorator(
        cls: T,
    ) -> T:
        if name in PROVIDER_REGISTRY:
            raise ValueError(
                f"Provider '{name}' is already registered "
                f"({PROVIDER_REGISTRY[name].__qualname__})"
            )
        PROVIDER_REGISTRY[name] = cls
        return cls

    return decorator


def get_available_providers() -> list[str]:
    """Returns the names of all registered providers"""
    return list(PROVIDER_REGISTRY)


def get_provider(name: str) -> type[BaseProvider] | None:
    """Looks up a provider by name, or raise an error if the provider is not registered."""
    return PROVIDER_REGISTRY[name]


def discover_providers() -> None:
    """
    Imports all provider modules in this directory to trigger registration. This should be called once from `app.core.models.registry`.

    It discovers any `.py` file in this directory that is not a base module and does not start with an underscore.
    """
    import importlib
    from pathlib import Path

    skip = {"__init__", "base", "provider_registry"}
    for path in Path(__file__).parent.glob("*.py"):
        if path.stem not in skip and not path.stem.startswith("_"):
            importlib.import_module(f"app.core.providers.{path.stem}")
