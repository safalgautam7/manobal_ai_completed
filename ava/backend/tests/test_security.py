import time
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app import security
from app.config import Settings


def _make_key_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    pub_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return priv_pem, pub_pem


def _token(priv_pem, issuer="https://issuer.clerk.accounts.dev", aud="manobal-frontend", sub="user_123", expires=True):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "iss": issuer,
        "aud": aud,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(hours=1) if expires else now - timedelta(hours=1),
    }
    return jwt.encode(payload, priv_pem, algorithm="RS256")


def _stub_key_client(pub_pem):
    class _Key:
        key = pub_pem

    class _Client:
        def get_signing_key_from_jwt(self, token):
            return _Key()

    return _Client()


def _authed_settings(pub_pem=None):
    return Settings(
        auth_enabled=True,
        clerk_issuer="https://issuer.clerk.accounts.dev",
        clerk_audience="manobal-frontend",
        clerk_jwks_url="https://issuer.clerk.accounts.dev/.well-known/jwks.json",
    )


def test_verify_token_returns_sub(monkeypatch):
    priv, pub = _make_key_pair()
    token = _token(priv)
    settings = _authed_settings()
    monkeypatch.setattr(security, "_get_key_client", lambda s: _stub_key_client(pub))
    assert security.verify_token(token, settings) == "user_123"


def test_verify_token_rejects_expired(monkeypatch):
    priv, pub = _make_key_pair()
    token = _token(priv, expires=False)
    settings = _authed_settings()
    monkeypatch.setattr(security, "_get_key_client", lambda s: _stub_key_client(pub))
    with pytest.raises(security.AuthError):
        security.verify_token(token, settings)


def test_verify_token_rejects_wrong_audience(monkeypatch):
    priv, pub = _make_key_pair()
    token = _token(priv, aud="someone-else")
    settings = _authed_settings()
    monkeypatch.setattr(security, "_get_key_client", lambda s: _stub_key_client(pub))
    with pytest.raises(security.AuthError):
        security.verify_token(token, settings)


def test_verify_token_requires_configured_jwks():
    settings = Settings(auth_enabled=True, clerk_jwks_url="")
    with pytest.raises(security.AuthError):
        security.verify_token("some-token", settings)


def test_get_current_user_anonymous_when_auth_disabled(settings):
    assert security.get_current_user(authorization=None, settings=settings) == "anonymous"


def test_get_current_user_requires_bearer(settings):
    authed = Settings(
        auth_enabled=True,
        clerk_jwks_url="https://issuer/.well-known/jwks.json",
    )
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        security.get_current_user(authorization=None, settings=authed)
    assert exc.value.status_code == 401