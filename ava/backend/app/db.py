"""SQLite persistence for sessions, messages and emotion analytics.

SQLite is used deliberately to keep the dependency footprint small. A new
connection is opened per call (cheap for SQLite) with WAL mode enabled, so the
module is safe to use from FastAPI's threadpool without sharing connections
across threads.
"""

from __future__ import annotations

import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone

from app import config


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect(db_path: str):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    db_path = db_path or config.get_settings().database_path
    with _connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, id);

            CREATE TABLE IF NOT EXISTS emotion_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                emotion TEXT NOT NULL,
                score REAL NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_emotion_user
                ON emotion_events(user_id);
            """
        )


def _session_exists(db_path: str, session_id: str, user_id: str) -> bool:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT id FROM sessions WHERE id = ? AND user_id = ?",
            (session_id, user_id),
        ).fetchone()
        if row:
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (utcnow_iso(), session_id),
            )
            return True
    return False


def _create_session(db_path: str, user_id: str) -> str:
    session_id = uuid.uuid4().hex
    now = utcnow_iso()
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO sessions (id, user_id, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (session_id, user_id, now, now),
        )
    return session_id


def get_or_create_session(session_id: str | None, user_id: str) -> str:
    """Return a session id owned by ``user_id``, creating it if needed.

    A requested ``session_id`` is only reused when it belongs to the same user,
    so users can never observe or continue another user's conversation.
    """
    db_path = config.get_settings().database_path
    if session_id and _session_exists(db_path, session_id, user_id):
        return session_id
    return _create_session(db_path, user_id)


def append_message(session_id: str, role: str, content: str) -> None:
    with _connect(config.get_settings().database_path) as conn:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, utcnow_iso()),
        )


def get_recent_messages(session_id: str, limit: int) -> list[dict]:
    with _connect(config.get_settings().database_path) as conn:
        rows = conn.execute(
            """
            SELECT role, content FROM messages
            WHERE session_id = ?
            ORDER BY id DESC LIMIT ?
            """,
            (session_id, limit),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def save_emotion(user_id: str, emotion: str, score: float) -> None:
    with _connect(config.get_settings().database_path) as conn:
        conn.execute(
            "INSERT INTO emotion_events (user_id, emotion, score, created_at) VALUES (?, ?, ?, ?)",
            (user_id, emotion, score, utcnow_iso()),
        )


def get_emotion_counts(user_id: str | None = None) -> dict[str, int]:
    with _connect(config.get_settings().database_path) as conn:
        if user_id:
            rows = conn.execute(
                "SELECT emotion, COUNT(*) AS c FROM emotion_events WHERE user_id = ? GROUP BY emotion",
                (user_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT emotion, COUNT(*) AS c FROM emotion_events GROUP BY emotion"
            ).fetchall()
    return {r["emotion"]: r["c"] for r in rows}