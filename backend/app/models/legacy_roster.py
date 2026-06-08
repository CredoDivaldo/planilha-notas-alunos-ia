"""Legacy CSV roster bridge models (Story 8.1 — Epic 8 cutover).

These tables are the storage target for the legacy CSV upload endpoints that
the FastAPI backend inherits from the old Express service (`src/`). They are
intentionally narrow: they preserve the CSV column shape (``student_number``,
``nome``, ``whatsapp``, ``turma``, ``nota``) so that the front-end dashboard
can keep its current Step 1/Step 2 contract during cutover.

Why a separate module (instead of extending the Epic 5 ``ClassEnrollment`` /
``GradeEntry`` models)?

* The Epic 5 models are the *internal / normalised* side of the grade
  lifecycle. They are intentionally FK-only (``student_id``, ``academic_context_id``)
  because the canonical student identity lives in the ``users`` / ``students``
  table — tables that are *not* part of this codebase's ORM (they are
  assumed to be managed by the institution's identity service).
* The legacy CSV uploads do not carry a stable ``student_id`` — they carry
  ``numero_estudante`` (string) and a WhatsApp phone number, both of which
  need reconciliation before they can join the Epic 5 schema. Story 8.1
  ports the Express *ingest* contract; reconciliation is a follow-up epic.
* The bulk-insert requirement (AC-5) and the 2 MB cap (AC-4) are easier to
  enforce on a narrow, CSV-shaped table.

This module is the *only* storage target used by
``backend/app/routers/ingest.py``. Once reconciliation lands, these tables
will be drained by a one-shot migration into ``class_enrollments`` /
``grade_entries``; the schema is deliberately small to make that future
drain trivial.
"""
from __future__ import annotations

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin


# ---------------------------------------------------------------------------
# Lifecycle constants (kept tiny; this is a passthrough table)
# ---------------------------------------------------------------------------


UPLOAD_STATUS_OK = "ok"
UPLOAD_STATUS_FAILED = "failed"
UPLOAD_STATUSES = (UPLOAD_STATUS_OK, UPLOAD_STATUS_FAILED)


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------


class LegacyStudent(Base, TimestampMixin):
    """One row per (academic_context_id, student_number) — CSV-shaped roster.

    Uniqueness on ``(academic_context_id, student_number)`` is what makes
    the upload idempotent (AC6 — re-uploading the same CSV does not
    duplicate rows).
    """

    __tablename__ = "legacy_students"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK: academic_contexts.id — nullable so the dashboard can upload a
    # roster before picking a context (the legacy behaviour was the same).
    academic_context_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    student_number: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    turma: Mapped[str | None] = mapped_column(String(60), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(40), nullable=True)
    # Echo of the original CSV row for audit / debugging (kept short).
    raw_row_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class LegacyGrade(Base, TimestampMixin):
    """One row per (academic_context_id, student_number, subject) — CSV grades.

    Idempotency key mirrors the legacy matcher: same student + same subject
    in the same context = upsert, not insert.
    """

    __tablename__ = "legacy_grades"

    id: Mapped[int] = mapped_column(primary_key=True)
    academic_context_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    student_number: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    turma: Mapped[str | None] = mapped_column(String(60), nullable=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Free-form: the legacy system stored the raw string (e.g. "12.5",
    # "MB", "Aprovado"). We do not coerce to Decimal here — that is the
    # reconciliation epic's job.
    value: Mapped[str] = mapped_column(String(60), nullable=False)
    raw_row_json: Mapped[str | None] = mapped_column(Text, nullable=True)


class LegacyUpload(Base, TimestampMixin):
    """One row per successful upload — minimal audit trail.

    Used by the dashboard's "last upload" badge and by the QA regression
    test in Story 8.6.
    """

    __tablename__ = "legacy_uploads"

    id: Mapped[int] = mapped_column(primary_key=True)
    # "students" | "grades"
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    academic_context_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # "ok" | "failed" (kept narrow for the dashboard badge)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    rows_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rows_persisted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
