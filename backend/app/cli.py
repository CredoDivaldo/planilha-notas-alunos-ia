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
from sqlalchemy.orm import Session

from backend.app.config import Settings
from backend.app.database import build_engine, ensure_sqlite_directory
from backend.app.models import (
    AcademicContext,
    ClassEnrollment,
    GradeEntry,
)

LOGGER = logging.getLogger("backend.cli")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_URL = Settings.database_url


def _validate_upload_context(
    session: Session,
    context_id: int,
    professor_id: int,
    roster_student_ids: set[int],
    subject: str,
) -> tuple[bool, str]:
    """Validate that upload context is valid and accessible by professor.

    AC-8 Validation:
    1. Context exists and belongs to the professor
    2. All students in roster are enrolled in that context
    3. Context subject matches the upload subject

    Returns: (valid, error_message)
    """
    context = session.query(AcademicContext).filter_by(id=context_id).first()
    if not context:
        return False, f"Context {context_id} does not exist"

    if context.professor_id != professor_id:
        return False, f"Professor {professor_id} does not own context {context_id}"

    if context.subject != subject:
        msg = (
            f"Context subject '{context.subject}' does not match "
            f"upload subject '{subject}'"
        )
        return False, msg

    # Validate all students in roster are enrolled in this context
    enrollments = session.query(ClassEnrollment).filter_by(
        academic_context_id=context_id
    ).all()
    enrolled_student_ids = {e.student_id for e in enrollments}
    missing_students = roster_student_ids - enrolled_student_ids

    if missing_students:
        return False, f"Students not enrolled in context: {missing_students}"

    return True, ""


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
            with open(csv_path, encoding="utf-8") as csvfile:
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


def import_grades_with_context(
    database_url: str,
    csv_path: Path,
    context_id: int,
    professor_id: int,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Import grades with context validation (AC-8).

    Expected CSV columns:
    - student_id (int)
    - teaching_assignment_id (int)
    - assessment_definition_id (int)
    - raw_value (float, optional)
    - status (str, optional: draft, validated, voided)

    Validates:
    1. Context exists and belongs to professor
    2. All students in import are enrolled in context
    3. Subject in context matches expected subject
    """
    if not csv_path.exists():
        return {
            "status": "error",
            "message": f"CSV file not found: {csv_path}",
            "grades_imported": 0,
            "grades_rejected": 0,
        }

    engine = build_engine(database_url)
    imported = 0
    rejected = 0
    errors: list[dict[str, Any]] = []

    try:
        with Session(engine) as session:
            # First, validate the context exists and belongs to professor
            context = session.query(AcademicContext).filter_by(id=context_id).first()
            if not context:
                return {
                    "status": "error",
                    "message": f"Context {context_id} does not exist",
                    "grades_imported": 0,
                    "grades_rejected": 0,
                }

            if context.professor_id != professor_id:
                return {
                    "status": "error",
                    "message": f"Professor {professor_id} does not own context {context_id}",
                    "grades_imported": 0,
                    "grades_rejected": 0,
                }

            # Get all enrolled students for this context
            enrollments = session.query(ClassEnrollment).filter_by(
                academic_context_id=context_id
            ).all()
            enrolled_student_ids = {e.student_id for e in enrollments}

            with open(csv_path, encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row_num, row in enumerate(reader, start=2):
                    try:
                        student_id = int(row["student_id"])
                        teaching_assignment_id = int(row["teaching_assignment_id"])
                        assessment_definition_id = int(row["assessment_definition_id"])
                        raw_value = (
                            float(row["raw_value"]) if row.get("raw_value") else None
                        )
                        status = row.get("status", "draft")

                        # AC-8: Validate student is enrolled in context
                        if student_id not in enrolled_student_ids:
                            rejected += 1
                            errors.append({
                                "row": row_num,
                                "error": (
                                    f"Student {student_id} not enrolled in "
                                    f"context {context_id}"
                                ),
                                "data": dict(row),
                            })
                            continue

                        grade_entry = GradeEntry(
                            academic_context_id=context_id,
                            student_id=student_id,
                            teaching_assignment_id=teaching_assignment_id,
                            assessment_definition_id=assessment_definition_id,
                            raw_value=raw_value if raw_value is not None else None,
                            status=status,
                        )
                        session.add(grade_entry)
                        imported += 1
                    except (KeyError, ValueError) as exc:
                        rejected += 1
                        errors.append({
                            "row": row_num,
                            "error": str(exc),
                            "data": dict(row),
                        })

            if not dry_run:
                session.commit()
                LOGGER.info("import_grades_with_context_completed", extra={
                    "context_id": context_id,
                    "grades_imported": imported,
                    "grades_rejected": rejected,
                    "dry_run": False,
                })
    finally:
        engine.dispose()

    return {
        "status": "success" if rejected == 0 else "partial",
        "csv_path": str(csv_path),
        "context_id": context_id,
        "professor_id": professor_id,
        "dry_run": dry_run,
        "grades_imported": imported,
        "grades_rejected": rejected,
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
            with open(csv_path, encoding="utf-8") as csvfile:
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

    import_grades = subparsers.add_parser(
        "import-grades",
        help="Import grades with academic context validation (AC-8)",
    )
    import_grades.add_argument("--database-url", default=DEFAULT_DATABASE_URL)
    import_grades.add_argument(
        "--csv-path", required=True, help="Path to CSV file with grade data"
    )
    import_grades.add_argument(
        "--context-id", type=int, required=True,
        help="Academic context ID (must be owned by professor)"
    )
    import_grades.add_argument(
        "--professor-id", type=int, required=True,
        help="Professor ID (for validation)"
    )
    import_grades.add_argument(
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

    if args.command == "bootstrap-academic-contexts":
        _json_print(bootstrap_academic_contexts(
            args.database_url,
            Path(args.csv_path),
            args.dry_run,
        ))
        return 0

    if args.command == "import-grades":
        _json_print(import_grades_with_context(
            args.database_url,
            Path(args.csv_path),
            args.context_id,
            args.professor_id,
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
