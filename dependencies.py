import os
import secrets

from fastapi import Header, HTTPException


async def require_api_key(x_api_key: str | None = Header(default=None)):
    """If API_KEY is set in the environment, protected endpoints require header `X-API-Key`."""
    expected = os.getenv("API_KEY")
    if not expected:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="invalid or missing API key")
