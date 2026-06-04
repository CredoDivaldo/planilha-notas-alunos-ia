"""Tests for Student Portal Calendar — Story 5.6.

Test Coverage:
  - AC-2: Calendar returns ONLY is_published=True events; drafts excluded
  - AC-3: Calendar scoped to authenticated student's enrolled contexts only
  - AC-4: Real query replaces TODO stub; empty list returned gracefully
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.models import (
    AcademicContext,
    Base,
    ClassEnrollment,
    PublishedCalendarSnapshot,
    Semester,
    Shift,
)
from backend.app.portal.service import PortalService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_db_session(tmp_path: Path):
    """Create an isolated SQLite database with the full schema."""
    db_path = tmp_path / "test_calendar.sqlite3"
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    yield session
    session.close()
    engine.dispose()


_shift_counter: int = 0
_semester_counter: int = 0


def _make_context(session: Session, professor_id: int = 1, subject: str = "Math") -> AcademicContext:
    """Helper: create semester, shift, and academic context; return context.

    Uses unique codes for semester and shift to avoid UNIQUE constraint
    violations when called multiple times within the same test.
    """
    global _shift_counter, _semester_counter
    _semester_counter += 1
    _shift_counter += 1

    semester = Semester(
        code=f"2026-S1-{_semester_counter}",
        name=f"2026 Semester {_semester_counter}",
        academic_year=2026,
        semester_number=1,
        status="active",
    )
    session.add(semester)
    session.flush()

    shift = Shift(code=f"MORNING-{_shift_counter}", name="Morning", status="active")
    session.add(shift)
    session.flush()

    context = AcademicContext(
        professor_id=professor_id,
        academic_year=2026,
        turma="10A",
        subject=subject,
        semester_id=semester.id,
        shift_id=shift.id,
        status="active",
    )
    session.add(context)
    session.flush()
    return context


def _make_snapshot(
    session: Session,
    academic_context_id: int,
    is_published: bool,
    student_id: int | None = None,
    event_type: str = "exam",
    subject: str = "Math",
    start_date: datetime | None = None,
    published_at: datetime | None = None,
) -> PublishedCalendarSnapshot:
    """Helper: create a PublishedCalendarSnapshot row."""
    if start_date is None:
        start_date = datetime(2026, 7, 15, 8, 0, 0)
    if published_at is None:
        published_at = datetime.now(UTC).replace(tzinfo=None)

    snap = PublishedCalendarSnapshot(
        academic_context_id=academic_context_id,
        student_id=student_id,
        event_type=event_type,
        subject=subject,
        start_date=start_date,
        is_published=is_published,
        published_at=published_at if is_published else None,
    )
    session.add(snap)
    session.flush()
    return snap


# ---------------------------------------------------------------------------
# Test 1: Calendar returns published events for enrolled student (AC-2, AC-4)
# ---------------------------------------------------------------------------


def test_calendar_returns_published_events(temp_db_session: Session) -> None:
    """AC-2, AC-4: Published events are returned for the authenticated student."""
    session = temp_db_session
    student_id = 200

    # Create a context and enroll the student
    context = _make_context(session, subject="Physics")
    session.add(ClassEnrollment(academic_context_id=context.id, student_id=student_id, enrollment_status="active"))
    session.flush()

    # Add one published class-wide event
    snap = _make_snapshot(session, context.id, is_published=True, student_id=None, subject="Physics")
    session.flush()

    service = PortalService()
    result = service.get_calendar(session, student_id)

    assert result["student_id"] == student_id
    events = result["calendar_events"]
    assert len(events) == 1
    assert events[0]["event_id"] == snap.id
    assert events[0]["event_type"] == "exam"
    assert events[0]["subject"] == "Physics"
    assert events[0]["start_date"] is not None
    assert events[0]["published_at"] is not None


# ---------------------------------------------------------------------------
# Test 2: Draft events (is_published=False) are excluded (AC-2)
# ---------------------------------------------------------------------------


def test_calendar_excludes_draft_events(temp_db_session: Session) -> None:
    """AC-2: Draft calendar events (is_published=False) are never returned."""
    session = temp_db_session
    student_id = 201

    context = _make_context(session, subject="Chemistry")
    session.add(ClassEnrollment(academic_context_id=context.id, student_id=student_id, enrollment_status="active"))
    session.flush()

    # One draft, one published
    _make_snapshot(session, context.id, is_published=False, student_id=None, subject="Chemistry")
    published_snap = _make_snapshot(
        session, context.id, is_published=True, student_id=None, subject="Chemistry",
        event_type="recurso", start_date=datetime(2026, 8, 10, 9, 0, 0),
    )
    session.flush()

    service = PortalService()
    result = service.get_calendar(session, student_id)

    events = result["calendar_events"]
    assert len(events) == 1, "Only the published event should be returned"
    assert events[0]["event_id"] == published_snap.id
    assert events[0]["event_type"] == "recurso"


# ---------------------------------------------------------------------------
# Test 3: Calendar scoped to student's contexts only (AC-3, IDOR regression)
# ---------------------------------------------------------------------------


def test_calendar_scoped_to_enrolled_contexts(temp_db_session: Session) -> None:
    """AC-3: Events from another student's context are not returned (IDOR guard)."""
    session = temp_db_session
    student_a = 300
    student_b = 301

    # Context for student_a
    context_a = _make_context(session, professor_id=1, subject="Biology")
    session.add(ClassEnrollment(academic_context_id=context_a.id, student_id=student_a, enrollment_status="active"))

    # Context for student_b (student_a is NOT enrolled here)
    context_b = _make_context(session, professor_id=2, subject="History")
    session.add(ClassEnrollment(academic_context_id=context_b.id, student_id=student_b, enrollment_status="active"))
    session.flush()

    # Published event in context_b — should NOT appear for student_a
    _make_snapshot(session, context_b.id, is_published=True, student_id=None, subject="History")
    # Published event in context_a — should appear for student_a
    snap_a = _make_snapshot(session, context_a.id, is_published=True, student_id=None, subject="Biology")
    session.flush()

    service = PortalService()

    # student_a sees only their context events
    result_a = service.get_calendar(session, student_a)
    assert len(result_a["calendar_events"]) == 1
    assert result_a["calendar_events"][0]["event_id"] == snap_a.id

    # student_b sees only their context events
    result_b = service.get_calendar(session, student_b)
    assert len(result_b["calendar_events"]) == 1
    assert result_b["calendar_events"][0]["subject"] == "History"


