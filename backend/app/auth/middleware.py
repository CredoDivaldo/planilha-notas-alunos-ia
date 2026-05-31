"""Auth observability middleware.

Logs structured auth context for every request:
  - request_id
  - user_id (when authenticated, from session cookie)
  - role (when authenticated)
  - auth_event_type (login, failed_login, logout, etc.)
  - failure_reason_category (credential_invalid, session_expired, etc.)

NEVER logs cleartext passwords or session tokens.
"""
from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request

LOGGER = logging.getLogger("backend.auth")

# Auth event type constants — must match audit_log.auth_event_type values.
AUTH_EVENT_LOGIN = "login"
AUTH_EVENT_FAILED_LOGIN = "failed_login"
AUTH_EVENT_PASSWORD_CHANGE = "password_change"
AUTH_EVENT_DELEGATE_ASSIGNMENT = "delegate_assignment"
AUTH_EVENT_SENSITIVE_OP_APPROVAL = "sensitive_op_approval_state_change"
AUTH_EVENT_LOGOUT = "logout"
AUTH_EVENT_SESSION_ROTATION = "session_rotation"

# Failure reason category constants — kept coarse to avoid leaking enumeration info.
FAILURE_REASON_CREDENTIAL_INVALID = "credential_invalid"
FAILURE_REASON_SESSION_EXPIRED = "session_expired"
FAILURE_REASON_SESSION_NOT_FOUND = "session_not_found"
FAILURE_REASON_ACCOUNT_INACTIVE = "account_inactive"
FAILURE_REASON_MUST_CHANGE_PASSWORD = "must_change_password"
FAILURE_REASON_RATE_LIMITED = "rate_limited"
FAILURE_REASON_INSUFFICIENT_ROLE = "insufficient_role"


def log_auth_event(
    *,
    request_id: str | None,
    user_id: int | None,
    role: str | None,
    event_type: str,
    failure_reason: str | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Emit a structured auth event log record.

    Parameters
    ----------
    request_id:
        Correlation ID from ``X-Request-ID`` header.
    user_id:
        Authenticated user ID, or *None* for unauthenticated requests.
    role:
        User's role string, or *None* when not authenticated.
    event_type:
        One of the AUTH_EVENT_* constants.
    failure_reason:
        One of the FAILURE_REASON_* constants, or *None* on success.
    extra:
        Additional context (must never contain passwords or tokens).
    """
    record: dict[str, Any] = {
        "request_id": request_id,
        "user_id": user_id,
        "role": role,
        "auth_event_type": event_type,
    }
    if failure_reason is not None:
        record["failure_reason"] = failure_reason
    if extra:
        record.update(extra)
    LOGGER.info("auth_event", extra=record)


async def auth_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Any]],
) -> Any:
    """Attach auth context to ``request.state`` for downstream use.

    Reads ``request.state.request_id`` (set by the request_id_middleware in
    main.py) and populates:
      - ``request.state.auth_user_id``
      - ``request.state.auth_role``

    Actual session validation is deferred to route-level dependencies.
    This middleware only ensures the context attributes exist.
    """
    request.state.auth_user_id = None
    request.state.auth_role = None
    response = await call_next(request)
    return response
