"""Fix class_enrollments.student_id FK: users(id) -> students(id).

Migration 0003 created class_enrollments.student_id as a FK to users(id)
(pre-normalized model where a student WAS a user). In the normalized model
students live in the `students` table, so enrolments must reference
students(id). The wrong FK made the 2nd+ student upload fail with
"FOREIGN KEY constraint failed".

Recreates the table with the corrected FK. class_enrollments is empty in
practice (the legacy path used legacy_students), but any rows whose
student_id maps to a valid students.id are preserved.

Revision ID: 20260616_0013
Revises: 20260616_0012
Create Date: 2026-06-16
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect, text


revision = "20260616_0013"
down_revision = "20260616_0012"
branch_labels = None
depends_on = None


def _create_table() -> None:
    op.create_table(
        "class_enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "academic_context_id", sa.Integer(),
            sa.ForeignKey("academic_contexts.id"), nullable=False,
        ),
        sa.Column(
            "student_id", sa.Integer(),
            sa.ForeignKey("students.id"), nullable=False,
        ),
        sa.Column("enrollment_status", sa.String(length=40), server_default="active", nullable=False),
        sa.Column("dropped_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.UniqueConstraint("academic_context_id", "student_id", name="uq_class_enrollments_context_student"),
    )
    op.create_index("ix_class_enrollments_academic_context_id", "class_enrollments", ["academic_context_id"])
    op.create_index("ix_class_enrollments_student_id", "class_enrollments", ["student_id"])


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    if "class_enrollments" not in insp.get_table_names():
        _create_table()
        return

    # Preserve rows whose student_id is a valid students.id
    valid = {r[0] for r in bind.execute(text("SELECT id FROM students"))}
    rows = [dict(r._mapping) for r in bind.execute(text(
        "SELECT academic_context_id, student_id, enrollment_status, dropped_at,"
        " completed_at, created_at, updated_at FROM class_enrollments"
    ))]
    keep = [r for r in rows if r.get("student_id") in valid]

    op.drop_table("class_enrollments")
    _create_table()

    for r in keep:
        bind.execute(text(
            "INSERT INTO class_enrollments"
            " (academic_context_id, student_id, enrollment_status, dropped_at, completed_at, created_at, updated_at)"
            " VALUES (:ac, :s, :st, :da, :ca, :cr, :up)"
        ), {
            "ac": r["academic_context_id"], "s": r["student_id"],
            "st": r.get("enrollment_status") or "active",
            "da": r.get("dropped_at"), "ca": r.get("completed_at"),
            "cr": r.get("created_at"), "up": r.get("updated_at"),
        })


def downgrade() -> None:
    pass