# ---------------------------------------------------------------------------
# Test 4: Empty list returned gracefully when no published events exist (AC-4)
# ---------------------------------------------------------------------------


def test_calendar_returns_empty_when_no_events(temp_db_session: Session) -> None:
    """AC-4: Graceful empty list when student has no published calendar events."""
    session = temp_db_session
    student_id = 400

    # Enroll in a context, but add NO calendar snapshots
    context = _make_context(session, subject="Geography")
    session.add(ClassEnrollment(academic_context_id=context.id, student_id=student_id, enrollment_status="active"))
    session.flush()

    service = PortalService()
    result = service.get_calendar(session, student_id)

    assert result["student_id"] == student_id
    assert result["calendar_events"] == []


# ---------------------------------------------------------------------------
# Test 5: Unenrolled student sees no events (AC-3 edge case)
# ---------------------------------------------------------------------------


def test_calendar_empty_for_unenrolled_student(temp_db_session: Session) -> None:
    """AC-3: Student with no enrollments sees an empty calendar."""
    session = temp_db_session
    unenrolled_student_id = 999

    # Create a published event in a context this student isn't enrolled in
    context = _make_context(session, subject="Art")
    _make_snapshot(session, context.id, is_published=True, subject="Art")
    session.flush()

    service = PortalService()
    result = service.get_calendar(session, unenrolled_student_id)

    assert result["student_id"] == unenrolled_student_id
    assert result["calendar_events"] == []
