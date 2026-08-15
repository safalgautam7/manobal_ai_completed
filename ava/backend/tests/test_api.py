import pytest
from fastapi.testclient import TestClient

from app import chat, config, db, emotion, security
from app.config import Settings
from app.main import create_app


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_random_quote(client):
    r = client.get("/random-quote")
    assert r.status_code == 200
    assert r.json()["quote"]


# --- /prompt ---


def test_prompt_success(client, monkeypatch):
    async def fake_generate(query, session_id, user_id):
        return f"answer for {query}"

    monkeypatch.setattr(chat, "generate_response", fake_generate)
    r = client.post("/prompt", json={"query": "What is anxiety?"})
    assert r.status_code == 200
    data = r.json()
    assert data["response"] == "answer for What is anxiety?"
    assert data["status"] == "success"
    assert data["session_id"]

    # the returned session is reusable (owned by this user)
    sid = data["session_id"]
    assert db.get_or_create_session(sid, "anonymous") == sid


def test_prompt_empty_query_422(client):
    r = client.post("/prompt", json={"query": "   "})
    assert r.status_code == 422


def test_prompt_too_long_422(client):
    r = client.post("/prompt", json={"query": "a" * 2001})
    assert r.status_code == 422


def test_prompt_generation_failure_returns_502(client, monkeypatch):
    async def broken(query, session_id, user_id):
        raise RuntimeError("groq down")

    monkeypatch.setattr(chat, "generate_response", broken)
    r = client.post("/prompt", json={"query": "hello"})
    assert r.status_code == 502


# --- /analyze-emotion & /emotion-graph ---


def test_analyze_emotion(client, monkeypatch):
    monkeypatch.setattr(emotion, "analyze_emotion", lambda text: ("joy", 0.95))
    r = client.post("/analyze-emotion", json={"text": "I am so happy today"})
    assert r.status_code == 200
    data = r.json()
    assert data["emotion"] == "joy"
    assert data["score"] == pytest.approx(0.95)
    assert "suggestion" in data


def test_analyze_emotion_empty_422(client):
    r = client.post("/analyze-emotion", json={"text": ""})
    assert r.status_code == 422


def test_emotion_graph_counts_per_user(client, monkeypatch):
    def fake_analyze(text):
        return text, 0.9

    monkeypatch.setattr(emotion, "analyze_emotion", fake_analyze)
    client.post("/analyze-emotion", json={"text": "joy"})
    client.post("/analyze-emotion", json={"text": "joy"})
    client.post("/analyze-emotion", json={"text": "sadness"})

    r = client.get("/emotion-graph")
    assert r.status_code == 200
    assert r.json() == {"joy": 2, "sadness": 1}


# --- auth ---


def _authed_app_settings(tmp_path):
    return Settings(
        database_path=str(tmp_path / "auth.db"),
        vector_store_dir=str(tmp_path / "vector"),
        auth_enabled=True,
        clerk_issuer="https://issuer.clerk.accounts.dev",
        clerk_audience="manobal-frontend",
        clerk_jwks_url="https://issuer.clerk.accounts.dev/.well-known/jwks.json",
    )


def test_authed_endpoints_require_token(tmp_path, monkeypatch):
    s = _authed_app_settings(tmp_path)
    monkeypatch.setattr(config, "get_settings", lambda: s)
    db.init_db(s.database_path)

    client = TestClient(create_app())
    r = client.post("/prompt", json={"query": "hello"})
    assert r.status_code == 401

    r = client.get("/emotion-graph")
    assert r.status_code == 401


def test_authed_endpoints_accept_valid_token(tmp_path, monkeypatch):
    s = _authed_app_settings(tmp_path)
    monkeypatch.setattr(config, "get_settings", lambda: s)
    db.init_db(s.database_path)

    monkeypatch.setattr(security, "verify_token", lambda token, settings=None: f"user-{token}")

    async def fake_generate(query, session_id, user_id):
        assert user_id == "user-abc"
        return "ok"

    monkeypatch.setattr(chat, "generate_response", fake_generate)

    client = TestClient(create_app())
    r = client.post(
        "/prompt",
        json={"query": "hello"},
        headers={"Authorization": "Bearer abc"},
    )
    assert r.status_code == 200