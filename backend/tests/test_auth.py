"""Tests for authentication and role foundation (Story 5.2).

Covers:
- Argon2id password hashing and verification (backend.app.auth.password)
- Session creation, rotation, invalidation (backend.app.auth.sessions)
- Role assignment and unauthenticated access regression
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from backend.app.auth.password import hash_password, needs_rehash, verify_password
from backend.app.auth.sessions import (
    SESSION_COOKIE_NAME,
    create_session,
    get_active_session,
    invalidate_session,
    rotate_session,
)
from backend.app.config import Settings
from backend.app.main import create_app


# ---------------------------------------------------------------------------
# Password hashing tests
# ---------------------------------------------------------------------------


def test_hash_password_returns_argon2id_hash() -> None:
    h = hash_password("correcthorsebatterystaple")
    assert h.startswith("$argon2id$"), "Expected Argon2id hash prefix"


def test_verify_password_correct_returns_true() -> None:
    h = hash_password("s3cr3t!")
    assert verify_password(h, "s3cr3t!") is True


def test_verify_password_wrong_returns_false() -> None:
    h = hash_password("s3cr3t!")
    assert verify_password(h, "wrong") is False


def test_verify_password_empty_against_hash_returns_false() -> None:
    h = hash_password("notempty")
    assert verify_password(h, "") is False


def test_hash_is_not_cleartext() -> None:
    plain = "mypassword123"
    h = hash_password(plain)
    assert plain not in h, "Hash must not contain cleartext password"


def test_two_hashes_of_same_password_are_different() -> None:
    h1 = hash_password("same")
    h2 = hash_password("same")
    assert h1 != h2, "Each hash should use a unique salt"


def test_needs_rehash_returns_false_for_fresh_hash() -> None:
    h = hash_password("fresh")
    assert needs_rehash(h) is False


# ---------------------------------------------------------------------------
# Session management tests (in-memory SQLite)
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem_conn():
    """Provide an in-memory SQLite connection with the minimal session schema."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    with engine.connect() as conn:
        # Minimal schema: users + user_sessions
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'student',
                    must_change_password INTEGER NOT NULL DEFAULT 1,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    last_login_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE user_sessions (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    created_at TEXT NOT NULL,
                    rotated_at TEXT,
                    expires_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    ip_address TEXT,
                    user_agent TEXT
                )
                """
            )
        )
        conn.execute(
            text("INSERT INTO users (id, username, password_hash, role) VALUES (1, 'student01', 'x', 'student')")
        )
        conn.commit()
        yield conn
    engine.dispose()


def test_create_session_returns_nonempty_id(mem_conn) -> None:
    sid = create_session(mem_conn, user_id=1)
    assert len(sid) == 128, "Session ID should be 128 hex chars (64 bytes)"


def test_get_active_session_returns_row(mem_conn) -> None:
    sid = create_session(mem_conn, user_id=1)
    mem_conn.commit()
    row = get_active_session(mem_conn, session_id=sid)
    assert row is not None
    assert row["user_id"] == 1


def test_get_active_session_returns_none_for_invalid_id(mem_conn) -> None:
    row = get_active_session(mem_conn, session_id="nonexistent")
    assert row is None


def test_invalidate_session_deactivates_it(mem_conn) -> None:
    sid = create_session(mem_conn, user_id=1)
    mem_conn.commit()
    invalidate_session(mem_conn, session_id=sid)
    mem_conn.commit()
    row = get_active_session(mem_conn, session_id=sid)
    assert row is None


def test_rotate_session_invalidates_old_and_creates_new(mem_conn) -> None:
    old_sid = create_session(mem_conn, user_id=1)
    mem_conn.commit()
    new_sid = rotate_session(mem_conn, old_session_id=old_sid, user_id=1)
    mem_conn.commit()
    assert new_sid != old_sid
    assert get_active_session(mem_conn, session_id=old_sid) is None
    assert get_active_session(mem_conn, session_id=new_sid) is not None


def test_session_cookie_name_constant() -> None:
    assert SESSION_COOKIE_NAME == "sid"


# ---------------------------------------------------------------------------
# Role assignment tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", ["professor", "student", "delegate", "admin_local"])
def test_valid_roles_are_accepted(mem_conn, role: str) -> None:
    """Verify all four roles can be stored in users.role."""
    mem_conn.execute(
        text(
            f"INSERT INTO users (id, username, password_hash, role) VALUES (99, 'user_{role}', 'x', :role)"
        ),
        {"role": role},
    )
    mem_conn.commit()
    row = mem_conn.execute(
        text("SELECT role FROM users WHERE username = :u"),
        {"u": f"user_{role}"},
    ).fetchone()
    assert row[0] == role


# ---------------------------------------------------------------------------
# Regression: unauthenticated access to unpublished data
# ---------------------------------------------------------------------------


def test_health_endpoint_accessible_without_auth(tmp_path: Path) -> None:
    """Health endpoint must remain accessible; unauthenticated requests should not leak data."""
    db_path = tmp_path / "app.sqlite3"
    app = create_app(Settings(database_url=f"sqlite:///{db_path}"))
    from fastapi.testclient import TestClient

    with TestClient(app) as client:
        response = client.get("/api/v1/health")
    assert response.status_code == 200
    payload = response.json()
    # Verify no auth internals leak through health endpoint
    assert "password" not in str(payload).lower()
    assert "session" not in str(payload).lower()
