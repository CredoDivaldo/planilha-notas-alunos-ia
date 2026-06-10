"""Add display_name and institution columns to users table.

Supports professor registration flow (Story Sprint-1).

Revision ID: 20260610_0006
Revises: 20260604_0005
Create Date: 2026-06-10 00:00:00.000000
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260610_0006"
down_revision: str | None = "20260604_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.add_column(
            sa.Column("display_name", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column("institution", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column("faculty", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column("disciplines", sa.Text(), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("disciplines")
        batch_op.drop_column("faculty")
        batch_op.drop_column("institution")
        batch_op.drop_column("display_name")
