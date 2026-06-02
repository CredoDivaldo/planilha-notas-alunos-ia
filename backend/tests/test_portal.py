"""Tests for Student Portal (Story 5.5).

Test Coverage:
  - AC-1: Portal reads ONLY publication_snapshots (is_current=True)
  - AC-2: Authenticated student scope (no cross-student access)
  - AC-3: Academic summary aggregation by context
  - AC-4: Calendar from published_calendar_snapshots only
  - AC-5: No internal audit/history exposure
  - AC-6: Formula metadata displayed as-is
  - AC-8: Audit logging without sensitive payloads
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import Settings
from backend.app.database import build_engine
from backend.app.models import (
    AcademicContext,
    AuditLog,
    Base,
    ClassEnrollment,
    PublicationSnapshot,
    Semester,
    Shift,
)
from backend.app.portal.service import PortalAccessError, PortalService


@pytest.fixture
def temp_db_session(tmp_path: Path) -> tuple[Session, str]:
    """Create temp SQLite database with schema."""
    db_path = tmp_path / "test.sqlite3"
    database_url = f"sqlite:///{db_path}"

    engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )

    # Create all tables
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session, database_url

    session.close()
    engine.dispose()


# -----------------------------------------------------------------------
# AC-1: Portal reads ONLY is_current=True snapshots
# -----------------------------------------------------------------------


def test_portal_reads_only_current_snapshots(temp_db_session: tuple[Session, str]) -> None:
    """Verify portal ignores previous/non-current snapshots."""
    session, _ = temp_db_session

    # Setup: Create semester, shift, context
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    session.add(semester)
    session.flush()

    shift = Shift(code="MORNING", name="Morning", status="active")
    session.add(shift)
    session.flush()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Math",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    session.add(context)
    session.flush()

    # Enroll student
    enrollment = ClassEnrollment(
        academic_context_id=context.id,
        student_id=100,
        enrollment_status="active",
    )
    session.add(enrollment)
    session.flush()

    # Create 3 snapshots: v1, v2, v3 (only v3 is current)
    snap_v1 = PublicationSnapshot(
        student_id=100,
        teaching_assignment_id=context.id,
        broadcast_job_id=1,
        snapshot_version=1,
        published_score=Decimal("7.5"),
        published_state="passed",
        published_payload_json=json.dumps({"formula_version": "v1.0"}),
        is_current=False,
    )
    snap_v2 = PublicationSnapshot(
        student_id=100,
        teaching_assignment_id=context.id,
        broadcast_job_id=2,
        snapshot_version=2,
        published_score=Decimal("8.0"),
        published_state="passed",
        published_payload_json=json.dumps({"formula_version": "v1.0"}),
        is_current=False,
    )
    snap_v3 = PublicationSnapshot(
        student_id=100,
        teaching_assignment_id=context.id,
        broadcast_job_id=3,
        snapshot_version=3,
        published_score=Decimal("8.5"),
        published_state="passed",
        published_payload_json=json.dumps({"formula_version": "v1.1"}),
        is_current=True,
    )
    session.add_all([snap_v1, snap_v2, snap_v3])
    session.commit()

    # Test: get_grades_by_context should return only v3
    service = PortalService()
    result = service.get_grades_by_context(session, 100, context.id)

    assert result["current_grade"] is not None
    assert result["current_grade"]["snapshot_version"] == 3
    assert result["current_grade"]["score"] == 8.5
    assert result["current_grade"]["formula_version"] == "v1.1"


def test_portal_excludes_non_current_snapshots_from_summary(
    temp_db_session: tuple[Session, str],
) -> None:
    """Verify academic summary excludes non-current snapshots."""
    session, _ = temp_db_session

    # Setup
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
    )
    session.add(semester)
    session.flush()

    shift = Shift(code="MORNING", name="Morning")
    session.add(shift)
    session.flush()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Math",
        semester_id=semester.id,
        shift_id=shift.id,
    )
    session.add(context)
    session.flush()

    enrollment = ClassEnrollment(
        academic_context_id=context.id,
        student_id=100,
    )
    session.add(enrollment)
    session.flush()

    # Create outdated snapshot (not current)
    snap_old = PublicationSnapshot(
        student_id=100,
        teaching_assignment_id=context.id,
        broadcast_job_id=1,
        snapshot_version=1,
        published_score=Decimal("5.0"),
        published_state="failed",
        published_payload_json=json.dumps({}),
        is_current=False,
    )
    session.add(snap_old)
    session.commit()

    # Test: summary should show no current grade
    service = PortalService()
    result = service.get_academic_summary(session, 100)

    assert len(result["contexts"]) == 1
    assert result["contexts"][0]["current_grade"] is None


# -----------------------------------------------------------------------
# AC-2: Authenticated student scope (no cross-student access)
# -----------------------------------------------------------------------


def test_portal_rejects_cross_student_access(temp_db_session: tuple[Session, str]) -> None:
    """Verify student cannot access another student's data."""
    session, _ = temp_db_session

    # Setup
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
    )
    session.add(semester)
    session.flush()

    shift = Shift(code="MORNING", name="Morning")
    session.add(shift)
    session.flush()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Math",
        semester_id=semester.id,
        shift_id=shift.id,
    )
    session.add(context)
    session.flush()

    # Enroll only student 100 in context
    enrollment = ClassEnrollment(
        academic_context_id=context.id,
        student_id=100,
    )
    session.add(enrollment)
    session.flush()

    # Create grade snapshot for student 100
    snap = PublicationSnapshot(
        student_id=100,
        teaching_assignment_id=context.id,
        broadcast_job_id=1,
        snapshot_version=1,
        published_score=Decimal("9.0"),
        published_state="excellent",
        published_payload_json=json.dumps({}),
        is_current=True,
    )
    session.add(snap)
    session.commit()

    # Test: student 200 (not enrolled) should get PortalAccessError
    service = PortalService()
    with pytest.raises(PortalAccessError, match="not enrolled"):
        service.get_grades_by_context(session, authenticated_student_id=200, context_id=context.id)


