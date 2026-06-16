from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.app.cli import bootstrap_db

EXPECTED_TABLES = {
    "users",
    "students",
    "professors",
    "courses",
    "semesters",
    "shifts",
    "class_groups",
    "subjects",
    "teaching_assignments",
    "enrollments",
    "assessment_definitions",
    "grade_entries",
    "calculation_results",
    "broadcast_jobs",
    "notification_deliveries",
    "publication_snapshots",
    "calendar_events",
    "published_calendar_snapshots",
    "audit_log",
    # Story 5.2 additions
    "user_sessions",
    "delegate_assignments",
    "pending_credential_deliveries",
    # Story 5.4 additions
    "academic_contexts",
    "class_enrollments",
    "context_subject_configurations",
}


def test_bootstrap_db_applies_initial_academic_schema(tmp_path: Path) -> None:
    database_path = tmp_path / "app.sqlite3"
    report = bootstrap_db(f"sqlite:///{database_path}", force=True)

    assert report["database_path"] == str(database_path)
    assert report["migrations_target"] == "head"
    assert report["imported_rows"] == 0
    assert report["rejected_rows"] == 0

    with sqlite3.connect(database_path) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "select name from sqlite_master where type = 'table'",
            )
        }
        journal_mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
        alembic_version = connection.execute("select version_num from alembic_version").fetchone()

    assert EXPECTED_TABLES.issubset(table_names)
    assert journal_mode == "wal"
    # Migrations run to head; legacy tables are dropped by 0012.
    assert alembic_version == ("20260616_0013",)
    assert "legacy_students" not in table_names
    assert "legacy_grades" not in table_names
