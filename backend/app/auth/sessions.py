"""Server-side session management.

Sessions are stored in ``user_sessions`` table.
The client receives only an opaque session ID via an HttpOnly cookie.
No session data is exposed to the frontend.

Cookie baseline:
  - HttpOnly=True
  - SameSite=Lax
  - Secure=False for local dev; set via config for production

Session lifecycle:
  - Created on successful login
  - Rotated on login (new ID, old invalidated) and password change
  - Expired sessions are treated as invalid (not deleted immediately)
"""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.engine import Connection

# Session cookie name
SESSION_COOKIE_NAME = "sid"

# Default session duration
DEFAULT_SESSION_TTL_HOURS: int = 12

# Session ID length (URL-safe token, 128 hex chars = 512 bits)
_SESSION_ID_BYTES: int = 64


def generate_session_id() -> str:
    """Return a cryptographically secure random session ID."""
    return secrets.token_hex(_SESSION_ID_BYTES)


def create_session(
    conn: Connection,
    *,
    user_id: int,
    ip_address: str | None = None,
    user_agent: str | None = None,
    ttl_hours: int = DEFAULT_SESSION_TTL_HOURS,
) -> str:
    """Insert a new session record and return the session ID.

    Parameters
    ----------
    conn:
        Active SQLAlchemy connection (within a transaction).
    user_id:
        ID of the authenticated user.
    ip_address:
        Client IP (for audit purposes only — never used for auth decisions).
    user_agent:
        Truncated user-agent string.
    ttl_hours:
        Session lifetime in hours.

    Returns
    -------
    str
        The new session ID to be stored in the ``sid`` cookie.
    """
    session_id = generate_session_id()
    now = datetime.now(UTC)
    expires_at = now + timedelta(hours=ttl_hours)
    conn.execute(
        text(
            "INSERT INTO user_sessions (id, user_id, created_at, expires_at, is_active,"
            " ip_address, user_agent)"
            " VALUES (:id, :user_id, :created_at, :expires_at, 1, :ip_address, :user_agent)"
        ),
        {
            "id": session_id,
            "user_id": user_id,
            "created_at": now.replace(tzinfo=None),
            "expires_at": expires_at.replace(tzinfo=None),
            "ip_address": ip_address,
            "user_agent": (user_agent or "")[:512] if user_agent else None,
        },
    )
    return session_id


def rotate_session(
    conn: Connection,
    *,
    old_session_id: str,
    user_id: int,
    ip_address: str | None = None,
    user_agent: str | None = None,
    ttl_hours: int = DEFAULT_SESSION_TTL_HOURS,
) -> str:
    """Invalidate *old_session_id* and create a new session.

    Called on login (prevents session fixation) and on password change.

    Returns
    -------
    str
        The new session ID.
    """
    now = datetime.now(UTC)
    # Invalidate old session
    conn.execute(
        text(
            "UPDATE user_sessions SET is_active = 0, rotated_at = :now"
            " WHERE id = :old_id AND is_active = 1"
        ),
        {"now": now.replace(tzinfo=None), "old_id": old_session_id},
    )
    return create_session(
        conn,
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        ttl_hours=ttl_hours,
    )


def invalidate_session(conn: Connection, *, session_id: str) -> None:
    """Mark *session_id* as inactive (logout)."""
    conn.execute(
        text("UPDATE user_sessions SET is_active = 0 WHERE id = :sid"),
        {"sid": session_id},
    )


def get_active_session(conn: Connection, *, session_id: str) -> dict | None:
    """Return the session row if active and not expired, otherwise *None*.

    Returns
    -------
    dict | None
        Row dict with keys: id, user_id, expires_at.
    """
    now = datetime.now(UTC).replace(tzinfo=None)
    row = conn.execute(
        text(
            "SELECT id, user_id, expires_at FROM user_sessions"
            " WHERE id = :sid AND is_active = 1 AND expires_at > :now"
        ),
        {"sid": session_id, "now": now},
    ).fetchone()
    if row is None:
        return None
    return {"id": row[0], "user_id": row[1], "expires_at": row[2]}
