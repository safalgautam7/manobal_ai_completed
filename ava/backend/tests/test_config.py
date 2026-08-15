from app.config import Settings


def test_defaults_when_env_empty(monkeypatch):
    for var in [
        "GROQ_API_KEY",
        "LLM_MODEL",
        "CLERK_ISSUER",
        "CORS_ORIGINS",
        "AUTH_ENABLED",
    ]:
        monkeypatch.delenv(var, raising=False)
    s = Settings(
        groq_api_key="",
        llm_model="",
        auth_enabled=False,
        clerk_issuer="",
        clerk_jwks_url="",
        cors_origins=[],
    )
    assert s.auth_required is False
    assert s.max_conversations == 30
    assert s.retriever_k == 4
    assert s.llm_temperature == 0.3


def test_auth_required_needs_jwks_url():
    assert Settings(auth_enabled=False, clerk_jwks_url="").auth_required is False
    assert Settings(auth_enabled=True, clerk_jwks_url="").auth_required is False
    assert (
        Settings(
            auth_enabled=True,
            clerk_jwks_url="https://x.clerk.accounts.dev/.well-known/jwks.json",
        ).auth_required
        is True
    )


def test_cors_origins_parsed():
    s = Settings(cors_origins=["http://a.com", "https://b.com"])
    assert s.cors_origins == ["http://a.com", "https://b.com"]


def test_env_overrides(monkeypatch):
    monkeypatch.setenv("MAX_CONVERSATIONS", "5")
    monkeypatch.setenv("RETRIEVER_K", "8")
    monkeypatch.setenv("LLM_TEMPERATURE", "0.7")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    s = Settings(
        auth_enabled=True,
        clerk_jwks_url="https://x/.well-known/jwks.json",
    )
    assert s.max_conversations == 5
    assert s.retriever_k == 8
    assert s.llm_temperature == 0.7