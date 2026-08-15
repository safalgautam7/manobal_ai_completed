"""Clerk JWT verification for FastAPI.

Tokens are RS256 JWTs signed by Clerk. Public keys are fetched from Clerk's
JWKS endpoint and cached by ``PyJWKClient`` for an hour. When
``AUTH_ENABLED=false`` (local development / tests) a dummy user id is returned.
"""

from __future__ import annotations

from typing import Optional

import jwt
from fastapi import Depends, Header, HTTPException
from jwt import PyJWKClient

from app import config
from app.config import Settings


class AuthError(Exception):
    """Raised when a token cannot be validated."""


def _get_key_client(settings) -> PyJWKClient:
    if not settings.clerk_jwks_url:
        raise AuthError("Clerk JWKS URL is not configured")
    # PyJWKClient caches fetched keys internally with a TTL.
    return PyJWKClient(settings.clerk_jwks_url)


def verify_token(token: str, settings=None) -> str:
    """Validate a Clerk session token and return the user id (``sub``)."""
    settings = settings or config.get_settings()
    client = _get_key_client(settings)
    try:
        signing_key = client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.clerk_audience,
            issuer=settings.clerk_issuer or None,
            options={"require": ["exp", "iat", "nbf"]},
        )
    except AuthError:
        raise
    except Exception as exc:  # noqa: BLE001 - normalize every jwt failure
        raise AuthError(f"Token validation failed: {exc}") from exc
    sub = payload.get("sub")
    if not sub:
        raise AuthError("Token is missing a subject")
    return sub


def _settings_dep() -> Settings:
    # Resolved at request time so tests can swap the settings provider.
    return config.get_settings()


def get_current_user(
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(_settings_dep),
) -> str:
    """FastAPI dependency that returns the authenticated user id."""
    if not settings.auth_required:
        return "anonymous"

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1].strip()
    try:
        return verify_token(token, settings)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc