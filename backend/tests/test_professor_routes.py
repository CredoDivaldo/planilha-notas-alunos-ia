"""Tests for the professor router (Story 8.2 — Epic 8).

Covers acceptance criteria AC1–AC5:

* AC1 — ``POST /api/v1/grades/match`` returns the documented shape
* AC2 — ``POST /api/v1/broadcast/`` returns portal/whatsapp/failure fields
* AC3 — ``GET /api/v1/whatsapp/status`` returns ``{connected, instance_name}``
* AC4 — dry-run / simulated lifecycle endpoints do not touch Evolution
* AC5 — Evolution 4xx surfaces as 502 with a sanitised detail

The Evolution HTTP path is exercised via ``monkeypatch`` on the
``evolution_api_client`` module functions — we don't need a live
container in unit tests.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import create_app
from backend.app.models import Base


# ---------------------------------------------------------------------------
# Fixtures (mirror the test_ingest.py pattern)
# ---------------------------------------------------------------------------


def _build_mem_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def client() -> TestClient:
    app = create_app()
    engine = _build_mem_engine()
    SessionLocal = sessionmaker(bind=engine)
    app.state.session_factory = SessionLocal
    app.state.engine = engine
    return TestClient(app)


# ---------------------------------------------------------------------------
# AC1 — /api/v1/grades/match
# ---------------------------------------------------------------------------


def test_match_empty_returns_zero_counts(client: TestClient) -> None:
    res = client.post("/api/v1/grades/match", json={})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body == {"matched": 0, "unmatched": 0, "invalid_phones": 0, "items": []}


def test_match_with_legacy_students_and_grades(client: TestClient) -> None:
    # Seed a student and a matching grade via direct SQL writes so we don't
    # need the upload endpoints to be wired through the API surface.
    from backend.app.models import LegacyGrade, LegacyStudent

    SessionLocal = client.app.state.session_factory
    with SessionLocal() as s:
        s.add(
            LegacyStudent(
                student_number="2001",
                name="Ana Silva",
                turma="10A",
                whatsapp="+244923456789",
            )
        )
        s.add(
            LegacyGrade(
                student_number="2001",
                name="Ana Silva",
                value="14.5",
            )
        )
        s.commit()

    res = client.post("/api/v1/grades/match", json={"context_id": None})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["matched"] == 1
    assert body["unmatched"] == 0
    assert body["invalid_phones"] == 0
    assert len(body["items"]) == 1
    assert body["items"][0]["numero_estudante"] == "2001"
    assert body["items"][0]["nome"] == "Ana Silva"
    assert body["items"][0]["nota"] == "14.5"


def test_match_invalid_phone_flagged(client: TestClient) -> None:
    """A student with a 3-digit phone is counted as invalid_phones."""
    from backend.app.models import LegacyGrade, LegacyStudent

    SessionLocal = client.app.state.session_factory
    with SessionLocal() as s:
        s.add(
            LegacyStudent(
                student_number="2002",
                name="Bruno Curto",
                turma="10A",
                whatsapp="123",  # invalid
            )
        )
        s.add(
            LegacyGrade(
                student_number="2002",
                name="Bruno Curto",
                value="12.0",
            )
        )
        s.commit()

    res = client.post("/api/v1/grades/match", json={})
    assert res.status_code == 200
    body = res.json()
    assert body["matched"] == 1
    assert body["invalid_phones"] == 1


# ---------------------------------------------------------------------------
# AC2 — /api/v1/broadcast/ (dry-run)
# ---------------------------------------------------------------------------


def test_broadcast_dry_run_returns_simulated(client: TestClient) -> None:
    """AC-4: dry-run returns the documented shape without touching Evolution."""
    res = client.post(
        "/api/v1/broadcast/",
        json={
            "context_id": 999,
            "dry_run": True,
            "channels": ["portal", "whatsapp"],
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["simulated"] is True
    assert body["total_recipients"] == 0
    assert body["channels"] == ["portal", "whatsapp"]


def test_broadcast_mode_simulation_also_dry(client: TestClient) -> None:
    """Legacy ``mode: 'simulation'`` field maps to dry-run."""
    res = client.post(
        "/api/v1/broadcast/",
        json={"context_id": 999, "mode": "simulation"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["simulated"] is True


def test_broadcast_real_without_teaching_assignment_returns_404(
    client: TestClient,
) -> None:
    """A real (non-dry) broadcast for a context with no grades returns 404."""
    res = client.post(
        "/api/v1/broadcast/",
        json={
            "context_id": 12345,
            "dry_run": False,
            "channels": ["portal"],
        },
    )
    assert res.status_code == 404
    assert "assignment" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# AC3 — /api/v1/whatsapp/status
# ---------------------------------------------------------------------------


def test_whatsapp_status_simulated_when_unconfigured(client: TestClient) -> None:
    """Without ``EVOLUTION_API_URL`` we get the simulated sentinel."""
    res = client.get("/api/v1/whatsapp/status")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["connected"] is False
    assert body["instance_name"]
    assert body["simulated"] is True


# ---------------------------------------------------------------------------
# AC4 — /api/v1/whatsapp/instance/{create,connect}
# ---------------------------------------------------------------------------


def test_whatsapp_instance_create_simulated(client: TestClient) -> None:
    res = client.post("/api/v1/whatsapp/instance/create")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "simulated"
    assert body["instance_name"]


def test_whatsapp_instance_connect_simulated(client: TestClient) -> None:
    res = client.get("/api/v1/whatsapp/instance/connect")
    assert res.status_code == 200
    body = res.json()
    assert body["simulated"] is True
    assert body["connected"] is False
    assert body["instance_name"]


# ---------------------------------------------------------------------------
# AC5 — Evolution 4xx surfaces as 502 with sanitised detail
# ---------------------------------------------------------------------------


def test_whatsapp_status_maps_evolution_error_to_502(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Story 3.6: 4xx/5xx from Evolution → 502 with short, sanitised message."""
    from backend.app.routers import professor as professor_module
    from backend.app.services import evolution_api_client

    async def _boom():
        raise evolution_api_client.EvolutionApiError(
            status_code=503, body="upstream down"
        )

    monkeypatch.setattr(evolution_api_client, "connection_state", _boom)
    # The router imports the symbol into its own namespace, so we must patch
    # both the source module and the router's reference.
    monkeypatch.setattr(professor_module, "connection_state", _boom)

    res = client.get("/api/v1/whatsapp/status")
    assert res.status_code == 502
    detail = res.json()["detail"]
    # Sanitised: no internal Python repr leaked
    assert "Traceback" not in detail
    assert "503" in detail
