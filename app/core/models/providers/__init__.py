"""
To add a new provider, create a `.py` file in this directory and decorate
a class with ``@register_provider("provider_name")``.
"""

from app.core.models.providers.provider_registry import (
    PROVIDER_REGISTRY,
    register_provider,
)

__all__ = ["PROVIDER_REGISTRY", "register_provider"]
