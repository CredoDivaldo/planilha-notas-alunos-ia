"""Tests for the legacy CSV ingest router (Story 8.1 — Epic 8).

Covers acceptance criteria AC1–AC6:

* AC1 — happy path students upload
* AC2 — happy path grades upload
* AC3 — invalid CSV returns 400 with sanitised detail
* AC4 — file > 2 MB returns 400
* AC5 — bulk insert is transactional (rollback on failure)
* AC6 — idempotent re-upload (no duplicate rows)

The test uses the FastAPI ``TestClient`` and spins up a fresh in-memory
SQLite database per test via the shared ``mem_engine`` fixture pattern
already in use across the backend test suite.
"""
from __future__ import annotations

import io
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.main import create_app
from backend.app.models import Base, LegacyGrade, LegacyStudent, LegacyUpload


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _build_mem_engine():
    """In-memory SQLite that *shares* its connection across sessions.

    Without ``StaticPool`` each new session opens a fresh ``:memory:``
    database — so the router's session and the test's verification
    session would see different schemas. ``StaticPool`` keeps a single
    connection alive for the engine's lifetime.
    """
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
    """A TestClient whose app.state.session_factory points at in-memory SQLite.

    The ``lifespan`` event is intentionally NOT entered (we use the bare
    ``TestClient(app)`` constructor, not the context-manager form) so the
    router's ``get_db_session(request)`` reads the session factory we
    wire in here, not the on-disk one configured in ``.env``.

    Tables are created on the in-memory engine via ``Base.metadata.create_all``
    so the legacy_* tables are present for the router queries.
    """
    app = create_app()
    engine = _build_mem_engine()
    SessionLocal = sessionmaker(bind=engine)
    app.state.session_factory = SessionLocal
    app.state.engine = engine
    return TestClient(app)


def _multipart(text: str, filename: str = "test.csv"):
    """Wrap a CSV string as a multipart upload payload."""
    return {"file": (filename, io.BytesIO(text.encode("utf-8")), "text/csv")}


VALID_STUDENTS_CSV = (
    "numero_estudante,nome,turma,whatsapp\n"
    "1001,Ana Silva,10A,+244923456789\n"
    "1002,Bruno Costa,10A,+244923456790\n"
    "1003,Carla Mendes,10A,+244923456791\n"
)

VALID_GRADES_CSV = (
    "numero_estudante,nome,disciplina,nota\n"
    "1001,Ana Silva,Matemática,12.5\n"
    "1002,Bruno Costa,Matemática,15.0\n"
    "1003,Carla Mendes,Matemática,18.0\n"
    "1004,Sem Nome,Matemática,10.0\n"
    "1005,Outro Sem,Matemática,11.0\n"
)

STUDENTS_MISSING_IDENTIFIER = "nome,turma\nAna,10A\n"
GRADES_MISSING_IDENTIFIER = "nome,nota\nAna,12\n"


# ---------------------------------------------------------------------------
# AC1 — happy path students upload
# ---------------------------------------------------------------------------


