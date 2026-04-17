from collections.abc import Iterable

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def _matches_token(raw_value: str | None, expected_token: str) -> bool:
    if not raw_value:
        return False
    if raw_value == expected_token:
        return True
    if raw_value.startswith("Bearer "):
        return raw_value.removeprefix("Bearer ").strip() == expected_token
    return False


def require_api_token(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
) -> None:
    settings = get_settings()
    candidates: Iterable[str | None] = (authorization, x_api_key)
    if any(_matches_token(value, settings.mcp_auth_token) for value in candidates):
        return
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid authentication token.",
    )
