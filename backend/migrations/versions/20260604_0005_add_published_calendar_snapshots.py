"""Rebuild published_calendar_snapshots for student portal calendar (Story 5.6).

The initial schema (20260528_0001) created a legacy `published_calendar_snapshots`
table tied to the Node.js data model (calendar_events FK, class_group_id, etc.).
This migration replaces it with the Story 5.6 schema aligned with academic_contexts
and the student portal read model.

Revision ID: 20260604_0005
Revises: 20260601_0004
Create Date: 2026-06-04 10:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260604_0005"
down_revision: str | None = "20260601_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop the legacy index and table from the initial Node.js schema
    op.drop_index(
        "ix_published_calendar_snapshots_context_current",
        table_name="published_calendar_snapshots",
    )
    op.drop_table("published_calendar_snapshots")

    # Recreate with the Story 5.6 schema for academic_contexts-based portal calendar
    op.create_table(
        "published_calendar_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "academic_context_id",
            sa.Integer(),
            sa.ForeignKey("academic_contexts.id"),
            nullable=False,
        ),
        # Nullable: NULL means class-wide event visible to all enrolled students
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id"),
            nullable=True,
        ),
        # event_type: exam | recurso | prova
        sa.Column("event_type", sa.String(length=40), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=True),
        sa.Column("location", sa.String(length=300), nullable=True),
        # Draft until explicitly published
        sa.Column(
            "is_published",
            sa.Boolean(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        # Nullable FK to the broadcast job that triggered publication
        sa.Column(
            "broadcast_job_id",
            sa.Integer(),
            sa.ForeignKey("broadcast_jobs.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_published_calendar_snapshots_academic_context_id",
        "published_calendar_snapshots",
        ["academic_context_id"],
    )
    op.create_index(
        "ix_published_calendar_snapshots_student_id",
        "published_calendar_snapshots",
        ["student_id"],
    )
    op.create_index(
        "ix_published_calendar_snapshots_is_published",
        "published_calendar_snapshots",
        ["is_published"],
    )


def downgrade() -> None:
    # Drop Story 5.6 table and indices
    op.drop_index(
        "ix_published_calendar_snapshots_is_published",
        table_name="published_calendar_snapshots",
    )
    op.drop_index(
        "ix_published_calendar_snapshots_student_id",
        table_name="published_calendar_snapshots",
    )
    op.drop_index(
        "ix_published_calendar_snapshots_academic_context_id",
        table_name="published_calendar_snapshots",
    )
    op.drop_table("published_calendar_snapshots")

    # Restore the legacy Node.js schema (from 20260528_0001)
    op.create_table(
        "published_calendar_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "calendar_event_id",
            sa.Integer(),
            sa.ForeignKey("calendar_events.id"),
            nullable=True,
        ),
        sa.Column(
            "broadcast_job_id",
            sa.Integer(),
            sa.ForeignKey("broadcast_jobs.id"),
            nullable=False,
        ),
        sa.Column(
            "class_group_id", sa.Integer(), sa.ForeignKey("class_groups.id"), nullable=True
        ),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id"), nullable=True),
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.Column("published_payload_json", sa.Text(), nullable=False),
        sa.Column(
            "is_current",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column(
            "published_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_published_calendar_snapshots_context_current",
        "published_calendar_snapshots",
        ["class_group_id", "semester_id", "subject_id", "is_current"],
    )