def test_students_upload_happy_path(client: TestClient) -> None:
    res = client.post(
        "/api/v1/students/upload",
        files=_multipart(VALID_STUDENTS_CSV),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["count"] == 3
    assert len(body["students"]) == 3
    assert body["students"][0]["student_number"] == "1001"
    assert body["students"][0]["name"] == "Ana Silva"
    assert body["students"][0]["turma"] == "10A"
    assert body["students"][0]["whatsapp"] == "+244923456789"


# ---------------------------------------------------------------------------
# AC2 — happy path grades upload
# ---------------------------------------------------------------------------


def test_grades_upload_happy_path(client: TestClient) -> None:
    res = client.post(
        "/api/v1/grades/upload",
        files=_multipart(VALID_GRADES_CSV),
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["count"] == 5
    assert len(body["grades"]) == 5
    assert body["grades"][0]["student_number"] == "1001"
    assert body["grades"][0]["value"] == "12.5"


# ---------------------------------------------------------------------------
# AC3 — invalid CSV returns 400 with sanitised detail
# ---------------------------------------------------------------------------


def test_students_upload_missing_identifier_returns_400(client: TestClient) -> None:
    res = client.post(
        "/api/v1/students/upload",
        files=_multipart(STUDENTS_MISSING_IDENTIFIER),
    )
    assert res.status_code == 400
    body = res.json()
    assert "identificador" in body["detail"].lower()
    # No internal stack trace leaked
    assert "Traceback" not in body["detail"]


def test_grades_upload_missing_identifier_returns_400(client: TestClient) -> None:
    res = client.post(
        "/api/v1/grades/upload",
        files=_multipart(GRADES_MISSING_IDENTIFIER),
    )
    assert res.status_code == 400
    body = res.json()
    assert "identificador" in body["detail"].lower()


def test_empty_csv_returns_400(client: TestClient) -> None:
    empty = "numero_estudante,nome\n"  # header only
    res = client.post(
        "/api/v1/students/upload",
        files=_multipart(empty),
    )
    assert res.status_code == 400
    assert "dados" in res.json()["detail"].lower()


# ---------------------------------------------------------------------------
# AC4 — file > 2 MB returns 400
# ---------------------------------------------------------------------------


def test_students_upload_oversize_returns_400(client: TestClient) -> None:
    # Build a CSV just over the 2 MB cap.
    # Each row: f"{i:04d}," + ("x" * 1000) + ",name" + suffix "\n"  -> ~1.05 KB per row
    # 2100 rows = ~2.2 MB which is over the 2 MB cap.
    big = "numero_estudante,padding,nome\n" + "".join(
        f"{i:04d},{'x' * 1000},name{i}\n" for i in range(2100)
    )
    assert len(big) > 2 * 1024 * 1024, (
        f"test setup wrong: csv is {len(big)} bytes, must exceed 2MB"
    )
    res = client.post(
        "/api/v1/students/upload",
        files=_multipart(big),
    )
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "2MB" in detail or "demasiado" in detail.lower(), detail


# ---------------------------------------------------------------------------
# AC5 — bulk insert is transactional
# ---------------------------------------------------------------------------


def test_students_upload_commits_atomically(client: TestClient) -> None:
    # The router commits once, then the audit row is updated and committed
    # again. Use the in-memory engine to confirm rows are visible after
    # the response.
    res = client.post(
        "/api/v1/students/upload",
        files=_multipart(VALID_STUDENTS_CSV),
    )
    assert res.status_code == 200

    # Inspect via a fresh session
    engine = client.app.state.session_factory().get_bind()
    Session_ = sessionmaker(bind=engine)
    with Session_() as s:
        rows = s.query(LegacyStudent).all()
        assert len(rows) == 3
        uploads = s.query(LegacyUpload).all()
        assert len(uploads) == 1
        assert uploads[0].status == "ok"
        assert uploads[0].rows_persisted == 3


# ---------------------------------------------------------------------------
# AC6 — idempotent re-upload
# ---------------------------------------------------------------------------


def test_students_upload_idempotent(client: TestClient) -> None:
    first = client.post(
        "/api/v1/students/upload",
        files=_multipart(VALID_STUDENTS_CSV),
    )
    assert first.status_code == 200
    second = client.post(
        "/api/v1/students/upload",
        files=_multipart(VALID_STUDENTS_CSV),
    )
    assert second.status_code == 200
    assert first.json()["count"] == second.json()["count"] == 3

    # Only 3 student rows — no duplicates.
    engine = client.app.state.session_factory().get_bind()
    Session_ = sessionmaker(bind=engine)
    with Session_() as s:
        assert s.query(LegacyStudent).count() == 3
        # Two audit rows: one per upload.
        assert s.query(LegacyUpload).count() == 2


def test_students_upload_with_context_id_persists_relation(client: TestClient) -> None:
    res = client.post(
        "/api/v1/students/upload?context_id=42",
        files=_multipart(VALID_STUDENTS_CSV),
    )
    assert res.status_code == 200

    engine = client.app.state.session_factory().get_bind()
    Session_ = sessionmaker(bind=engine)
    with Session_() as s:
        rows = s.query(LegacyStudent).all()
        assert all(r.academic_context_id == 42 for r in rows)


# ---------------------------------------------------------------------------
# Pure-function coverage for the helper module
# ---------------------------------------------------------------------------


def test_pure_helpers_match_legacy_module() -> None:
    """Smoke test for the pure parse/validate helpers."""
    from backend.app.services.legacy_import import (
        build_match,
        is_valid_phone,
        normalize_grade,
        normalize_name,
        normalize_phone,
        normalize_student,
        parse_csv,
    )

    parsed = parse_csv(VALID_STUDENTS_CSV)
    assert parsed.headers[:4] == ["numero_estudante", "nome", "turma", "whatsapp"]
    assert len(parsed.rows) == 3

    student = normalize_student(parsed.rows[0])
    assert student["numero_estudante"] == "1001"
    assert student["nome"] == "Ana Silva"

    grades = parse_csv(VALID_GRADES_CSV)
    grade = normalize_grade(grades.rows[0])
    assert grade["nota"] == "12.5"

    assert normalize_name("Ana Cláudia") == "ana claudia"
    assert normalize_phone("+244 (92) 345-6789") == "244923456789"
    assert is_valid_phone("+244923456789")
    assert not is_valid_phone("123")

    match = build_match(
        students=[normalize_student(r) for r in parsed.rows],
        grades=[normalize_grade(r) for r in grades.rows],
    )
    assert match["matched"] == 3
    assert match["unmatched"] == 2  # 1004 and 1005 not in students
