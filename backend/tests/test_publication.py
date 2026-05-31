"""Tests for Grade Publication Workflow Foundation (Story 5.3).

Covers all Acceptance Criteria:
- AC-1: grade_entries / calculation_results are internal; portal reads only snapshots
- AC-2: BroadcastJob is the publication trigger; no snapshot without a job
- AC-3: each snapshot linked to a broadcast_job; deliveries tracked per recipient
- AC-4: re-publication creates new immutable snapshot version; only one is_current
- AC-5: portal read model returns only is_current=True; never grade_entries
- AC-6: formula_version and derived_state are configurable; no hard-coded rules

Regression:
- ORM model imports succeed
- PublicationService can be instantiated
- All existing tests in the suite continue to pass (verified by running full suite)
"""
from __future__ import annotations

import json
from datetime import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from backend.app.models.academic import (
    GRADE_STATUS_DRAFT,
    GRADE_STATUS_VALIDATED,
    GRADE_STATUS_VOIDED,
    DERIVED_STATE_PROVISIONAL,
    AuditLog,
    CalculationResult,
    GradeEntry,
)
from backend.app.models.base import Base
from backend.app.models.publication import (
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_PENDING,
    JOB_STATUS_RUNNING,
    DELIVERY_STATUS_FAILED,
    DELIVERY_STATUS_SENT,
    BroadcastJob,
    NotificationDelivery,
    PublicationSnapshot,
)
from backend.app.publication.service import (
    ACTION_DELIVERY_COMPLETED,
    ACTION_DELIVERY_FAILED,
    ACTION_PUBLICATION_CONFIRMED,
    ACTION_PUBLICATION_START,
    ACTION_SNAPSHOT_CREATED,
    PreflightError,
    PublicationService,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def engine():
    """In-memory SQLite engine with the full academic schema."""
    _engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    with _engine.connect() as conn:
        # Minimal tables required for publication tests.
        # We create them explicitly to avoid needing Alembic in tests.
        conn.execute(
            text(
                """
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL DEFAULT 'x',
                    role TEXT NOT NULL DEFAULT 'professor',
                    must_change_password INTEGER NOT NULL DEFAULT 1,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE courses (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE semesters (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'planned',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE shifts (
                    id INTEGER PRIMARY KEY,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE class_groups (
                    id INTEGER PRIMARY KEY,
                    course_id INTEGER,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE subjects (
                    id INTEGER PRIMARY KEY,
                    course_id INTEGER,
                    code TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE professors (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    full_name TEXT NOT NULL,
                    email TEXT,
                    phone TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE teaching_assignments (
                    id INTEGER PRIMARY KEY,
                    professor_id INTEGER NOT NULL,
                    class_group_id INTEGER NOT NULL,
                    subject_id INTEGER NOT NULL,
                    semester_id INTEGER NOT NULL,
                    shift_id INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE students (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    student_number TEXT NOT NULL UNIQUE,
                    full_name TEXT NOT NULL,
                    phone TEXT,
                    email TEXT,
                    current_class_group_id INTEGER,
                    course_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE assessment_definitions (
                    id INTEGER PRIMARY KEY,
                    teaching_assignment_id INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    name TEXT,
                    weight REAL,
                    max_score REAL,
                    sort_order INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE grade_entries (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    teaching_assignment_id INTEGER NOT NULL,
                    assessment_definition_id INTEGER NOT NULL,
                    raw_value REAL,
                    normalized_value REAL,
                    status TEXT NOT NULL DEFAULT 'draft',
                    source_upload_id TEXT,
                    updated_by_user_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE calculation_results (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    teaching_assignment_id INTEGER NOT NULL,
                    formula_version TEXT NOT NULL,
                    computed_score REAL,
                    derived_state TEXT NOT NULL DEFAULT 'provisional',
                    computed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE broadcast_jobs (
                    id INTEGER PRIMARY KEY,
                    teaching_assignment_id INTEGER,
                    class_group_id INTEGER,
                    job_type TEXT NOT NULL,
                    actor_user_id INTEGER,
                    status TEXT NOT NULL DEFAULT 'pending',
                    channels_json TEXT,
                    total_recipients INTEGER NOT NULL DEFAULT 0,
                    total_success INTEGER NOT NULL DEFAULT 0,
                    total_failed INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_at TEXT
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE publication_snapshots (
                    id INTEGER PRIMARY KEY,
                    student_id INTEGER NOT NULL,
                    teaching_assignment_id INTEGER NOT NULL,
                    broadcast_job_id INTEGER NOT NULL,
                    snapshot_version INTEGER NOT NULL,
                    published_score REAL,
                    published_state TEXT NOT NULL,
                    published_payload_json TEXT NOT NULL,
                    is_current INTEGER NOT NULL DEFAULT 1,
                    published_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (student_id, teaching_assignment_id, snapshot_version)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE notification_deliveries (
                    id INTEGER PRIMARY KEY,
                    broadcast_job_id INTEGER NOT NULL,
                    student_id INTEGER,
                    user_id INTEGER,
                    channel TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    error_code TEXT,
                    error_message TEXT,
                    attempt INTEGER NOT NULL DEFAULT 0,
                    external_response_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE audit_log (
                    id INTEGER PRIMARY KEY,
                    actor_user_id INTEGER,
                    request_id TEXT,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT,
                    before_json TEXT,
                    after_json TEXT,
                    reason TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    auth_event_type TEXT,
                    failure_reason TEXT
                )
                """
            )
        )
        # Seed minimal reference data
        conn.execute(text("INSERT INTO users (id, username, role) VALUES (1, 'prof01', 'professor')"))
        conn.execute(text("INSERT INTO users (id, username, role) VALUES (2, 'stu01', 'student')"))
        conn.execute(text("INSERT INTO users (id, username, role) VALUES (3, 'stu02', 'student')"))
        conn.execute(text("INSERT INTO courses (id, code, name) VALUES (1, 'CS101', 'Computer Science')"))
        conn.execute(text("INSERT INTO semesters (id, code, name) VALUES (1, '2026-1', 'First Semester 2026')"))
        conn.execute(text("INSERT INTO shifts (id, code, name) VALUES (1, 'MORN', 'Morning')"))
        conn.execute(text("INSERT INTO class_groups (id, course_id, code, name) VALUES (1, 1, 'CG-A', 'Class Group A')"))
        conn.execute(text("INSERT INTO subjects (id, course_id, code, name) VALUES (1, 1, 'MATH', 'Mathematics')"))
        conn.execute(text("INSERT INTO professors (id, user_id, full_name) VALUES (1, 1, 'Professor One')"))
        conn.execute(text("INSERT INTO teaching_assignments (id, professor_id, class_group_id, subject_id, semester_id, shift_id) VALUES (1, 1, 1, 1, 1, 1)"))
        conn.execute(text("INSERT INTO students (id, user_id, student_number, full_name) VALUES (1, 2, 'S001', 'Student One')"))
        conn.execute(text("INSERT INTO students (id, user_id, student_number, full_name) VALUES (2, 3, 'S002', 'Student Two')"))
        conn.execute(text("INSERT INTO assessment_definitions (id, teaching_assignment_id, code, name) VALUES (1, 1, 'EXAM1', 'Exam 1')"))
        conn.commit()
    yield _engine
    _engine.dispose()


@pytest.fixture()
def session(engine):
    """Provide a transactional session that rolls back after each test."""
    with Session(engine) as s:
        yield s


@pytest.fixture()
def svc() -> PublicationService:
    return PublicationService()


# Grade data helper
def _grade_data(student_id: int, score: float = 14.5, state: str = "provisional") -> dict:
    return {
        "student_id": student_id,
        "published_score": score,
        "published_state": state,
        "payload": {
            "formula_version": "v1.0",
            "components": {"exam": score},
            "derived_state": state,
        },
    }


# ---------------------------------------------------------------------------
# AC-1: Internal models exist; lifecycle constants are correct
# ---------------------------------------------------------------------------


def test_grade_entry_lifecycle_constants() -> None:
    assert GRADE_STATUS_DRAFT == "draft"
    assert GRADE_STATUS_VALIDATED == "validated"
    assert GRADE_STATUS_VOIDED == "voided"


def test_calculation_result_derived_state_provisional() -> None:
    assert DERIVED_STATE_PROVISIONAL == "provisional"


def test_grade_entry_orm_can_be_created(session: Session) -> None:
    entry = GradeEntry(
        student_id=1,
        teaching_assignment_id=1,
        assessment_definition_id=1,
        raw_value=15.0,
        normalized_value=15.0,
        status=GRADE_STATUS_DRAFT,
    )
    session.add(entry)
    session.flush()
    assert entry.id is not None
    assert entry.status == GRADE_STATUS_DRAFT


def test_calculation_result_orm_stores_formula_version(session: Session) -> None:
    """AC-6: formula_version is stored; derived_state defaults to provisional."""
    cr = CalculationResult(
        student_id=1,
        teaching_assignment_id=1,
        formula_version="v2.1-beta",
        computed_score=13.75,
        derived_state=DERIVED_STATE_PROVISIONAL,
    )
    session.add(cr)
    session.flush()
    assert cr.formula_version == "v2.1-beta"
    assert cr.derived_state == DERIVED_STATE_PROVISIONAL


# ---------------------------------------------------------------------------
# AC-2: BroadcastJob is the publication trigger
# ---------------------------------------------------------------------------


def test_create_broadcast_job_returns_pending_job(session: Session, svc: PublicationService) -> None:
    job = svc.create_broadcast_job(
        session,
        teaching_assignment_id=1,
        actor_user_id=1,
        job_type="grade_publication",
        channels=["whatsapp"],
    )
    session.commit()
    assert job.id is not None
    assert job.status == JOB_STATUS_PENDING
    assert json.loads(job.channels_json) == ["whatsapp"]


def test_broadcast_job_lifecycle_constants() -> None:
    assert JOB_STATUS_PENDING == "pending"
    assert JOB_STATUS_RUNNING == "running"
    assert JOB_STATUS_COMPLETED == "completed"
    assert JOB_STATUS_FAILED == "failed"


def test_create_broadcast_job_stores_class_group(session: Session, svc: PublicationService) -> None:
    job = svc.create_broadcast_job(
        session,
        teaching_assignment_id=1,
        actor_user_id=1,
        job_type="grade_publication",
        channels=["email"],
        class_group_id=1,
    )
    session.flush()
    assert job.class_group_id == 1


# ---------------------------------------------------------------------------
# AC-2 + AC-3: create_publication_snapshots links to job
# ---------------------------------------------------------------------------


def test_create_publication_snapshots_creates_snapshots(
    session: Session, svc: PublicationService
) -> None:
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    data = [_grade_data(1), _grade_data(2)]
    snapshots = svc.create_publication_snapshots(session, job, data)
    session.commit()

    assert len(snapshots) == 2
    for snap in snapshots:
        assert snap.broadcast_job_id == job.id
        assert snap.is_current is True
        assert snap.snapshot_version == 1

    assert job.status == JOB_STATUS_COMPLETED
    assert job.total_recipients == 2


def test_create_publication_snapshots_stores_payload_with_formula_version(
    session: Session, svc: PublicationService
) -> None:
    """AC-6: payload includes formula_version; no hard-coded formula rules."""
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    data = [_grade_data(1, score=16.0, state="provisional")]
    snapshots = svc.create_publication_snapshots(session, job, data)
    session.commit()

    payload = json.loads(snapshots[0].published_payload_json)
    assert "formula_version" in payload
    assert payload["formula_version"] == "v1.0"
    assert "derived_state" in payload


# ---------------------------------------------------------------------------
# AC-4: Re-publication creates new immutable snapshot version
# ---------------------------------------------------------------------------


def test_republish_creates_new_version_and_supersedes_current(
    session: Session, svc: PublicationService
) -> None:
    # First publication
    job1 = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    svc.create_publication_snapshots(session, job1, [_grade_data(1, score=10.0)])
    session.commit()

    # Re-publication
    job2 = svc.republish(
        session,
        teaching_assignment_id=1,
        actor_user_id=1,
        grade_data=[_grade_data(1, score=15.0)],
        channels=["whatsapp"],
    )
    session.commit()

    # Query all snapshots for student 1
    from sqlalchemy import select as _select
    all_snaps = list(
        session.execute(
            _select(PublicationSnapshot).where(
                PublicationSnapshot.student_id == 1,
                PublicationSnapshot.teaching_assignment_id == 1,
            ).order_by(PublicationSnapshot.snapshot_version)
        ).scalars()
    )
    assert len(all_snaps) == 2
    v1, v2 = all_snaps
    assert v1.snapshot_version == 1
    assert v1.is_current is False  # superseded
    assert v2.snapshot_version == 2
    assert v2.is_current is True   # new current


def test_republish_previous_snapshot_remains_in_db(
    session: Session, svc: PublicationService
) -> None:
    """AC-4: Previous snapshots remain auditable — not deleted."""
    job1 = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    svc.create_publication_snapshots(session, job1, [_grade_data(1)])
    session.commit()

    svc.republish(
        session, teaching_assignment_id=1, actor_user_id=1,
        grade_data=[_grade_data(1)], channels=["whatsapp"]
    )
    session.commit()

    from sqlalchemy import select as _select
    total = session.execute(
        _select(PublicationSnapshot).where(PublicationSnapshot.student_id == 1)
    ).scalars().all()
    assert len(total) == 2  # both versions preserved


# ---------------------------------------------------------------------------
# AC-5: Portal read model — only is_current=True; never grade_entries
# ---------------------------------------------------------------------------


def test_get_current_snapshots_returns_only_current(
    session: Session, svc: PublicationService
) -> None:
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    svc.create_publication_snapshots(session, job, [_grade_data(1), _grade_data(2)])
    session.commit()

    portal_snaps = svc.get_current_snapshots_for_portal(session, student_id=1)
    assert len(portal_snaps) == 1
    assert portal_snaps[0].is_current is True
    assert portal_snaps[0].student_id == 1


def test_get_current_snapshots_excludes_superseded_versions(
    session: Session, svc: PublicationService
) -> None:
    job1 = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    svc.create_publication_snapshots(session, job1, [_grade_data(1)])
    session.commit()

    svc.republish(
        session, teaching_assignment_id=1, actor_user_id=1,
        grade_data=[_grade_data(1, score=18.0)], channels=["whatsapp"]
    )
    session.commit()

    portal_snaps = svc.get_current_snapshots_for_portal(session, student_id=1)
    # Only the latest version is returned
    assert len(portal_snaps) == 1
    assert portal_snaps[0].published_score == 18.0


def test_get_current_snapshots_with_assignment_filter(
    session: Session, svc: PublicationService
) -> None:
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    svc.create_publication_snapshots(session, job, [_grade_data(1)])
    session.commit()

    result_match = svc.get_current_snapshots_for_portal(session, student_id=1, teaching_assignment_id=1)
    result_no_match = svc.get_current_snapshots_for_portal(session, student_id=1, teaching_assignment_id=999)

    assert len(result_match) == 1
    assert len(result_no_match) == 0


def test_portal_read_model_never_returns_unpublished_data(session: Session, svc: PublicationService) -> None:
    """AC-5: Student with only internal grade_entries gets no portal data."""
    # Insert internal grade only — no publication
    entry = GradeEntry(
        student_id=1,
        teaching_assignment_id=1,
        assessment_definition_id=1,
        raw_value=12.0,
        status=GRADE_STATUS_VALIDATED,
    )
    session.add(entry)
    session.commit()

    portal_snaps = svc.get_current_snapshots_for_portal(session, student_id=1)
    assert portal_snaps == []


# ---------------------------------------------------------------------------
# AC-3: Notification delivery tracking
# ---------------------------------------------------------------------------


def test_record_delivery_outcome_success(session: Session, svc: PublicationService) -> None:
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    session.flush()

    delivery = svc.record_delivery_outcome(
        session, job_id=job.id, student_id=1,
        channel="whatsapp", destination="+244900000001", success=True
    )
    session.commit()

    assert delivery.status == DELIVERY_STATUS_SENT
    assert delivery.error_code is None
    assert delivery.channel == "whatsapp"


def test_record_delivery_outcome_failure_captures_error(
    session: Session, svc: PublicationService
) -> None:
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    session.flush()

    delivery = svc.record_delivery_outcome(
        session, job_id=job.id, student_id=2,
        channel="whatsapp", destination="+244900000002", success=False,
        error_code="ERR_UNREACHABLE", error_message="Number not reachable"
    )
    session.commit()

    assert delivery.status == DELIVERY_STATUS_FAILED
    assert delivery.error_code == "ERR_UNREACHABLE"
    assert delivery.error_message == "Number not reachable"


def test_record_delivery_updates_job_totals(session: Session, svc: PublicationService) -> None:
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    session.flush()

    svc.record_delivery_outcome(session, job_id=job.id, student_id=1, channel="whatsapp", destination="x", success=True)
    svc.record_delivery_outcome(session, job_id=job.id, student_id=2, channel="whatsapp", destination="y", success=False, error_code="ERR")
    session.commit()

    # Re-fetch job to see updated totals
    from sqlalchemy import select as _select
    refreshed = session.execute(_select(BroadcastJob).where(BroadcastJob.id == job.id)).scalar_one()
    assert refreshed.total_success == 1
    assert refreshed.total_failed == 1


# ---------------------------------------------------------------------------
# Preflight / rollback (task 9)
# ---------------------------------------------------------------------------


def test_empty_grade_data_raises_preflight_error(session: Session, svc: PublicationService) -> None:
    """Preflight: empty grade_data must not create snapshots; job set to failed."""
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    session.flush()

    with pytest.raises(PreflightError):
        svc.create_publication_snapshots(session, job, [])

    assert job.status == JOB_STATUS_FAILED


# ---------------------------------------------------------------------------
# Dry-run counts (task 6)
# ---------------------------------------------------------------------------


def test_compute_dry_run_counts_returns_dict(session: Session, svc: PublicationService) -> None:
    # Seed a validated grade entry
    entry = GradeEntry(
        student_id=1,
        teaching_assignment_id=1,
        assessment_definition_id=1,
        raw_value=15.0,
        status=GRADE_STATUS_VALIDATED,
    )
    session.add(entry)
    session.commit()

    counts = svc.compute_dry_run_counts(session, teaching_assignment_id=1)
    assert counts["teaching_assignment_id"] == 1
    assert counts["total_recipients"] == 1
    assert "existing_current_snapshots" in counts


def test_compute_dry_run_counts_does_not_create_rows(session: Session, svc: PublicationService) -> None:
    """Dry-run must not persist any rows."""
    svc.compute_dry_run_counts(session, teaching_assignment_id=1)
    session.commit()

    from sqlalchemy import select as _select
    job_count = session.execute(_select(BroadcastJob)).scalars().all()
    snap_count = session.execute(_select(PublicationSnapshot)).scalars().all()
    assert len(job_count) == 0
    assert len(snap_count) == 0


def test_dry_run_excludes_draft_entries(session: Session, svc: PublicationService) -> None:
    """Only validated grade entries are counted in dry-run."""
    draft = GradeEntry(
        student_id=1, teaching_assignment_id=1, assessment_definition_id=1,
        raw_value=10.0, status=GRADE_STATUS_DRAFT
    )
    validated = GradeEntry(
        student_id=2, teaching_assignment_id=1, assessment_definition_id=1,
        raw_value=12.0, status=GRADE_STATUS_VALIDATED
    )
    session.add_all([draft, validated])
    session.commit()

    counts = svc.compute_dry_run_counts(session, teaching_assignment_id=1)
    assert counts["total_recipients"] == 1  # only validated


# ---------------------------------------------------------------------------
# Audit events (task 8)
# ---------------------------------------------------------------------------


def test_publication_creates_audit_events(session: Session, svc: PublicationService) -> None:
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    svc.create_publication_snapshots(session, job, [_grade_data(1)], request_id="req-123")
    session.commit()

    from sqlalchemy import select as _select
    events = list(session.execute(_select(AuditLog)).scalars())
    actions = {e.action for e in events}
    assert ACTION_PUBLICATION_START in actions
    assert ACTION_SNAPSHOT_CREATED in actions
    assert ACTION_PUBLICATION_CONFIRMED in actions


def test_delivery_audit_events_recorded(session: Session, svc: PublicationService) -> None:
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    session.flush()
    svc.record_delivery_outcome(session, job_id=job.id, student_id=1, channel="whatsapp", destination="x", success=True)
    svc.record_delivery_outcome(session, job_id=job.id, student_id=2, channel="whatsapp", destination="y", success=False, error_code="ERR")
    session.commit()

    from sqlalchemy import select as _select
    events = list(session.execute(_select(AuditLog)).scalars())
    actions = {e.action for e in events}
    assert ACTION_DELIVERY_COMPLETED in actions
    assert ACTION_DELIVERY_FAILED in actions


def test_audit_event_contains_broadcast_job_id(session: Session, svc: PublicationService) -> None:
    """AC-10: broadcast_job_id must appear in audit after_json."""
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    svc.create_publication_snapshots(session, job, [_grade_data(1)])
    session.commit()

    from sqlalchemy import select as _select
    events = list(session.execute(_select(AuditLog)).scalars())
    pub_start = next(e for e in events if e.action == ACTION_PUBLICATION_START)
    payload = json.loads(pub_start.after_json)
    assert payload["broadcast_job_id"] == job.id


def test_record_audit_event_directly(session: Session, svc: PublicationService) -> None:
    svc.record_audit_event(
        session,
        actor_user_id=1,
        action="manual_test",
        entity_type="test_entity",
        entity_id="42",
        request_id="r-001",
        after_json=json.dumps({"key": "value"}),
        reason="unit test",
    )
    session.commit()

    from sqlalchemy import select as _select
    entry = session.execute(
        _select(AuditLog).where(AuditLog.action == "manual_test")
    ).scalar_one()
    assert entry.entity_id == "42"
    assert entry.request_id == "r-001"
    assert entry.reason == "unit test"


# ---------------------------------------------------------------------------
# AC-6: Formula is configurable — no hard-coded rules
# ---------------------------------------------------------------------------


def test_calculation_result_stores_custom_formula_version(session: Session) -> None:
    cr = CalculationResult(
        student_id=1,
        teaching_assignment_id=1,
        formula_version="custom-v3.0",
        computed_score=17.0,
        derived_state="provisional",
    )
    session.add(cr)
    session.flush()
    assert cr.formula_version == "custom-v3.0"
    # derived_state is stored as-is; no validation against institution rules
    assert cr.derived_state == "provisional"


def test_snapshot_payload_stores_any_formula_version(session: Session, svc: PublicationService) -> None:
    """AC-6: payload formula_version is free-form; service does not validate it."""
    job = svc.create_broadcast_job(
        session, teaching_assignment_id=1, actor_user_id=1,
        job_type="grade_publication", channels=["whatsapp"]
    )
    custom_entry = {
        "student_id": 1,
        "published_score": 12.0,
        "published_state": "provisional",
        "payload": {
            "formula_version": "experimental-2026",
            "components": {"midterm": 10.0, "final": 14.0},
            "derived_state": "provisional",
        },
    }
    snapshots = svc.create_publication_snapshots(session, job, [custom_entry])
    session.commit()

    payload = json.loads(snapshots[0].published_payload_json)
    assert payload["formula_version"] == "experimental-2026"


# ---------------------------------------------------------------------------
# Regression: imports and instantiation
# ---------------------------------------------------------------------------


def test_publication_service_can_be_instantiated() -> None:
    svc = PublicationService()
    assert svc is not None


def test_model_imports_succeed() -> None:
    from backend.app.models import (
        AuditLog,
        Base,
        BroadcastJob,
        CalculationResult,
        GradeEntry,
        NotificationDelivery,
        PublicationSnapshot,
        TimestampMixin,
    )
    assert Base is not None
    assert GradeEntry is not None
    assert CalculationResult is not None
    assert BroadcastJob is not None
    assert PublicationSnapshot is not None
    assert NotificationDelivery is not None
    assert AuditLog is not None
