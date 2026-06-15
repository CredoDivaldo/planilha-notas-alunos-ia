"""Link academic_contexts to teaching_assignments (1:1).

The professor-facing entity is ``academic_contexts`` (the frontend uses
``context_id`` everywhere). The normalized relational model scopes
assessment_definitions / grade_entries / publication_snapshots by
``teaching_assignment_id``. This column ties the two together so each
context maps to exactly one teaching assignment.

Revision ID: 20260615_0011
Revises: 20260615_0010
Create Date: 2026-06-15
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect


revision = "20260615_0011"
down_revision = "20260615_0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    cols = {c["name"] for c in inspect(bind).get_columns("academic_contexts")}
    if "teaching_assignment_id" not in cols:
        with op.batch_alter_table("academic_contexts") as batch_op:
            batch_op.add_column(
                sa.Column("teaching_assignment_id", sa.Integer(), nullable=True)
            )


def downgrade() -> None:
    with op.batch_alter_table("academic_contexts") as batch_op:
        batch_op.drop_column("teaching_assignment_id")
