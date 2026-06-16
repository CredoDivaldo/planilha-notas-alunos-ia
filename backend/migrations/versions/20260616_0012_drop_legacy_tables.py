"""Drop the legacy CSV-shaped tables and academic_contexts.components_json.

The application now uses the normalized relational model (students /
class_enrollments / grade_entries / publication_snapshots). The legacy
CSV bridge tables and the components_json blob are no longer used.

Revision ID: 20260616_0012
Revises: 20260615_0011
Create Date: 2026-06-16
"""
from alembic import op
from sqlalchemy import inspect


revision = "20260616_0012"
down_revision = "20260615_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)
    tables = set(insp.get_table_names())

    for tbl in ("legacy_grades", "legacy_students", "legacy_uploads"):
        if tbl in tables:
            op.drop_table(tbl)

    if "academic_contexts" in tables:
        cols = {c["name"] for c in insp.get_columns("academic_contexts")}
        if "components_json" in cols:
            with op.batch_alter_table("academic_contexts") as batch_op:
                batch_op.drop_column("components_json")


def downgrade() -> None:
    # One-way cleanup; legacy tables are not recreated.
    pass
