"""Add components_json to academic_contexts for persistent grade component config.

Stores assessment component definitions (name + weight) as a JSON string
directly on the context row, bypassing the teaching_assignment FK requirement.

Revision ID: 20260615_0008
Revises: 20260614_0007
Create Date: 2026-06-15 00:00:00.000000
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260615_0008"
down_revision = "20260614_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("academic_contexts") as batch_op:
        batch_op.add_column(sa.Column("components_json", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("academic_contexts") as batch_op:
        batch_op.drop_column("components_json")
