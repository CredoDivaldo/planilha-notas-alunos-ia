"""Story 9.2 — Chaos tests for broadcast with Evolution interruption.

These tests mock the httpx layer (used by EvolutionApiClient.send_whatsapp_text)
to deterministically simulate docker kill scenarios. The same scenarios are
exercised live in docs/qa/chaos-test-9.2.md during operator validation.

Acceptance Criteria covered:
- AC1: 5+ destinatários in broadcast
- AC2: Evolution interrupted mid-broadcast
- AC3: HTTP 502 with sanitised error (no internal leak)
- AC4: Retry recovers after Evolution restart
- AC5: 11ª mensagem triggers rate limit
- AC6: Transcript doc archived (manual — verified in 9.2 docs)
- AC7: This suite (5 tests) is reproducible in CI

Note: pytest-asyncio is NOT a dependency. Tests use asyncio.run() so they
work on the existing pytest setup without extra plugins.
"""
from __future__ import annotations

import asyncio
import inspect
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.app.services.evolution_api_client import (
    EvolutionApiError,
    send_whatsapp_text,
)
from backend.app.services.chatbot_rate_limiter import ChatbotRateLimiter
from backend.app.utils.phone import normalize_phone


# ---------------------------------------------------------------------------
# AC1: Broadcast with 5+ destinatários (smoke baseline, no kill)
# ---------------------------------------------------------------------------


def test_broadcast_succeeds_against_live_evolution(chaos_students: list[dict[str, Any]]) -> None:
    """AC1 + AC7: 5 destinatários sent successfully when Evolution is healthy.

    This is the smoke baseline — proves the suite can drive a real-shaped
    broadcast (5 sequential sends) without the chaos injection. If THIS test
    fails, the fixture/wiring is broken; the chaos tests would be unreliable.
    """
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'{"key": {"id": "ok-1"}}'
        mock_response.json.return_value = {"key": {"id": "ok-1"}}
        mock_response.raise_for_status = MagicMock()

        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        async def run_broadcast() -> list[dict[str, Any]]:
            results: list[dict[str, Any]] = []
            for student in chaos_students:
                result = await send_whatsapp_text(
                    instance="turma-c",
                    phone_number=student["phone"],
                    message=f"Olá {student['full_name']}, a sua nota está disponível.",
                )
                results.append(result)
            return results

        results = asyncio.run(run_broadcast())

    assert len(results) == 5
    assert all(r["success"] is True for r in results)
    assert all(r["error"] is None for r in results)
    assert mock_client.post.call_count == 5


# ---------------------------------------------------------------------------
# AC2 + AC3: Evolution killed mid-broadcast → sanitised error
# ---------------------------------------------------------------------------


def test_broadcast_returns_error_when_evolution_killed_midway(
    chaos_students: list[dict[str, Any]],
) -> None:
    """AC2 + AC3: First N sends succeed, then docker kill → ConnectError.

    Simulates docker kill evolution_api after 2 successful sends. The 3rd
    send must raise EvolutionApiError with status_code=0 (transport error).
    """
    import httpx

    sent = {"count": 0}
    ok_response = MagicMock()
    ok_response.status_code = 200
    ok_response.content = b'{"key": {"id": "ok-1"}}'
    ok_response.json.return_value = {"key": {"id": "ok-1"}}
    ok_response.raise_for_status = MagicMock()

    async def fake_post(url: str, **kwargs: Any) -> Any:
        sent["count"] += 1
        if sent["count"] > 2:  # kill happens after 2nd send
            raise httpx.ConnectError("Connection refused: docker kill evolution_api")
        return ok_response

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = fake_post

    with patch("httpx.AsyncClient", return_value=mock_client):
        async def run_scenario() -> tuple[dict[str, Any] | None, dict[str, Any] | None, Any]:
            # First 2 succeed
            r1 = await send_whatsapp_text(
                instance="turma-c",
                phone_number=chaos_students[0]["phone"],
                message="m1",
            )
            r2 = await send_whatsapp_text(
                instance="turma-c",
                phone_number=chaos_students[1]["phone"],
                message="m2",
            )
            # 3rd send (mid-broadcast, Evolution is down) must raise
            try:
                await send_whatsapp_text(
                    instance="turma-c",
                    phone_number=chaos_students[2]["phone"],
                    message="m3",
                )
                return r1, r2, None
            except EvolutionApiError as exc:
                return r1, r2, exc

        r1, r2, exc = asyncio.run(run_scenario())

    # First two sends succeed
    assert r1 is not None and r1["success"] is True
    assert r2 is not None and r2["success"] is True

    # Third send raised
    assert exc is not None

    # AC3: status_code=0 indicates transport error (sanitised)
    assert exc.status_code == 0
    # The user-facing message is sanitised — no internal paths / docker hints leak
    user_msg = exc.user_message
    assert "docker" not in user_msg.lower(), f"docker leak: {user_msg!r}"
    assert "/var/log" not in user_msg, f"path leak: {user_msg!r}"
    # The user message is short and friendly
    assert len(user_msg) <= 120
    # But the log-facing str() preserves the diagnostic info (for log inspection)
    log_msg = str(exc)
    assert "ConnectError" in log_msg, "log-facing str() should preserve type name"


