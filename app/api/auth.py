"""JWT auth + dependency injection."""
from __future__ import annotations
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from shared.config import get_settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """Validates JWT bearer token. Returns user dict. Allows dev bypass."""
    settings = get_settings()
    # In development, accept any token (or no token) — no auth enforcement
    if settings.app_env == "development":
        return {"sub": "dev-user", "role": "admin"}
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=["HS256"])
        return payload
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
