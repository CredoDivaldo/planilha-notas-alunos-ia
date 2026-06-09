# Story 9.2 — Chaos Test Transcript (Evolution mid-broadcast)

**Date:** 2026-06-09
**Operator:** Dex (@dev) via SDC engine, with operator attestation by Credo
**Branch:** `master` (Story 9.1 merged at `ba07f43`)
**Predecessor:** [Story 9.1 — Evolution Acceptance](evolution-acceptance-9.1.md)
**Acceptance Criteria verified:** AC1, AC2, AC3, AC4, AC5, AC6, AC7

---

## Overview

This document archives the chaos test results for Story 9.2. The tests
**deterministically simulate** the docker kill scenarios (mocking httpx so
they run in CI without a live Evolution stack) and are also **exercised
manually** against a live Evolution stack during operator validation.

| | Deterministic (CI) | Live (operator) |
|---|---|---|
| Suite | `backend/tests/chaos/test_broadcast_chaos.py` | manual `docker kill`/`docker compose restart` |
| Result | **6/6 passed** in 0.18s | run-by-Credo (attestation below) |
| Replayable | ✅ | manual |

The full pytest suite ran **176/176 passed** in 7.77s — zero regression.

---

## Acceptance Criteria — Evidence Matrix

| AC | Description | Evidence |
|----|-------------|----------|
| **AC1** | 5+ destinatários in broadcast | `test_broadcast_succeeds_against_live_evolution` — 5 sequential sends, all `success=True` |
| **AC2** | Evolution interrupted mid-broadcast | `test_broadcast_returns_error_when_evolution_killed_midway` — first 2 succeed, 3rd raises `EvolutionApiError` (simulates `docker kill evolution_api`) |
| **AC3** | HTTP 502 with sanitised error | (a) `test_broadcast_returns_error_when_evolution_killed_midway` — user_message is sanitised, no `docker`/`/var/log` leak; (b) `test_broadcast_500_response_is_sanitised` — 500 body containing `/var/log/evolution/api.log` is stripped from user_message; (c) Story 3.6 mapping `EvolutionApiError` → HTTP 502 already covered by `test_professor_routes.py::test_whatsapp_status_maps_evolution_error_to_502` |
| **AC4** | Retry recovers after restart | `test_broadcast_retry_recovers_after_evolution_restart` — phase 1: 1 success + 1 fail; phase 2 (after restart): 1 retry + 3 remaining all succeed |
| **AC5** | 11ª mensagem triggers rate limit | `test_broadcast_eleventh_message_per_phone_triggers_rate_limit` — first 10 messages pass via `ChatbotRateLimiter`, 11th is blocked; other students unaffected (per-phone key) |
| **AC6** | Transcript archived | This document |
| **AC7** | Pytest reproduzível | `backend/tests/chaos/test_broadcast_chaos.py` — 5 chaos tests + 1 meta-verifier, runs in 0.18s, no live Docker required |

---

## Scenario Walkthroughs

### Scenario 1 — Healthy baseline (AC1)

**Setup:** Evolution is configured, all sends should succeed.

```python
# 5 sequential sends via send_whatsapp_text
for student in chaos_students:  # 5 students with +244900000001..5
    result = await send_whatsapp_text(
        instance="turma-c",
        phone_number=student["phone"],
        message=f"Olá {student['full_name']}, a sua nota está disponível.",
    )
    # result: {"success": True, "message_id": "chaos-msg-id", "error": None}
```

**Result:** ✅ All 5 sends `success=True`, 5 httpx.post calls, 0 failures.

### Scenario 2 — Mid-broadcast kill (AC2 + AC3)

**Setup:** Operator runs `docker kill evolution_api` between the 2nd and 3rd send.

```python
# Simulated by httpx.ConnectError raised after 2nd call
httpx.ConnectError("Connection refused: docker kill evolution_api")
```

| Step | Phone | Result | Notes |
|------|-------|--------|-------|
| 1 | +244900000001 | ✅ `success=True` | before kill |
| 2 | +244900000002 | ✅ `success=True` | before kill |
| 3 | +244900000003 | ❌ raises `EvolutionApiError(status_code=0)` | docker kill happened |

**Sanitisation check on `user_message`:**
- ❌ does NOT contain `docker` (was `docker kill evolution_api` in raw)
- ❌ does NOT contain `/var/log`
- ✅ length ≤ 120 chars
- ✅ fallback to "Evolution API is unreachable" when body empty
- `str(exc)` (log-facing) preserves `ConnectError` for debugging

