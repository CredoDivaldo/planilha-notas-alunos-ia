"""Chaos test fixtures for Story 9.2.

Provides:
- 5+ student fixture (chaos_students) seeded with normalised phones
- chaos_docker_compose — fixture that mocks httpx to simulate docker kill
  scenarios deterministically (no live Docker required)
- restore_evolution — context manager helper to "restart" Evolution mid-test
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixture: 5 chaos students with realistic phone numbers
# ---------------------------------------------------------------------------


@pytest.fixture()
def chaos_students() -> list[dict[str, Any]]:
    """5 students with deterministic phone numbers for chaos broadcast tests.

    Mirrors Story 9.1 follow-up: 6 students seeded in turma 10A. We use 5 here
    so a single test covers AC1 (5+ destinatários) without depending on row 6.
    """
    return [
        {"student_id": 1, "phone": "+244900000001", "full_name": "Chaos One"},
        {"student_id": 2, "phone": "+244900000002", "full_name": "Chaos Two"},
        {"student_id": 3, "phone": "+244900000003", "full_name": "Chaos Three"},
        {"student_id": 4, "phone": "+244900000004", "full_name": "Chaos Four"},
        {"student_id": 5, "phone": "+244900000005", "full_name": "Chaos Five"},
    ]


# ---------------------------------------------------------------------------
# Fixture: configured Evolution environment
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def configure_evolution_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mark Evolution as configured so the production path is exercised.

    Each test can override the actual httpx behaviour via chaos_docker_compose.
    """
    monkeypatch.setenv("EVOLUTION_API_URL", "http://localhost:8080")
    monkeypatch.setenv("EVOLUTION_API_KEY", "test-chaos-api-key")
    monkeypatch.setenv("EVOLUTION_INSTANCE", "turma-c")


# ---------------------------------------------------------------------------
# Chaos injection helpers
# ---------------------------------------------------------------------------


@contextmanager
def evolution_healthy():
    """Patch httpx so Evolution returns 200 OK for every sendText call."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"key": {"id": "chaos-msg-id"}}'
    mock_response.json.return_value = {"key": {"id": "chaos-msg-id"}}
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        yield mock_client


@contextmanager
def evolution_killed_midway(kill_after: int = 2):
    """Patch httpx so Evolution returns ConnectError after N successful sends.

    First ``kill_after`` posts succeed (HTTP 200). Subsequent posts raise
    httpx.ConnectError as if docker killed the container mid-broadcast.

    ``kill_after=2`` simulates: send to student 1 ✓, send to student 2 ✓,
    kill happens, send to student 3+ fails with ConnectError.
    """
    sent = {"count": 0}

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b'{"key": {"id": "chaos-msg-id"}}'
    mock_response.json.return_value = {"key": {"id": "chaos-msg-id"}}
    mock_response.raise_for_status = MagicMock()

    async def fake_post(url: str, **kwargs: Any) -> Any:
        sent["count"] += 1
        if sent["count"] > kill_after:
            import httpx
            raise httpx.ConnectError("Connection refused: docker kill evolution_api")
        return mock_response

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = fake_post

    with patch("httpx.AsyncClient", return_value=mock_client):
        yield mock_client, sent


@contextmanager
def evolution_returns_500(mid_broadcast: bool = True):
    """Patch httpx so Evolution returns 500 (vs ConnectError).

    Useful for verifying sanitisation of 4xx/5xx response bodies (AC3).
    """
    error_response = MagicMock()
    error_response.status_code = 500
    error_response.text = "Internal Server Error — see /var/log/evolution/api.log"
    error_response.raise_for_status.side_effect = Exception("500 Server Error")

    sent = {"count": 0}
    ok_response = MagicMock()
    ok_response.status_code = 200
    ok_response.content = b'{"key": {"id": "ok-msg"}}'
    ok_response.json.return_value = {"key": {"id": "ok-msg"}}
    ok_response.raise_for_status = MagicMock()

    async def fake_post(url: str, **kwargs: Any) -> Any:
        sent["count"] += 1
        if mid_broadcast and sent["count"] > 2:
            return error_response
        return ok_response

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = fake_post

    with patch("httpx.AsyncClient", return_value=mock_client):
        yield mock_client, sent


@pytest.fixture()
def reset_rate_limiter(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset the chatbot rate limiter so test runs are isolated.

    Story 3.4: limit is per phone. Each test should start with a clean count.
    """
    from backend.app.services.chatbot_rate_limiter import reset_for_tests
    reset_for_tests()


# ---------------------------------------------------------------------------
# Test isolation: ensure env doesn't leak between tests
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _isolate_chaos_tests(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure EVOLUTION_API_URL is set for every test in this directory."""
    monkeypatch.setenv("EVOLUTION_API_URL", "http://localhost:8080")
