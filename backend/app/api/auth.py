from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt

from app.config.settings import get_settings

jwks_cache = None
settings = get_settings().jwt


async def get_jwks() -> dict:
    """Fetches the JSON Web Key Set (JWKS) from the configured URL and caches it for future use."""
    global jwks_cache
    if jwks_cache is None:
        async with httpx.AsyncClient() as client:
            response = await client.get(settings.jwks_url)
            jwks_cache = response.json()
    return jwks_cache


async def verify_token(token: str) -> dict | None:
    """Verifies the provided JWT token using either a JWKS endpoint or a secret key, depending on the configuration."""
    try:
        if settings.jwks_url:
            jwks = await get_jwks()
            header = jwt.get_unverified_header(token)
            key = next(k for k in jwks["keys"] if k["kid"] == header["kid"])

            payload = jwt.decode(
                token,
                key,
                algorithms=[settings.algorithm],
                audience=settings.audience,
                issuer=settings.issuer,
            )
        else:
            payload = jwt.decode(
                token,
                settings.secret,
                algorithms=[settings.algorithm],
                audience=settings.audience,
                issuer=settings.issuer,
            )
        return payload
    except Exception:
        return None


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),  # noqa: B008
) -> dict:
    """Dependency function that extracts and verifies the JWT token from the Authorization header and returns the payload as the current user information."""
    token = credentials.credentials
    payload = await verify_token(token)

    if payload is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid or expired token")
    return payload


# this is only for local development as there is no normal other way to get the token for now


def create_token(sub: str = "dev-user") -> str:
    """Creates a JWT token with the specified subject (sub) claim, signed using the configured secret and algorithm, and valid for 24 hours."""
    payload = {
        "sub": sub,
        "iss": settings.issuer,
        "aud": settings.audience,
        "exp": datetime.now(UTC) + timedelta(hours=24),
    }

    return jwt.encode(payload, settings.secret, settings.algorithm)


router = APIRouter()


@router.get(
    path="/dev/token",
    tags=["Dev"],
)
def get_dev_token() -> dict[str,str]:
    """Endpoint for generating a development JWT token."""
    return {"access_token": create_token("frontend-dev"), "token_type": "bearer"}
