"""Tests for the academic provisioning service (normalized model).

Verifies find-or-create idempotency and the full chain:
professor → subject/class_group → teaching_assignment → components →
student → enrollment → grade entry.
"""
from __future__ import annotations

from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool

from backend.app.models import Base
from backend.app.services import academic_provisioning as ap


def _mem_engine():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def _pragmas(dbapi_connection, _record):  # noqa: ANN001
        cur = dbapi_connection.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    Base.metadata.create_all(engine)
    return engine


def test_provisioning_full_chain_and_idempotency():
    engine = _mem_engine()
    with engine.connect() as conn:
        prof = ap.ensure_professor(conn, user_id=1, name="Daniela Lima")
        assert ap.ensure_professor(conn, user_id=1, name="Daniela Lima") == prof  # idempotent

        subject = ap.ensure_subject(conn, "Programação")
        assert ap.ensure_subject(conn, "Programação") == subject
        cg = ap.ensure_class_group(conn, "EI1M")
        assert ap.ensure_class_group(conn, "EI1M") == cg

        ta = ap.ensure_teaching_assignment(conn, prof, subject, cg, semester_id=1, shift_id=1)
        assert ap.ensure_teaching_assignment(conn, prof, subject, cg, 1, 1) == ta

        comps = [{"name": "P1", "weight": 50}, {"name": "P2", "weight": 50}]
        ad_ids = ap.sync_components(conn, ta, comps)
        assert len(ad_ids) == 2
        # idempotent: same ids on re-sync
        assert ap.sync_components(conn, ta, comps) == ad_ids
        assert ap.get_component_ids(conn, ta) == ad_ids

        student = ap.ensure_student(conn, "2026001", "Credo Lopes", "244938745635", cg)
        assert ap.ensure_student(conn, "2026001", "Credo Lopes", "244938745635", cg) == student

        enr = ap.enroll_student(conn, academic_context_id=1, student_id=student)
        assert ap.enroll_student(conn, 1, student) == enr  # idempotent

        g1 = ap.upsert_grade(conn, student, ta, ad_ids[0], 17, user_id=1)
        # update same grade entry
        assert ap.upsert_grade(conn, student, ta, ad_ids[0], 18, user_id=1) == g1
        ap.upsert_grade(conn, student, ta, ad_ids[1], 15, user_id=1)

        rows = conn.execute(
            text(
                "SELECT assessment_definition_id, raw_value, status FROM grade_entries"
                " WHERE student_id = :s ORDER BY assessment_definition_id"
            ),
            {"s": student},
        ).fetchall()
        assert len(rows) == 2
        assert float(rows[0][1]) == 18.0  # updated value
        assert rows[0][2] == "validated"


def test_sync_components_shrink_removes_surplus():
    engine = _mem_engine()
    with engine.connect() as conn:
        prof = ap.ensure_professor(conn, 1, "P")
        subj = ap.ensure_subject(conn, "Mat")
        cg = ap.ensure_class_group(conn, "10A")
        ta = ap.ensure_teaching_assignment(conn, prof, subj, cg, 1, 1)
        ids3 = ap.sync_components(conn, ta, [{"name": "A", "weight": 33}, {"name": "B", "weight": 33}, {"name": "C", "weight": 34}])
        assert len(ids3) == 3
        # shrink to 2 → surplus removed
        ids2 = ap.sync_components(conn, ta, [{"name": "A", "weight": 50}, {"name": "B", "weight": 50}])
        assert len(ids2) == 2
        assert ap.get_component_ids(conn, ta) == ids2
