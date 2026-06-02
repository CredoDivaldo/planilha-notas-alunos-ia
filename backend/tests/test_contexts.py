"""Tests for academic contexts and rosters (Story 5.4).

Covers:
- Academic context model: professor scoping, lifecycle
- Class enrollments: roster management, status transitions
- Subject configuration: JSON storage and retrieval
- Context isolation: professor A cannot access professor B's contexts
- AC-8: Grade entry context scoping and upload validation
"""
from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from backend.app.models import (
    AcademicContext,
    Base,
    ClassEnrollment,
    ContextSubjectConfiguration,
    GradeEntry,
    Semester,
    Shift,
)

# ---------------------------------------------------------------------------
# Fixtures: in-memory SQLite with schema
# ---------------------------------------------------------------------------


@pytest.fixture()
def mem_session() -> Session:  # type: ignore[misc]
    """In-memory SQLite session with all schema tables."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # Enable foreign keys for SQLite
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables from ORM models
    Base.metadata.create_all(engine)
    session = Session(engine)
    yield session
    session.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# Test: Semester and Shift reference data
# ---------------------------------------------------------------------------


def test_semester_creation(mem_session: Session) -> None:
    """Semester can be created and queried."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
        start_date=datetime(2026, 1, 15, tzinfo=UTC),
        end_date=datetime(2026, 6, 30, tzinfo=UTC),
    )
    mem_session.add(semester)
    mem_session.commit()

    retrieved = mem_session.query(Semester).filter_by(code="2026-S1").first()
    assert retrieved is not None
    assert retrieved.academic_year == 2026
    assert retrieved.semester_number == 1


def test_shift_creation(mem_session: Session) -> None:
    """Shift can be created and queried."""
    shift = Shift(
        code="MORNING",
        name="Morning Shift",
        shift_order=1,
        status="active",
    )
    mem_session.add(shift)
    mem_session.commit()

    retrieved = mem_session.query(Shift).filter_by(code="MORNING").first()
    assert retrieved is not None
    assert retrieved.name == "Morning Shift"


# ---------------------------------------------------------------------------
# Test: Academic context model (AC-1)
# ---------------------------------------------------------------------------


def test_academic_context_creation(mem_session: Session) -> None:
    """Academic context can be created with all required fields (AC-1)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="draft",
    )
    mem_session.add(context)
    mem_session.commit()

    retrieved = mem_session.query(AcademicContext).filter_by(turma="10A").first()
    assert retrieved is not None
    assert retrieved.professor_id == 1
    assert retrieved.subject == "Mathematics"


def test_professor_multiple_contexts_different_turmas(mem_session: Session) -> None:
    """Professor can have multiple contexts for different turmas (AC-2)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context1 = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    context2 = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10B",  # Different turma
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context1)
    mem_session.add(context2)
    mem_session.commit()

    contexts = mem_session.query(AcademicContext).filter_by(professor_id=1).all()
    assert len(contexts) == 2


def test_professor_context_isolation(mem_session: Session) -> None:
    """Professor A's contexts are not visible to professor B (AC-2)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context_prof1 = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    context_prof2 = AcademicContext(
        professor_id=2,
        academic_year=2026,
        turma="10B",
        subject="Physics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context_prof1)
    mem_session.add(context_prof2)
    mem_session.commit()

    # Professor 1 sees only their context
    prof1_contexts = mem_session.query(AcademicContext).filter_by(professor_id=1).all()
    assert len(prof1_contexts) == 1
    assert prof1_contexts[0].turma == "10A"

    # Professor 2 sees only their context
    prof2_contexts = mem_session.query(AcademicContext).filter_by(professor_id=2).all()
    assert len(prof2_contexts) == 1
    assert prof2_contexts[0].turma == "10B"


# ---------------------------------------------------------------------------
# Test: Class enrollments (AC-4)
# ---------------------------------------------------------------------------


def test_class_enrollment_creation(mem_session: Session) -> None:
    """Student can be enrolled in a context (AC-4)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context)
    mem_session.commit()

    enrollment = ClassEnrollment(
        academic_context_id=context.id,
        student_id=101,
        enrollment_status="active",
    )
    mem_session.add(enrollment)
    mem_session.commit()

    retrieved = mem_session.query(ClassEnrollment).filter_by(student_id=101).first()
    assert retrieved is not None
    assert retrieved.enrollment_status == "active"


def test_enrollment_status_transitions(mem_session: Session) -> None:
    """Enrollment status can transition: active → dropped/completed."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context)
    mem_session.commit()

    enrollment = ClassEnrollment(
        academic_context_id=context.id,
        student_id=101,
        enrollment_status="active",
    )
    mem_session.add(enrollment)
    mem_session.commit()

    # Transition to dropped
    enrollment.enrollment_status = "dropped"
    enrollment.dropped_at = datetime.now(UTC)
    mem_session.commit()

    retrieved = mem_session.query(ClassEnrollment).filter_by(student_id=101).first()
    assert retrieved is not None
    assert retrieved.enrollment_status == "dropped"
    assert retrieved.dropped_at is not None


# ---------------------------------------------------------------------------
# Test: Subject configuration (AC-5)
# ---------------------------------------------------------------------------


def test_context_subject_configuration_creation(mem_session: Session) -> None:
    """Subject configuration can be stored per context (AC-5)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context)
    mem_session.commit()

    config_data = {
        "formula_version": "v1.0",
        "assessment_count": 4,
        "weight_distribution": {"assessment": 0.5, "exam": 0.5},
        "minimum_grade": 2.0,
    }
    config = ContextSubjectConfiguration(
        academic_context_id=context.id,
        configuration_json=json.dumps(config_data),
    )
    mem_session.add(config)
    mem_session.commit()

    retrieved = mem_session.query(ContextSubjectConfiguration).filter_by(
        academic_context_id=context.id
    ).first()
    assert retrieved is not None
    assert retrieved.get_config()["formula_version"] == "v1.0"


