from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config.settings import get_settings


API_KEY_HEADER = "X-API-Key"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

VALID_API_KEYS = set(map(lambda x: x.get_secret_value(),get_settings().api.keys.keys()))

def get_api_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return get_settings().api.keys[api_key]