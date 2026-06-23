"""Modelos ORM académicos internos: GradeEntry, CalculationResult, AuditLog.

PT: Estes modelos são o "lado interno" das notas (nunca são mostrados ao aluno
directamente — para o aluno usa-se o `publication.py`). GradeEntry guarda cada
nota individual; CalculationResult guarda a nota final calculada por uma fórmula;
AuditLog é um registo de auditoria (histórico do que aconteceu). As constantes
no topo definem os estados válidos de uma nota (draft → validated → voided).

Academic ORM models: GradeEntry, CalculationResult, AuditLog.

These represent the *internal* side of the grade lifecycle.  Portal-facing
data lives exclusively in ``publication.py`` models.

Lifecycle constants
-------------------
GradeEntry.status:
    draft      — raw upload; not yet reviewed
    validated  — professor confirmed this value is correct
    voided     — entry was retracted (soft-delete); never shown

CalculationResult.derived_state:
    provisional — formula output is provisional; final label not yet closed
    (additional states are product decisions; this model stores whatever
    string the formula engine emits at the time of calculation)

Open formula rule (AC-6):
    ``formula_version`` stores the identifier of the scoring algorithm used.
    No hard-coded scoring rules exist here.  The application layer is
    responsible for populating ``computed_score`` and ``derived_state``
    based on the versioned formula.
"""
from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin

# ---------------------------------------------------------------------------
# GradeEntry lifecycle constants
# ---------------------------------------------------------------------------

# Estados possíveis de uma nota: rascunho, validada, anulada.
GRADE_STATUS_DRAFT = "draft"
GRADE_STATUS_VALIDATED = "validated"
GRADE_STATUS_VOIDED = "voided"
GRADE_STATUSES = (GRADE_STATUS_DRAFT, GRADE_STATUS_VALIDATED, GRADE_STATUS_VOIDED)

# ---------------------------------------------------------------------------
# CalculationResult derived state constants
# ---------------------------------------------------------------------------

DERIVED_STATE_PROVISIONAL = "provisional"


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------


class GradeEntry(Base, TimestampMixin):
    """Per-student, per-assessment grade record.

    Internal model — NEVER exposed directly to the student portal.
    Use ``PublicationSnapshot`` for student-facing data.

    Lifecycle: draft → validated → voided

    AC-8: All grade entries are scoped to an academic_context_id.
    Uploads must specify the context and validate against that context's
    student roster and subject configuration.
    """

    __tablename__ = "grade_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK: academic_contexts.id — scopes grade to professor's teaching assignment (AC-8)
    academic_context_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # FK: students.id — enforced at DB level via migration; not declared in ORM to
    # allow in-memory test fixtures that create tables via raw DDL.
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)
    teaching_assignment_id: Mapped[int] = mapped_column(Integer, nullable=False)
    assessment_definition_id: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_value: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    normalized_value: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    # lifecycle: draft | validated | voided
    status: Mapped[str] = mapped_column(
        String(40), server_default=GRADE_STATUS_DRAFT, nullable=False
    )
    source_upload_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_by_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class CalculationResult(Base, TimestampMixin):
    """Versioned, per-student score derived from internal grade entries.

    Internal model — NEVER read by portal endpoints.
    ``formula_version`` identifies the exact scoring algorithm used so
    results can be reproduced or compared across formula iterations.

    The ``derived_state`` field defaults to ``provisional``; product
    validation decides when and if a state becomes final.
    """

    __tablename__ = "calculation_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK: students.id — enforced at DB level via migration.
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)
    teaching_assignment_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # Identifies the scoring algorithm — keeps formula open (AC-6)
    formula_version: Mapped[str] = mapped_column(String(80), nullable=False)
    computed_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    # provisional by default; final label is a product decision
    derived_state: Mapped[str] = mapped_column(
        String(80), server_default=DERIVED_STATE_PROVISIONAL, nullable=False
    )
    computed_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )


class AuditLog(Base):
    """Append-only audit trail.

    Records publication lifecycle events: publication_start,
    publication_confirmed, snapshot_created, delivery_completed,
    delivery_failed.

    Columns match the schema created by migration 0001 and extended by 0002:
    - before_json / after_json  — state diff (JSON strings)
    - reason                    — human-readable summary
    - auth_event_type           — auth-specific event label (0002 addition)
    - failure_reason            — auth failure detail (0002 addition)
    """

    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK: users.id — enforced at DB level via migration.
    actor_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    request_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    action: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    before_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    after_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    # Added by migration 0002 — auth-specific fields (nullable for non-auth events)
    auth_event_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(120), nullable=True)
