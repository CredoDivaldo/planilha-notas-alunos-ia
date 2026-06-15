"""Remove Isaú Neves (student_number 2026002) from legacy tables.

Revision ID: 20260615_0009
Revises: 20260615_0008
Create Date: 2026-06-15
"""
from alembic import op
from sqlalchemy import inspect


revision = "20260615_0009"
down_revision = "20260615_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # legacy_* tables are ORM-only (created via Base.metadata.create_all),
    # so on a clean database they may not exist yet when this runs. Guard
    # the DELETE behind an existence check to stay idempotent.
    bind = op.get_bind()
    tables = set(inspect(bind).get_table_names())
    if "legacy_students" in tables:
        op.execute("DELETE FROM legacy_students WHERE student_number = '2026002'")
    if "legacy_grades" in tables:
        op.execute("DELETE FROM legacy_grades WHERE student_number = '2026002'")


def downgrade() -> None:
    pass
