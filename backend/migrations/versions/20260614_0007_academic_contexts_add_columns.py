"""Add class_group_id and subject_code to academic_contexts.

The router references these columns but migration 0003 created the table
without them. This migration adds them as nullable so existing rows are
preserved with NULL values.

Revision ID: 20260614_0007
Revises: 20260610_0006
Create Date: 2026-06-14 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260614_0007"
down_revision: str | None = "20260610_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("academic_contexts") as batch_op:
        batch_op.add_column(
            sa.Column("class_group_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("subject_code", sa.String(length=80), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("academic_contexts") as batch_op:
        batch_op.drop_column("subject_code")
        batch_op.drop_column("class_group_id")
