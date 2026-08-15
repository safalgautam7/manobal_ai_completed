import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("AUTH_ENABLED", "false")

import pytest

from app import config, db
from app.config import Settings

BACKEND_DIR = Path(__file__).resolve().parent


@pytest.fixture()
def settings(tmp_path, monkeypatch):
    """Point every config-dependent module at an isolated tmp database."""
    s = Settings(
        database_path=str(tmp_path / "manobal.db"),
        vector_store_dir=str(tmp_path / "vector_store"),
        auth_enabled=False,
        clerk_jwks_url="",
        csv_data_file=str(BACKEND_DIR / "data" / "combined_mental_health_dataset.csv"),
        quotes_file=str(BACKEND_DIR / "data" / "mental_health_quotes.txt"),
    )
    monkeypatch.setattr(config, "get_settings", lambda: s)
    db.init_db(s.database_path)
    return s


@pytest.fixture()
def client(settings):
    from fastapi.testclient import TestClient

    from app.main import create_app

    with TestClient(create_app()) as c:
        yield c