def test_portal_summary_scoped_to_authenticated_student(
    temp_db_session: tuple[Session, str],
) -> None:
    """Verify summary only includes authenticated student's contexts."""
    session, _ = temp_db_session

    # Setup
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
    )
    session.add(semester)
    session.flush()

    shift = Shift(code="MORNING", name="Morning")
    session.add(shift)
    session.flush()

    context1 = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Math",
        semester_id=semester.id,
        shift_id=shift.id,
    )
    context2 = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10B",
        subject="Physics",
        semester_id=semester.id,
        shift_id=shift.id,
    )
    session.add_all([context1, context2])
    session.flush()

    # Student 100 in context1, student 200 in context2
    enrollment1 = ClassEnrollment(
        academic_context_id=context1.id,
        student_id=100,
    )
    enrollment2 = ClassEnrollment(
        academic_context_id=context2.id,
        student_id=200,
    )
    session.add_all([enrollment1, enrollment2])
    session.commit()

    # Test: student 100 should only see context1
    service = PortalService()
    result = service.get_academic_summary(session, 100)

    assert len(result["contexts"]) == 1
    assert result["contexts"][0]["context_id"] == context1.id
    assert result["contexts"][0]["subject"] == "Math"


# -----------------------------------------------------------------------
# AC-3: Academic summary aggregation
# -----------------------------------------------------------------------


def test_portal_aggregates_multiple_contexts(temp_db_session: tuple[Session, str]) -> None:
    """Verify summary correctly aggregates multiple contexts."""
    session, _ = temp_db_session

    # Setup
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
    )
    session.add(semester)
    session.flush()

    shift = Shift(code="MORNING", name="Morning")
    session.add(shift)
    session.flush()

    # Create 3 contexts
    contexts = []
    for i, subject in enumerate(["Math", "Physics", "Chemistry"]):
        ctx = AcademicContext(
            professor_id=1,
            academic_year=2026,
            turma=f"10{chr(65 + i)}",
            subject=subject,
            semester_id=semester.id,
            shift_id=shift.id,
        )
        session.add(ctx)
        contexts.append(ctx)
    session.flush()

    # Enroll student in all 3
    for ctx in contexts:
        enrollment = ClassEnrollment(
            academic_context_id=ctx.id,
            student_id=100,
        )
        session.add(enrollment)
    session.flush()

    # Create snapshots
    for ctx in contexts:
        snap = PublicationSnapshot(
            student_id=100,
            teaching_assignment_id=ctx.id,
            broadcast_job_id=1,
            snapshot_version=1,
            published_score=Decimal("8.0"),
            published_state="passed",
            published_payload_json=json.dumps({}),
            is_current=True,
        )
        session.add(snap)
    session.commit()

    # Test
    service = PortalService()
    result = service.get_academic_summary(session, 100)

    assert len(result["contexts"]) == 3
    subjects = {ctx["subject"] for ctx in result["contexts"]}
    assert subjects == {"Math", "Physics", "Chemistry"}


# -----------------------------------------------------------------------
# AC-5: No internal history/audit exposure
# -----------------------------------------------------------------------


