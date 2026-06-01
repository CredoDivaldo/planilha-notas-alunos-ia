"""AC-8: Grade entries scoped to academic context (Story 5.4).

Adds:
- academic_context_id field to grade_entries table
- Foreign key constraint to academic_contexts
- Compound unique constraint updated to include context scoping
- Index for efficient context-based queries

Revision ID: 20260601_0004
Revises: 20260601_0003
Create Date: 2026-06-01 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260601_0004"
down_revision: str | None = "20260601_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Use batch mode for SQLite FK constraints
    # This allows us to add a column with a foreign key on SQLite
    with op.batch_alter_table("grade_entries") as batch_op:
        batch_op.add_column(
            sa.Column(
                "academic_context_id",
                sa.Integer(),
                sa.ForeignKey("academic_contexts.id", name="fk_grade_entries_academic_context_id"),
                nullable=True,
            )
        )

    # Create index for efficient context-based queries
    op.create_index(
        "ix_grade_entries_academic_context_id",
        "grade_entries",
        ["academic_context_id"],
    )

    # Create compound index for context + student queries (common in validation)
    op.create_index(
        "ix_grade_entries_context_student",
        "grade_entries",
        ["academic_context_id", "student_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_grade_entries_context_student", table_name="grade_entries")
    op.drop_index("ix_grade_entries_academic_context_id", table_name="grade_entries")

    with op.batch_alter_table("grade_entries") as batch_op:
        batch_op.drop_column("academic_context_id")
