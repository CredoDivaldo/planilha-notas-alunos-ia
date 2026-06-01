"""Academic contexts and rosters (Story 5.4).

Adds:
- academic_contexts table: professor's scoped teaching assignment
  (professor_id, turma, subject, semester_id, shift_id, academic_year, status)
  with compound unique constraint (professor_id, turma, subject, semester_id, shift_id)
- class_enrollments table: student roster per context
  (academic_context_id, student_id, enrollment_status, dropped_at, completed_at)
- context_subject_configurations table: subject-specific rules per context
  (academic_context_id, configuration_json)
- Extends audit_log: context_event_type for context lifecycle tracking

Revision ID: 20260601_0003
Revises: 20260531_0002
Create Date: 2026-06-01 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260601_0003"
down_revision: str | None = "20260531_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column[sa.DateTime], sa.Column[sa.DateTime]]:
    return (
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
    )


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # academic_contexts — professor's scoped teaching assignment          #
    # ------------------------------------------------------------------ #
    op.create_table(
        "academic_contexts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("professor_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("academic_year", sa.Integer(), nullable=False),
        sa.Column("turma", sa.String(length=60), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=False),
        sa.Column("shift_id", sa.Integer(), sa.ForeignKey("shifts.id"), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="draft", nullable=False),
        sa.Column("notes", sa.String(length=500), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint(
            "professor_id",
            "turma",
            "subject",
            "semester_id",
            "shift_id",
            name="uq_academic_contexts_professor_subject_scope",
        ),
    )
    op.create_index("ix_academic_contexts_professor_id", "academic_contexts", ["professor_id"])
    op.create_index("ix_academic_contexts_semester_id", "academic_contexts", ["semester_id"])
    op.create_index("ix_academic_contexts_shift_id", "academic_contexts", ["shift_id"])
    op.create_index("ix_academic_contexts_status", "academic_contexts", ["status"])
    op.create_index(
        "ix_academic_contexts_professor_status",
        "academic_contexts",
        ["professor_id", "status"],
    )

    # ------------------------------------------------------------------ #
    # class_enrollments — student roster per context                     #
    # ------------------------------------------------------------------ #
    op.create_table(
        "class_enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "academic_context_id", sa.Integer(), sa.ForeignKey("academic_contexts.id"), nullable=False
        ),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("enrollment_status", sa.String(length=40), server_default="active", nullable=False),
        sa.Column("dropped_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint(
            "academic_context_id",
            "student_id",
            name="uq_class_enrollments_context_student",
        ),
    )
    op.create_index("ix_class_enrollments_academic_context_id", "class_enrollments", ["academic_context_id"])
    op.create_index("ix_class_enrollments_student_id", "class_enrollments", ["student_id"])
    op.create_index(
        "ix_class_enrollments_status",
        "class_enrollments",
        ["enrollment_status"],
    )
    op.create_index(
        "ix_class_enrollments_context_status",
        "class_enrollments",
        ["academic_context_id", "enrollment_status"],
    )

    # ------------------------------------------------------------------ #
    # context_subject_configurations — flexible per-context rules        #
    # ------------------------------------------------------------------ #
    op.create_table(
        "context_subject_configurations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "academic_context_id",
            sa.Integer(),
            sa.ForeignKey("academic_contexts.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column("configuration_json", sa.Text(), nullable=False),
        *_timestamps(),
    )
    op.create_index(
        "ix_context_subject_configurations_academic_context_id",
        "context_subject_configurations",
        ["academic_context_id"],
    )

    # ------------------------------------------------------------------ #
    # Extend audit_log for context lifecycle events                      #
    # ------------------------------------------------------------------ #
    op.add_column(
        "audit_log",
        sa.Column("context_event_type", sa.String(length=80), nullable=True),
    )
    # Valid context event types: context_created, context_activated, context_archived,
    # enrollment_added, enrollment_dropped, enrollment_completed


def downgrade() -> None:
    op.drop_column("audit_log", "context_event_type")
    op.drop_table("context_subject_configurations")
    op.drop_table("class_enrollments")
    op.drop_table("academic_contexts")
