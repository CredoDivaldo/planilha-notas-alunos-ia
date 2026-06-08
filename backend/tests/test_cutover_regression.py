"""Story 8.6 — Cutover regression tests.

Three fast, deterministic assertions that prove:

1. The legacy Express surface (``/api/students/upload``) is fully removed —
   the path must return 404, not 200 and not 500.
2. The new FastAPI health endpoint (``/api/v1/health``) is live.
3. The new FastAPI WhatsApp status endpoint (``/api/v1/whatsapp/status``)
   returns the contract the dashboard badge depends on.

These tests are intentionally isolated from the rest of the suite so that
they fail loudly if anyone re-introduces a legacy route or breaks the new
prefix wiring.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app


def _client() -> TestClient:
    """Build a fresh app + TestClient pair to avoid cross-test pollution."""
    app = create_app(Settings(database_url="sqlite:///:memory:"))
    return TestClient(app)


def test_old_express_students_path_returns_404() -> None:
    """Legacy ``/api/students/upload`` must NOT serve a request.

    After the Story 8.5 cutover, the Express tree is gone. If this test
    ever returns 200 or 500, the legacy path has been re-introduced and
    the cutover has regressed.
    """
    with _client() as client:
        response = client.get("/api/students/upload")

    assert response.status_code == 404, (
        f"Legacy /api/students/upload should be 404 after cutover, "
        f"got {response.status_code}. Re-introducing this path is a regression."
    )


def test_new_fastapi_health_works() -> None:
    """``/api/v1/health`` must respond 200 with the documented payload."""
    with _client() as client:
        response = client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["api_prefix"] == "/api/v1"


def test_new_fastapi_whatsapp_status_works() -> None:
    """``/api/v1/whatsapp/status`` must respond 200 with ``connected`` field."""
    with _client() as client:
        response = client.get("/api/v1/whatsapp/status")

    assert response.status_code == 200
    payload = response.json()
    assert "connected" in payload, (
        f"whatsapp/status payload missing 'connected' key: {payload}"
    )
    assert isinstance(payload["connected"], bool)
