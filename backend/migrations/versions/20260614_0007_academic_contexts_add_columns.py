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
from sqlalchemy import inspect

revision: str = "20260614_0007"
down_revision: str | None = "20260610_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Idempotent: create_all may have already added these columns on a
    # database whose alembic_version lagged behind (hybrid local DBs).
    bind = op.get_bind()
    existing = {c["name"] for c in inspect(bind).get_columns("academic_contexts")}
    to_add = []
    if "class_group_id" not in existing:
        to_add.append(sa.Column("class_group_id", sa.Integer(), nullable=True))
    if "subject_code" not in existing:
        to_add.append(sa.Column("subject_code", sa.String(length=80), nullable=True))
    if not to_add:
        return
    with op.batch_alter_table("academic_contexts") as batch_op:
        for col in to_add:
            batch_op.add_column(col)


def downgrade() -> None:
    with op.batch_alter_table("academic_contexts") as batch_op:
        batch_op.drop_column("subject_code")
        batch_op.drop_column("class_group_id")
