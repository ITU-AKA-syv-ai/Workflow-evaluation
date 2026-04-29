from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.config.settings import get_settings


API_KEY_HEADER = "X-API-Key"
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

API_KEY_LOOKUP = {
    secret.get_secret_value():value
    for secret,value in get_settings().api.keys.items()
}

def get_api_key(api_key: str = Security(api_key_header)):
    if not api_key or api_key not in API_KEY_LOOKUP:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return API_KEY_LOOKUP[api_key]