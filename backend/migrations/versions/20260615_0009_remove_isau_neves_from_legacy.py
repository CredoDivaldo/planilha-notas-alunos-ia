"""Remove Isaú Neves (student_number 2026002) from legacy tables.

Revision ID: 20260615_0009
Revises: 20260615_0008
Create Date: 2026-06-15
"""
from alembic import op

revision = "20260615_0009"
down_revision = "20260615_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "DELETE FROM legacy_students WHERE student_number = '2026002'"
    )
    op.execute(
        "DELETE FROM legacy_grades WHERE student_number = '2026002'"
    )


def downgrade() -> None:
    pass