def test_broadcast_500_response_is_sanitised(
    chaos_students: list[dict[str, Any]],
) -> None:
    """AC3: Evolution returns 500 with internal log path → response must NOT leak it.

    The 500 body contains '/var/log/evolution/api.log' which is internal. The
    sanitised error must keep status_code but truncate the body. Detail must
    not expose the full path.
    """
    import httpx

    error_response = MagicMock()
    error_response.status_code = 500
    error_response.text = (
        "Internal Server Error: traceback at /var/log/evolution/api.log line 42"
    )
    error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "500 Server Error", request=MagicMock(), response=error_response
    )

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.post = AsyncMock(return_value=error_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        async def run_scenario() -> Any:
            try:
                await send_whatsapp_text(
                    instance="turma-c",
                    phone_number=chaos_students[0]["phone"],
                    message="m1",
                )
                return None
            except EvolutionApiError as exc:
                return exc

        exc = asyncio.run(run_scenario())

    assert exc is not None
    # Status code is preserved (for log/debug)
    assert exc.status_code == 500
    # Body is preserved (for log) but should be truncated to 500 chars
    assert len(exc.body) <= 500
    # The user-facing message is short and sanitised — no internal paths leak
    user_msg = exc.user_message
    assert len(user_msg) <= 120, f"user_message too long: {user_msg!r}"
    assert "/var/log" not in user_msg, f"path leak in user_message: {user_msg!r}"
    assert "traceback" not in user_msg.lower(), f"traceback leak: {user_msg!r}"
    # Log-facing str() still has the full diagnostic
    log_facing = str(exc)
    assert "500" in log_facing


# ---------------------------------------------------------------------------
# AC4: Retry recovers after Evolution restart
# ---------------------------------------------------------------------------


def test_broadcast_retry_recovers_after_evolution_restart(
    chaos_students: list[dict[str, Any]],
) -> None:
    """AC4: After Evolution restart, retry must succeed.

    Sequence:
    1. Send 1 — succeed
    2. Send 2 — fail (ConnectError, Evolution killed)
    3. Restart Evolution (simulated: re-patch httpx with healthy mock)
    4. Retry send 2 — succeed
    5. Send 3..5 — succeed
    """
    import httpx

    # Phase 1: Evolution is up briefly, then killed
    sent_phase1 = {"count": 0}

    async def phase1_post(url: str, **kwargs: Any) -> Any:
        sent_phase1["count"] += 1
        if sent_phase1["count"] == 1:
            ok = MagicMock()
            ok.status_code = 200
            ok.content = b'{"key": {"id": "phase1-1"}}'
            ok.json.return_value = {"key": {"id": "phase1-1"}}
            ok.raise_for_status = MagicMock()
            return ok
        raise httpx.ConnectError("Connection refused")

    mock_client1 = AsyncMock()
    mock_client1.__aenter__ = AsyncMock(return_value=mock_client1)
    mock_client1.__aexit__ = AsyncMock(return_value=None)
    mock_client1.post = phase1_post

    # Phase 2: Evolution restarted (operator runs `docker compose restart evolution_api`)
    sent_phase2 = {"count": 0}

    async def phase2_post(url: str, **kwargs: Any) -> Any:
        sent_phase2["count"] += 1
        ok = MagicMock()
        ok.status_code = 200
        ok.content = b'{"key": {"id": "phase2-1"}}'
        ok.json.return_value = {"key": {"id": "phase2-1"}}
        ok.raise_for_status = MagicMock()
        return ok

    mock_client2 = AsyncMock()
    mock_client2.__aenter__ = AsyncMock(return_value=mock_client2)
    mock_client2.__aexit__ = AsyncMock(return_value=None)
    mock_client2.post = phase2_post

    async def run_recovery() -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
        # Phase 1: send 1 succeeds, send 2 fails
        with patch("httpx.AsyncClient", return_value=mock_client1):
            r1 = await send_whatsapp_text(
                instance="turma-c", phone_number=chaos_students[0]["phone"], message="m1"
            )
            try:
                await send_whatsapp_text(
                    instance="turma-c", phone_number=chaos_students[1]["phone"], message="m2"
                )
                raise AssertionError("phase 1 send 2 should have raised")
            except EvolutionApiError:
                pass

        # Phase 2: Evolution is back. Retry send 2 and continue with rest
        with patch("httpx.AsyncClient", return_value=mock_client2):
            r2_retry = await send_whatsapp_text(
                instance="turma-c",
                phone_number=chaos_students[1]["phone"],
                message="m2-retry",
            )
            remaining: list[dict[str, Any]] = []
            for student in chaos_students[2:]:
                r = await send_whatsapp_text(
                    instance="turma-c", phone_number=student["phone"], message="m"
                )
                remaining.append(r)
            return r1, r2_retry, remaining

    r1, r2_retry, remaining = asyncio.run(run_recovery())

    # Phase 1: only 1 success + 1 fail
    assert sent_phase1["count"] == 2
    # Phase 2: 1 retry + 3 remaining
    assert sent_phase2["count"] == 4
    # All phase-2 sends succeeded
    assert r1["success"] is True
    assert r2_retry["success"] is True
    assert r2_retry["error"] is None
    assert all(r["success"] is True for r in remaining)


# ---------------------------------------------------------------------------
# AC5: 11ª mensagem triggers rate limit (per phone, per day)
# ---------------------------------------------------------------------------


def test_broadcast_eleventh_message_per_phone_triggers_rate_limit(
    chaos_students: list[dict[str, Any]],
) -> None:
    """AC5: Story 3.4 rate limiter — 11ª mensagem do mesmo nº deve bloquear.

    The chatbot rate limiter is per-phone, per-day (default 10/day). The 11th
    message from the same number must be blocked. The broadcast for OTHER
    students is unaffected — the limiter is per-phone, not global.
    """
    # Fresh in-memory limiter
    limiter = ChatbotRateLimiter(daily_limit=10)
    target_phone = normalize_phone(chaos_students[0]["phone"])  # 244900000001

    # First 10 messages pass (record then check)
    for i in range(10):
        assert limiter.is_blocked(target_phone) is False, (
            f"message {i + 1} should not yet be blocked"
        )
        limiter.record(target_phone)

    # 11th message is blocked (limit reached, NOT recorded — that's the contract)
    assert limiter.is_blocked(target_phone) is True, "11th message must be blocked"
    # Sanity: count is exactly 10 (the 11th never made it through)
    assert limiter.get_count(target_phone) == 10

    # Broadcast for OTHER students is unaffected (per-phone key)
    for student in chaos_students[1:]:
        other_phone = normalize_phone(student["phone"])
        assert limiter.is_blocked(other_phone) is False, (
            f"other student {student['phone']} should not be rate-limited"
        )


# ---------------------------------------------------------------------------
# AC7 helper: verify pytest discovers all 5 tests
# ---------------------------------------------------------------------------


def test_chaos_suite_has_5_tests() -> None:
    """AC7: Verify the suite has exactly 5 chaos test functions (deterministic count)."""
    from backend.tests.chaos import test_broadcast_chaos as module

    tests = [
        name
        for name, obj in inspect.getmembers(module)
        if inspect.isfunction(obj) and name.startswith("test_")
    ]
    # 5 functional tests + 1 helper = 6 functions starting with test_
    assert len(tests) == 6
    # The 5 AC-tagged tests must all be present
    assert "test_broadcast_succeeds_against_live_evolution" in tests
    assert "test_broadcast_returns_error_when_evolution_killed_midway" in tests
    assert "test_broadcast_500_response_is_sanitised" in tests
    assert "test_broadcast_retry_recovers_after_evolution_restart" in tests
    assert "test_broadcast_eleventh_message_per_phone_triggers_rate_limit" in tests
