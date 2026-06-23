"""Modelos de publicação — o que fica VISÍVEL para os alunos.

PT: O aluno nunca vê as notas internas (grade_entries). Quando o professor decide
"publicar", cria-se um BroadcastJob (a acção), grava-se uma PublicationSnapshot
(cópia imutável da nota que o aluno passa a ver) e regista-se cada envio em
NotificationDelivery (ex.: WhatsApp enviado/falhado). PublishedCalendarSnapshot
faz o mesmo para datas de exames/provas no calendário do aluno.
Regra central: uma snapshot nunca é alterada; republicar cria uma nova versão.

Publication ORM models: BroadcastJob, PublicationSnapshot, NotificationDelivery.

These models form the *publication boundary*:
- BroadcastJob      — records the explicit professor action that triggers publication
- PublicationSnapshot — immutable, versioned copy of the grade visible to students
- NotificationDelivery — per-recipient, per-channel delivery outcome tracking

Core invariant (AC-1, AC-2, AC-5):
    Grades are NEVER visible to students via grade_entries or calculation_results.
    Only current PublicationSnapshot rows (is_current=True) feed the student portal.

Immutability rule (AC-4):
    PublicationSnapshot rows are never updated after creation.
    Re-publication increments snapshot_version and sets the new row as is_current=True
    while setting is_current=False on the previous current row for the same
    (student_id, teaching_assignment_id) pair.

Lifecycle constants
-------------------
BroadcastJob.status:
    pending    — created, not yet started
    running    — delivery in progress
    completed  — all deliveries attempted; see totals
    failed     — catastrophic failure; delivery did not complete
    cancelled  — cancelled before running

NotificationDelivery.status:
    pending    — not yet attempted
    sent       — successfully delivered
    failed     — attempt failed; see error_code / error_message
    bounced    — address unreachable
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base

# ---------------------------------------------------------------------------
# BroadcastJob lifecycle constants
# ---------------------------------------------------------------------------

JOB_STATUS_PENDING = "pending"
JOB_STATUS_RUNNING = "running"
JOB_STATUS_COMPLETED = "completed"
JOB_STATUS_FAILED = "failed"
JOB_STATUS_CANCELLED = "cancelled"
JOB_STATUSES = (
    JOB_STATUS_PENDING,
    JOB_STATUS_RUNNING,
    JOB_STATUS_COMPLETED,
    JOB_STATUS_FAILED,
    JOB_STATUS_CANCELLED,
)

# ---------------------------------------------------------------------------
# NotificationDelivery status constants
# ---------------------------------------------------------------------------

DELIVERY_STATUS_PENDING = "pending"
DELIVERY_STATUS_SENT = "sent"
DELIVERY_STATUS_FAILED = "failed"
DELIVERY_STATUS_BOUNCED = "bounced"
DELIVERY_STATUSES = (
    DELIVERY_STATUS_PENDING,
    DELIVERY_STATUS_SENT,
    DELIVERY_STATUS_FAILED,
    DELIVERY_STATUS_BOUNCED,
)


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------


class BroadcastJob(Base):
    """Records the professor's explicit publication action (AC-2).

    A BroadcastJob is created BEFORE any snapshot is written.  It transitions
    through: pending → running → completed | failed | cancelled.

    Observability fields (AC-10):
    - total_recipients, total_success, total_failed are updated atomically
      as deliveries complete; broadcast_job_id is logged in every related
      audit event and delivery record.

    Dry-run support (task 6):
    - job_type="dry_run" creates a BroadcastJob in completed state without
      writing snapshots or deliveries; PublicationService.compute_dry_run_counts()
      returns counts without persisting anything.

    Rollback policy (task 9):
    - If preflight validation fails, the service raises and the BroadcastJob
      is set to status="failed" — no snapshots are created.
    - Legacy Node.js upload → match → send routes are NOT affected by this
      service; they run independently and must not be broken.
    """

    __tablename__ = "broadcast_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FKs enforced at DB level via migration; omitted here to allow raw-DDL test fixtures.
    teaching_assignment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    class_group_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # lifecycle: pending | running | completed | failed | cancelled
    status: Mapped[str] = mapped_column(
        String(40), server_default=JOB_STATUS_PENDING, nullable=False
    )
    # JSON array of channel names, e.g. '["whatsapp", "email"]'
    channels_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_recipients: Mapped[int] = mapped_column(
        Integer, server_default=text("0"), nullable=False
    )
    total_success: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    total_failed: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class PublicationSnapshot(Base):
    """Immutable, student-visible grade snapshot (AC-1, AC-4, AC-5).

    IMMUTABILITY RULE: rows are NEVER updated after creation.  To re-publish,
    the service creates a new row with an incremented snapshot_version and
    sets is_current=False on the previous current row for the same
    (student_id, teaching_assignment_id) pair.

    The database enforces: at most one is_current=True per
    (student_id, teaching_assignment_id) via a partial unique index
    (``uq_publication_snapshots_one_current``).

    published_payload_json (AC-6):
    Stores the full grade payload including formula_version and configurable
    component results.  No institutional final-status rules are hard-coded
    here; derived_state is whatever the calculation engine emitted.
    """

    __tablename__ = "publication_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FKs enforced at DB level via migration; omitted here to allow raw-DDL test fixtures.
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)
    teaching_assignment_id: Mapped[int] = mapped_column(Integer, nullable=False)
    broadcast_job_id: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_version: Mapped[int] = mapped_column(Integer, nullable=False)
    published_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    published_state: Mapped[str] = mapped_column(String(80), nullable=False)
    # Full JSON payload: includes formula_version, components, derived_state (AC-6)
    published_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    # is_current=True iff this is the latest published version for the student/context
    is_current: Mapped[bool] = mapped_column(
        Boolean, server_default=text("1"), nullable=False
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class NotificationDelivery(Base):
    """Per-recipient, per-channel delivery outcome (AC-3).

    Tracks each individual delivery attempt.  Multiple rows per broadcast job
    are expected (one per student × channel combination).

    error_code and error_message capture provider-specific failure details
    for operational debugging without leaking them to students.
    """

    __tablename__ = "notification_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FKs enforced at DB level via migration; omitted here to allow raw-DDL test fixtures.
    broadcast_job_id: Mapped[int] = mapped_column(Integer, nullable=False)
    student_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    channel: Mapped[str] = mapped_column(String(40), nullable=False)
    destination: Mapped[str] = mapped_column(String(255), nullable=False)
    # lifecycle: pending | sent | failed | bounced
    status: Mapped[str] = mapped_column(
        String(40), server_default=DELIVERY_STATUS_PENDING, nullable=False
    )
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attempt: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False)
    external_response_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Calendar snapshot (Story 5.6)
# ---------------------------------------------------------------------------

# Valid event types for published_calendar_snapshots
CALENDAR_EVENT_TYPE_EXAM = "exam"
CALENDAR_EVENT_TYPE_RECURSO = "recurso"
CALENDAR_EVENT_TYPE_PROVA = "prova"
CALENDAR_EVENT_TYPES = (
    CALENDAR_EVENT_TYPE_EXAM,
    CALENDAR_EVENT_TYPE_RECURSO,
    CALENDAR_EVENT_TYPE_PROVA,
)


class PublishedCalendarSnapshot(Base):
    """Immutable, student-visible calendar event snapshot (Story 5.6, AC-1–AC-4).

    Records professor-published assessment dates visible through the student portal.

    Scope rules:
    - student_id IS NULL  → class-wide event; visible to ALL enrolled students
    - student_id IS NOT NULL → per-student event; visible ONLY to that student

    Portal query filter:
        is_published=True
        AND academic_context_id IN <enrolled_context_ids>
        AND (student_id IS NULL OR student_id = :authenticated_student_id)

    event_type is one of: exam | recurso | prova
    """

    __tablename__ = "published_calendar_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FKs enforced at DB level via migration; omitted here to allow raw-DDL test fixtures.
    academic_context_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # Nullable: NULL means class-wide event
    student_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # exam | recurso | prova
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    location: Mapped[str | None] = mapped_column(String(300), nullable=True)
    # Draft until explicitly published
    is_published: Mapped[bool] = mapped_column(
        Boolean, server_default=text("0"), nullable=False
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # Nullable FK to the broadcast job that triggered publication
    broadcast_job_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        onupdate=datetime.utcnow,
        nullable=False,
    )
