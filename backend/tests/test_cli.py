from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from backend.app.cli import bootstrap_db, inspect_legacy_json

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
    assert alembic_version == ("20260601_0003",)


def test_legacy_json_import_dry_run_reports_counts_without_mutating_files(tmp_path: Path) -> None:
    students_path = tmp_path / "students.json"
    grades_path = tmp_path / "grades-last-upload.json"
    match_path = tmp_path / "match-last.json"

    students_path.write_text(json.dumps({"students": [{"id": 1}, {"id": 2}]}), encoding="utf-8")
    grades_path.write_text(json.dumps([{"student": "1"}]), encoding="utf-8")
    match_path.write_text(json.dumps({"matches": [{"student": "1"}]}), encoding="utf-8")

    original_payloads = {
        path.name: path.read_text(encoding="utf-8")
        for path in (students_path, grades_path, match_path)
    }

    report = inspect_legacy_json(tmp_path)

    assert report["dry_run"] is True
    assert report["applied"] is False
    assert report["total_rows"] == 4
    assert report["imported_rows"] == 0
    assert report["rejected_rows"] == 0
    assert {
        path.name: path.read_text(encoding="utf-8")
        for path in (students_path, grades_path, match_path)
    } == original_payloads
