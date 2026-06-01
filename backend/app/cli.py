from __future__ import annotations

import argparse
import csv
import json
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from backend.app.config import Settings
from backend.app.database import build_engine, ensure_sqlite_directory
from backend.app.models import AcademicContext, ClassEnrollment, ContextSubjectConfiguration
from backend.app.models import Semester, Shift

LOGGER = logging.getLogger("backend.cli")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = Settings.database_url
LEGACY_JSON_FILES = ("students.json", "grades-last-upload.json", "match-last.json")


def _alembic_config(database_url: str) -> Config:
    config = Config(str(ROOT_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _revision_count() -> int:
    versions_dir = ROOT_DIR / "backend" / "migrations" / "versions"
    return len(list(versions_dir.glob("*.py")))


def _remove_sqlite_files(sqlite_path: Path) -> int:
    removed = 0
    for candidate in (
        sqlite_path,
        sqlite_path.with_suffix(sqlite_path.suffix + "-wal"),
        sqlite_path.with_suffix(sqlite_path.suffix + "-shm"),
    ):
        if candidate.exists():
            candidate.unlink()
            removed += 1
    return removed


def bootstrap_db(database_url: str, force: bool) -> dict[str, Any]:
    sqlite_path = ensure_sqlite_directory(database_url)
    removed_files = 0
    if force and sqlite_path is not None:
        removed_files = _remove_sqlite_files(sqlite_path)

    command.upgrade(_alembic_config(database_url), "head")
    report = {
        "database_url": database_url,
        "database_path": str(sqlite_path) if sqlite_path else None,
        "clean_requested": force,
        "sqlite_files_removed": removed_files,
        "migrations_available": _revision_count(),
        "migrations_target": "head",
        "imported_rows": 0,
        "rejected_rows": 0,
    }
    LOGGER.info("bootstrap_db_completed", extra=report)
    return report


def _count_json_records(payload: Any) -> int:
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("students", "grades", "matches", "items", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
        return 1
    return 0


def inspect_legacy_json(source_dir: Path) -> dict[str, Any]:
    file_reports: list[dict[str, Any]] = []
    total_rows = 0
    rejected_rows = 0

    for filename in LEGACY_JSON_FILES:
        path = source_dir / filename
        if not path.exists():
            file_reports.append(
                {"file": filename, "status": "missing", "rows": 0, "rejected_rows": 0}
            )
            continue

        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            rejected_rows += 1
            file_reports.append(
                {
                    "file": filename,
                    "status": "invalid_json",
                    "rows": 0,
                    "rejected_rows": 1,
                    "error": exc.msg,
                }
            )
            continue

        rows = _count_json_records(payload)
        total_rows += rows
        file_reports.append({"file": filename, "status": "read", "rows": rows, "rejected_rows": 0})

    report = {
        "source_dir": str(source_dir),
        "dry_run": True,
        "applied": False,
        "files": file_reports,
        "total_rows": total_rows,
        "imported_rows": 0,
        "rejected_rows": rejected_rows,
        "conflicts": 0,
    }
    LOGGER.info("legacy_import_dry_run_completed", extra=report)
    return report


def bootstrap_academic_contexts(
    database_url: str,
    csv_path: Path,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Bootstrap academic contexts from CSV.

    Expected CSV columns:
    - professor_id (int)
    - turma (str)
    - subject (str)
    - semester_id (int)
    - shift_id (int)
    - academic_year (int)
    - notes (optional, str)

    Returns a report of contexts created or validation failures.
    """
    if not csv_path.exists():
        return {
            "status": "error",
            "message": f"CSV file not found: {csv_path}",
            "contexts_created": 0,
            "contexts_failed": 0,
        }

    engine = build_engine(database_url)
    created = 0
    failed = 0
    errors: list[dict[str, Any]] = []

    try:
        with Session(engine) as session:
            with open(csv_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
                    try:
                        professor_id = int(row["professor_id"])
                        turma = row["turma"]
                        subject = row["subject"]
                        semester_id = int(row["semester_id"])
                        shift_id = int(row["shift_id"])
                        academic_year = int(row["academic_year"])
                        notes = row.get("notes", "")

                        context = AcademicContext(
                            professor_id=professor_id,
                            turma=turma,
                            subject=subject,
                            semester_id=semester_id,
                            shift_id=shift_id,
                            academic_year=academic_year,
                            notes=notes if notes else None,
                            status="draft",
                        )
                        session.add(context)
                        created += 1
                    except (KeyError, ValueError) as exc:
                        failed += 1
                        errors.append({
                            "row": row_num,
                            "error": str(exc),
                            "data": dict(row),
                        })

            if not dry_run:
                session.commit()
                LOGGER.info("bootstrap_academic_contexts_completed", extra={
                    "contexts_created": created,
                    "contexts_failed": failed,
                    "dry_run": False,
                })
    finally:
        engine.dispose()

    return {
        "status": "success" if failed == 0 else "partial",
        "csv_path": str(csv_path),
        "dry_run": dry_run,
        "contexts_created": created,
        "contexts_failed": failed,
        "errors": errors if errors else None,
    }


def import_context_rosters(
    database_url: str,
    csv_path: Path,
    context_id: int | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Import student roster into a context from CSV.

    Expected CSV columns:
    - student_id (int)
    - enrollment_status (str: active, dropped, completed)

    If context_id not specified, expects a 'context_id' column in CSV.
    """
    if not csv_path.exists():
        return {
            "status": "error",
            "message": f"CSV file not found: {csv_path}",
            "enrollments_created": 0,
            "enrollments_failed": 0,
        }

    engine = build_engine(database_url)
    created = 0
    failed = 0
    errors: list[dict[str, Any]] = []

    try:
        with Session(engine) as session:
            with open(csv_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        student_id = int(row["student_id"])
                        enrollment_status = row.get("enrollment_status", "active")
                        ctx_id = context_id if context_id else int(row["context_id"])

                        enrollment = ClassEnrollment(
                            academic_context_id=ctx_id,
                            student_id=student_id,
                            enrollment_status=enrollment_status,
                        )
                        session.add(enrollment)
                        created += 1
                    except (KeyError, ValueError) as exc:
                        failed += 1
                        errors.append({
                            "row": row_num,
                            "error": str(exc),
                            "data": dict(row),
                        })

            if not dry_run:
                session.commit()
                LOGGER.info("import_context_rosters_completed", extra={
                    "enrollments_created": created,
                    "enrollments_failed": failed,
                    "dry_run": False,
                })
    finally:
        engine.dispose()

    return {
        "status": "success" if failed == 0 else "partial",
        "csv_path": str(csv_path),
        "context_id": context_id,
        "dry_run": dry_run,
        "enrollments_created": created,
        "enrollments_failed": failed,
        "errors": errors if errors else None,
    }


def _json_print(report: dict[str, Any]) -> None:
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Academic backend local operations")
    subparsers = parser.add_subparsers(dest="command", required=True)

    bootstrap = subparsers.add_parser("bootstrap-db", help="Create a clean local SQLite DB")
    bootstrap.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    bootstrap.add_argument(
        "--force", action="store_true", help="Remove existing SQLite files first"
    )

    legacy_import = subparsers.add_parser(
        "import-legacy-json",
        help="Inspect legacy JSON files and emit a dry-run import report",
    )
    legacy_import.add_argument("--source-dir", default="data")
    legacy_import.add_argument("--dry-run", action="store_true", default=True)

    bootstrap_contexts = subparsers.add_parser(
        "bootstrap-academic-contexts",
        help="Bootstrap academic contexts from CSV (bulk import)",
    )
    bootstrap_contexts.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    bootstrap_contexts.add_argument(
        "--csv-path", required=True, help="Path to CSV file with context definitions"
    )
    bootstrap_contexts.add_argument(
        "--dry-run", action="store_true", help="Preview without persisting"
    )

    import_rosters = subparsers.add_parser(
        "import-context-rosters",
        help="Import student rosters into a context from CSV",
    )
    import_rosters.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    import_rosters.add_argument(
        "--csv-path", required=True, help="Path to CSV file with student roster"
    )
    import_rosters.add_argument(
        "--context-id", type=int, help="Target context ID (or use CSV column)"
    )
    import_rosters.add_argument(
        "--dry-run", action="store_true", help="Preview without persisting"
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "bootstrap-db":
        _json_print(bootstrap_db(args.database_url, args.force))
        return 0

    if args.command == "import-legacy-json":
        _json_print(inspect_legacy_json(Path(args.source_dir)))
        return 0

    if args.command == "bootstrap-academic-contexts":
        _json_print(bootstrap_academic_contexts(
            args.database_url,
            Path(args.csv_path),
            args.dry_run,
        ))
        return 0

    if args.command == "import-context-rosters":
        _json_print(import_context_rosters(
            args.database_url,
            Path(args.csv_path),
            args.context_id,
            args.dry_run,
        ))
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