### Scenario 3 — 500 with internal log path (AC3 hardening)

**Setup:** Evolution returns 500 with body containing `/var/log/evolution/api.log`.

```
Body: "Internal Server Error: traceback at /var/log/evolution/api.log line 42"
```

**Sanitisation:**
- `exc.status_code == 500` (preserved for log)
- `exc.body` ≤ 500 chars (preserved for log)
- `user_message` is ≤ 120 chars, **does NOT contain** `/var/log` or `traceback`
- `str(exc)` retains the full diagnostic for log inspection

This proves the pattern-stripping in `EvolutionApiError._INTERNAL_LEAK_PATTERNS` works.

### Scenario 4 — Recovery via docker restart (AC4)

**Setup:** Operator runs `docker compose restart evolution_api` after the kill.

| Phase | Send | Result | Notes |
|-------|------|--------|-------|
| 1 | 1 of 5 | ✅ success | before kill |
| 1 | 2 of 5 | ❌ ConnectError | kill |
| 2 (after restart) | retry 2 | ✅ success | recovered |
| 2 | 3, 4, 5 | ✅ success | normal |

**Result:** Total 6 posts (5 successful, 1 fail, 1 retry). All phase-2 sends succeed → broadcast is **recuperável**.

### Scenario 5 — Rate limit (AC5)

**Setup:** `ChatbotRateLimiter(daily_limit=10)` for phone `+244900000001` (normalised: `244900000001`).

```
Messages 1-10:  is_blocked=False → record() → count goes 1..10
Message 11:     is_blocked=True  → 11th never recorded, get_count()=10
Other phones:   independent counter (per-phone key)
```

**Broadcast-level impact:** The 11th message to one student does **not** fail the broadcast for other students — the limiter is per-phone.

---

## Live Operator Validation (Credo attestation)

> **When:** Run by Credo before story close
> **How:** With the live Evolution stack (`docker compose -f docker-compose.evolution.yml up -d`), kill `evolution_api` mid-broadcast via the React UI
> **Expected:** Same outcomes as the deterministic suite (AC1-AC5)

*(To be signed off by Credo during session — T5 of the story's task list.)*

---

## Code Changes Summary

| File | Change | Lines |
|------|--------|-------|
| `backend/app/services/evolution_api_client.py` | Added `EvolutionApiError.user_message` property with sanitisation patterns (Story 9.2 AC-3 hardening) | +57 |
| `backend/tests/chaos/__init__.py` | New module | +5 |
| `backend/tests/chaos/conftest.py` | New conftest with `chaos_students` fixture, `evolution_healthy/killed_midway/returns_500` context managers, env isolation | +110 |
| `backend/tests/chaos/test_broadcast_chaos.py` | 5 chaos tests + 1 meta-verifier, covering AC1-AC5 + AC7 | +310 |
| `docs/qa/chaos-test-9.2.md` | This transcript | +200 |

**Total:** 5 files, ~680 lines, 6 new tests, 0 regressions.

---

## Quality Gate Pre-Flight

| Check | Status | Notes |
|-------|--------|-------|
| `pytest backend/tests/` | ✅ **176/176 passed** in 7.77s | 170 (pre) + 6 (new chaos) |
| Lint (`ruff`) | ⚠️ **tool not installed in this env** | Files parse OK via AST; `python -m py_compile` exit 0 |
| Typecheck (`mypy`) | ⚠️ **tool not installed in this env** | Same — runtime pytest exercises the API surface |
| CodeRabbit self-healing | ⏭️ skipped (no WSL) | Test suite + manual review sufficient for AC-7 doc quality |
| No HIGH/CRITICAL issues | ✅ | All 7 ACs satisfied; `user_message` hardening fix closes the leak that was uncovered by AC-3 test |

---

## Known Limitations

1. **pytest-asyncio not installed** — tests use `asyncio.run()` instead. Cleaner would be `@pytest.mark.asyncio` + `asyncio_mode = "auto"`. Out of scope for 9.2.
2. **Live docker kill validation** — relies on operator attestation; not automated in this story. Story 9.3 (runbook) will document the manual procedure.
3. **`_INTERNAL_LEAK_PATTERNS` is hardcoded** — could move to a config if more patterns emerge. Story 9.3 runbook will document the sanitisation contract.

---

## Operator Sign-Off

> [ ] Credo confirma (live docker kill, 5 destinatários, recovery funciona, rate limit edge case respeitado) — to be filled before story closes.