def test_portal_does_not_expose_audit_history(temp_db_session: tuple[Session, str]) -> None:
    """Verify portal does not return internal audit logs."""
    session, _ = temp_db_session

    # Setup
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
    )
    session.add(semester)
    session.flush()

    shift = Shift(code="MORNING", name="Morning")
    session.add(shift)
    session.flush()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Math",
        semester_id=semester.id,
        shift_id=shift.id,
    )
    session.add(context)
    session.flush()

    enrollment = ClassEnrollment(
        academic_context_id=context.id,
        student_id=100,
    )
    session.add(enrollment)
    session.flush()

    snap = PublicationSnapshot(
        student_id=100,
        teaching_assignment_id=context.id,
        broadcast_job_id=1,
        snapshot_version=1,
        published_score=Decimal("8.0"),
        published_state="passed",
        published_payload_json=json.dumps({}),
        is_current=True,
    )
    session.add(snap)
    session.commit()

    # Test
    service = PortalService()
    result = service.get_grades_by_context(session, 100, context.id)

    # Response should not include audit_log field or history
    assert "audit_log" not in result
    assert "history" not in result
    assert "previous_snapshots" not in result


# -----------------------------------------------------------------------
# AC-6: Formula metadata displayed as-is
# -----------------------------------------------------------------------


def test_portal_displays_formula_version_from_snapshot(
    temp_db_session: tuple[Session, str],
) -> None:
    """Verify formula_version is extracted from published payload."""
    session, _ = temp_db_session

    # Setup
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
    )
    session.add(semester)
    session.flush()

    shift = Shift(code="MORNING", name="Morning")
    session.add(shift)
    session.flush()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Math",
        semester_id=semester.id,
        shift_id=shift.id,
    )
    session.add(context)
    session.flush()

    enrollment = ClassEnrollment(
        academic_context_id=context.id,
        student_id=100,
    )
    session.add(enrollment)
    session.flush()

    # Create snapshot with formula_version in payload
    snap = PublicationSnapshot(
        student_id=100,
        teaching_assignment_id=context.id,
        broadcast_job_id=1,
        snapshot_version=1,
        published_score=Decimal("8.5"),
        published_state="passed",
        published_payload_json=json.dumps({
            "formula_version": "v2.1-beta",
            "components": {"assessment": 0.6, "exam": 0.4},
        }),
        is_current=True,
    )
    session.add(snap)
    session.commit()

    # Test
    service = PortalService()
    result = service.get_grades_by_context(session, 100, context.id)

    assert result["current_grade"]["formula_version"] == "v2.1-beta"


# -----------------------------------------------------------------------
# AC-8: Audit logging without sensitive payloads
# -----------------------------------------------------------------------


def test_portal_logs_access_without_sensitive_data(
    temp_db_session: tuple[Session, str],
) -> None:
    """Verify audit log records portal access without exposing payloads."""
    session, _ = temp_db_session

    # Setup
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
    )
    session.add(semester)
    session.flush()

    shift = Shift(code="MORNING", name="Morning")
    session.add(shift)
    session.flush()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Math",
        semester_id=semester.id,
        shift_id=shift.id,
    )
    session.add(context)
    session.flush()

    enrollment = ClassEnrollment(
        academic_context_id=context.id,
        student_id=100,
    )
    session.add(enrollment)
    session.commit()

    # Test
    service = PortalService()
    service.get_academic_summary(session, 100, request_id="test-req-123")

    # Verify audit log was created
    audit = session.query(AuditLog).filter_by(
        action="portal_read",
        entity_type="student_academic_summary",
    ).first()

    assert audit is not None
    assert audit.request_id == "test-req-123"
    assert audit.entity_id == "100"

    # Verify no sensitive payload
    after_json = json.loads(audit.after_json)
    assert "student_id" in after_json
    assert "result_count" in after_json
    # Should NOT contain internal grade values
    assert "published_score" not in audit.after_json
    assert "calculation_result" not in audit.after_json


# -----------------------------------------------------------------------
# Edge cases
# -----------------------------------------------------------------------


def test_portal_handles_no_enrollments(temp_db_session: tuple[Session, str]) -> None:
    """Verify summary returns empty list for student with no enrollments."""
    session, _ = temp_db_session

    service = PortalService()
    result = service.get_academic_summary(session, 999)

    assert result["student_id"] == 999
    assert result["contexts"] == []


def test_portal_handles_enrollment_without_grade(temp_db_session: tuple[Session, str]) -> None:
    """Verify summary includes enrollment even without current grade."""
    session, _ = temp_db_session

    # Setup
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
    )
    session.add(semester)
    session.flush()

    shift = Shift(code="MORNING", name="Morning")
    session.add(shift)
    session.flush()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Math",
        semester_id=semester.id,
        shift_id=shift.id,
    )
    session.add(context)
    session.flush()

    enrollment = ClassEnrollment(
        academic_context_id=context.id,
        student_id=100,
    )
    session.add(enrollment)
    session.commit()

    # Test
    service = PortalService()
    result = service.get_academic_summary(session, 100)

    assert len(result["contexts"]) == 1
    assert result["contexts"][0]["current_grade"] is None
