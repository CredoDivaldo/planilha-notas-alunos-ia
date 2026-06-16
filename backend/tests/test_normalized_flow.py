"""End-to-end integration test for the normalized model flow.

Covers: professor creates context (provisions subject/class_group/
teaching_assignment/assessment_definitions), uploads students CSV
(students + class_enrollments), uploads grades CSV per component
(grade_entries), reads grades back, publishes (publication_snapshots),
and a student self-registers and reads published grades on the portal.
"""
from __future__ import annotations

import io
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text  # noqa: F401
from sqlalchemy.orm import sessionmaker

from backend.app.auth.password import hash_password
from backend.app.cli import bootstrap_db
from backend.app.main import create_app


@pytest.fixture()
def app_client(tmp_path):
    # Use the real production schema by applying Alembic migrations to a
    # temporary SQLite file (create_all diverges from migrations for some tables).
    db_file = tmp_path / "flow.db"
    db_url = f"sqlite:///{db_file}"
    bootstrap_db(db_url, force=True)
    engine = create_engine(db_url, connect_args={"check_same_thread": False})

    # Enforce foreign keys like the production engine does (catches FK bugs)
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_connection, _record):  # noqa: ANN001
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    # whatsapp_instance is added at runtime by the setup router; ensure it exists
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE users ADD COLUMN whatsapp_instance VARCHAR(120)"))
            conn.commit()
        except Exception:
            conn.rollback()
    app = create_app()
    app.state.engine = engine
    app.state.session_factory = sessionmaker(bind=engine)
    return TestClient(app), engine


def _make_professor(engine, user_id=1, name="Daniela Lima") -> str:
    """Insert a professor user + active session; return the bearer token."""
    now = datetime.now(UTC).replace(tzinfo=None)
    token = f"sess-prof-{user_id}"
    with engine.connect() as conn:
        conn.execute(text(
            "INSERT INTO users (id, username, password_hash, role, display_name, created_at, updated_at)"
            " VALUES (:id, :u, :ph, 'professor', :dn, :now, :now)"
        ), {"id": user_id, "u": f"prof{user_id}@ula.com", "ph": hash_password("Passw0rd"), "dn": name, "now": now})
        conn.execute(text(
            "INSERT INTO user_sessions (id, user_id, created_at, expires_at, is_active)"
            " VALUES (:sid, :uid, :now, :exp, 1)"
        ), {"sid": token, "uid": user_id, "now": now, "exp": now + timedelta(days=1)})
        conn.commit()
    return token


def _csv(text_data: str) -> dict:
    return {"file": ("data.csv", io.BytesIO(text_data.encode("utf-8")), "text/csv")}


def test_full_professor_and_student_flow(app_client):
    client, engine = app_client
    token = _make_professor(engine)
    auth = {"Authorization": f"Bearer {token}"}

    # 1) Create context with two components
    res = client.post("/academic-contexts/", headers=auth, json={
        "turma": "EI1M", "disciplina": "Programação",
        "components": [{"name": "P1", "weight": 50}, {"name": "P2", "weight": 50}],
    })
    assert res.status_code == 201, res.text
    ctx = res.json()
    ctx_id = ctx["id"]
    assert len(ctx["components"]) == 2

    # 2) Upload students roster (2 students — the 2nd caught the FK→users bug)
    students_csv = (
        "numero_estudante,nome,turma,whatsapp\n"
        "2026001,Credo Lopes,EI1M,244938745635\n"
        "2026002,Ana Silva,EI1M,244900000000\n"
    )
    res = client.post(f"/api/v1/students/upload?context_id={ctx_id}", headers=auth, files=_csv(students_csv))
    assert res.status_code == 200, res.text
    assert res.json()["count"] == 2

    # 3) Upload grades for component 0 (P1) and component 1 (P2)
    for comp_idx, nota in ((0, "16"), (1, "18")):
        grades_csv = f"numero_estudante,nome,nota\n2026001,Credo Lopes,{nota}\n"
        res = client.post(
            f"/api/v1/grades/upload?context_id={ctx_id}&component_id={comp_idx}",
            headers=auth, files=_csv(grades_csv),
        )
        assert res.status_code == 200, res.text
        assert res.json()["count"] == 1

    # 4) Read grades back — both students enrolled; first has both components
    res = client.get(f"/grades/?context_id={ctx_id}", headers=auth)
    assert res.status_code == 200, res.text
    rows = res.json()["students"]
    assert len(rows) == 2
    credo = next(r for r in rows if r["studentNumber"] == "2026001")
    assert float(credo["components"]["0"]["value"]) == 16.0
    assert float(credo["components"]["1"]["value"]) == 18.0
    assert credo["published"] is False
    # Regression: the grades upload must NOT wipe the roster phone
    assert credo["phone"] == "244938745635"

    # 5) Publish (portal channel) — creates publication_snapshots
    res = client.post("/api/v1/broadcast/", headers=auth, json={
        "context_id": ctx_id, "audience": "all", "channels": ["portal"],
        "message_template": "Olá {{nome}}, nota {{nota_final}}",
    })
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["portal_published"] == 1  # final grade 17, complete

    # 6) Student self-registers and reads published grades
    res = client.post("/auth/student/status", json={"student_number": "2026001"})
    assert res.status_code == 200
    assert res.json() == {"found_in_roster": True, "has_account": False}

    res = client.post("/auth/student/activate", json={
        "student_number": "2026001", "password": "Estud0nte", "confirm_password": "Estud0nte",
    })
    assert res.status_code == 201, res.text
    student_token = res.json()["access_token"]

    res = client.get("/api/v1/portal/me/grades", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200, res.text
    portal = res.json()
    assert portal["student_number"] == "2026001"
    assert len(portal["subjects"]) == 1
    subj = portal["subjects"][0]
    assert subj["disciplina"] == "Programação"
    assert subj["nota_final"] == 17.0
    assert subj["resultado"] == "aprovado"

    # 7) Professor creates a calendar event in the context → student sees it
    res = client.post("/api/v1/calendar/events", headers=auth, json={
        "title": "Exame Final", "date": "2026-07-01T10:00:00", "type": "exame",
        "context_id": str(ctx_id),
    })
    assert res.status_code == 201, res.text

    res = client.get("/api/v1/portal/me/calendar", headers={"Authorization": f"Bearer {student_token}"})
    assert res.status_code == 200, res.text
    events = res.json()["events"]
    assert any(e["title"] == "Exame Final" and e["date"] == "2026-07-01" for e in events)