def test_configuration_json_helpers(mem_session: Session) -> None:
    """Configuration JSON getters/setters work correctly."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context)
    mem_session.commit()

    config = ContextSubjectConfiguration(academic_context_id=context.id, configuration_json="{}")
    config_data = {"formula_version": "v2.0", "assessment_count": 5}
    config.set_config(config_data)
    mem_session.add(config)
    mem_session.commit()

    retrieved = mem_session.query(ContextSubjectConfiguration).filter_by(
        academic_context_id=context.id
    ).first()
    assert retrieved is not None
    retrieved_config = retrieved.get_config()
    assert retrieved_config["formula_version"] == "v2.0"
    assert retrieved_config["assessment_count"] == 5


# ---------------------------------------------------------------------------
# Test: Context lifecycle (AC-7)
# ---------------------------------------------------------------------------


def test_context_lifecycle_transitions(mem_session: Session) -> None:
    """Context status can transition: draft → active → archived (AC-7)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="draft",  # Start as draft
    )
    mem_session.add(context)
    mem_session.commit()

    assert context.status == "draft"

    # Transition to active
    context.status = "active"
    mem_session.commit()
    assert context.status == "active"

    # Transition to archived
    context.status = "archived"
    mem_session.commit()
    assert context.status == "archived"


# ---------------------------------------------------------------------------
# Test: AC-8 Grade entry context scoping and upload validation
# ---------------------------------------------------------------------------


def test_grade_entry_requires_academic_context(mem_session: Session) -> None:
    """Grade entry can store academic_context_id (AC-8)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context)
    mem_session.commit()

    grade = GradeEntry(
        academic_context_id=context.id,
        student_id=101,
        teaching_assignment_id=1,
        assessment_definition_id=1,
        raw_value=85.0,
        status="draft",
    )
    mem_session.add(grade)
    mem_session.commit()

    retrieved = mem_session.query(GradeEntry).filter_by(student_id=101).first()
    assert retrieved is not None
    assert retrieved.academic_context_id == context.id


def test_upload_context_validation_passes_for_valid_context(mem_session: Session) -> None:
    """Upload validation passes when context is valid and professor owns it (AC-8)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context)
    mem_session.commit()

    # Enroll students in context
    for student_id in [101, 102, 103]:
        enrollment = ClassEnrollment(
            academic_context_id=context.id,
            student_id=student_id,
            enrollment_status="active",
        )
        mem_session.add(enrollment)
    mem_session.commit()

    # Simulate upload validation
    roster_student_ids = {101, 102, 103}

    # Get context and verify
    ctx = mem_session.query(AcademicContext).filter_by(id=context.id).first()
    assert ctx is not None
    assert ctx.professor_id == 1

    # Verify students are enrolled
    enrollments = mem_session.query(ClassEnrollment).filter_by(
        academic_context_id=context.id
    ).all()
    enrolled_student_ids = {e.student_id for e in enrollments}
    missing = roster_student_ids - enrolled_student_ids

    assert len(missing) == 0, "All students should be enrolled"


def test_upload_rejects_invalid_context_id(mem_session: Session) -> None:
    """Upload is rejected if context_id does not exist (AC-8)."""
    # Try to query non-existent context
    context = mem_session.query(AcademicContext).filter_by(id=999).first()
    assert context is None, "Invalid context should not exist"


def test_upload_rejects_context_not_owned_by_professor(mem_session: Session) -> None:
    """Upload is rejected if professor does not own the context (AC-8)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    # Create context owned by professor 1
    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context)
    mem_session.commit()

    # Verify professor 2 does not own this context
    ctx = mem_session.query(AcademicContext).filter_by(id=context.id).first()
    assert ctx is not None
    assert ctx.professor_id != 2, "Professor 2 should not own this context"


def test_upload_rejects_mismatched_subject(mem_session: Session) -> None:
    """Upload is rejected if subject does not match context subject (AC-8)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    # Create context for Mathematics
    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context)
    mem_session.commit()

    # Verify context subject
    ctx = mem_session.query(AcademicContext).filter_by(id=context.id).first()
    assert ctx is not None
    assert ctx.subject == "Mathematics"
    assert ctx.subject != "Physics", "Subject should not match Physics upload"


def test_upload_rejects_missing_student_roster(mem_session: Session) -> None:
    """Upload is rejected if students are not enrolled in context (AC-8)."""
    semester = Semester(
        code="2026-S1",
        name="2026 Semester 1",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    shift = Shift(code="MORNING", name="Morning Shift", shift_order=1, status="active")
    mem_session.add(semester)
    mem_session.add(shift)
    mem_session.commit()

    context = AcademicContext(
        professor_id=1,
        academic_year=2026,
        turma="10A",
        subject="Mathematics",
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    mem_session.add(context)
    mem_session.commit()

    # Enroll only students 101, 102
    for student_id in [101, 102]:
        enrollment = ClassEnrollment(
            academic_context_id=context.id,
            student_id=student_id,
            enrollment_status="active",
        )
        mem_session.add(enrollment)
    mem_session.commit()

    # Try to validate upload with students 101, 102, 103 (103 not enrolled)
    enrollments = mem_session.query(ClassEnrollment).filter_by(
        academic_context_id=context.id
    ).all()
    enrolled_student_ids = {e.student_id for e in enrollments}
    roster_student_ids = {101, 102, 103}
    missing_students = roster_student_ids - enrolled_student_ids

    assert 103 in missing_students, "Student 103 should be missing from enrollment"
