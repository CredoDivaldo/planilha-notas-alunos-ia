"""Pure CSV parsing/normalising helpers (Story 8.1 — Epic 8 cutover).

These functions are the Python port of the legacy Express service:
    src/services/csv-parser.js
    src/services/csv-validator.js
    src/services/matcher.js

They are deliberately *pure* (no I/O, no DB) so the QA gate can exercise
the happy path and the failure paths without touching the database.
The router (``backend/app/routers/ingest.py``) is the only place that
joins these helpers to a SQLAlchemy session.

The function signatures mirror the legacy JS module 1-for-1 so the port
is reviewable line-by-line:

* ``parse_csv(text)`` ↔ ``parseCsv(buffer)``
* ``normalize_student(raw)`` ↔ ``normalizeStudent(raw)``
* ``normalize_grade(raw)`` ↔ ``normalizeGrade(raw)``
* ``validate_students_csv(headers, rows)`` ↔ ``validateStudentsCsv``
* ``validate_grades_csv(headers, rows)`` ↔ ``validateGradesCsv``
* ``check_file_size(size)`` ↔ ``checkFileSize``
* ``build_match(students, grades)`` ↔ ``buildMatch`` (in matcher.js)
* ``normalize_name(name)`` ↔ ``normalizeName`` (matcher.js)
* ``normalize_phone(phone)`` ↔ ``normalizePhone`` (matcher.js)
* ``is_valid_phone(phone)`` ↔ ``isValidPhone`` (matcher.js)
"""
from __future__ import annotations

import csv
import io
import unicodedata
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Constants — mirror the legacy JS module exactly
# ---------------------------------------------------------------------------

IDENTIFIER_COLS: tuple[str, ...] = (
    "numero_estudante",
    "numero",
    "numeroAluno",
    "id",
)
NAME_COLS: tuple[str, ...] = ("nome", "aluno")
MAX_FILE_SIZE_BYTES: int = 2 * 1024 * 1024  # 2 MB

# CSV header aliases for the subject / value columns (used by the matcher
# during reconciliation — Story 8.2 uses these to align grades.csv with
# students.csv).
SUBJECT_COLS: tuple[str, ...] = ("disciplina", "subject", "materia")
VALUE_COLS: tuple[str, ...] = ("nota", "media", "valor", "grade")


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedCsv:
    """A parsed CSV: header + rows. Mirrors ``parseCsv`` in csv-parser.js."""

    headers: list[str]
    rows: list[dict[str, str]]


@dataclass(frozen=True)
class ValidationResult:
    """The boolean / error envelope returned by the legacy validator."""

    valid: bool
    error: str | None


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_csv(text: str) -> ParsedCsv:
    """Parse a CSV string into ``ParsedCsv(headers, rows)``.

    Mirrors ``parseCsv(buffer)`` in the legacy module — same options
    (columns=True, skip_empty_lines=True, trim=True).
    """
    reader = csv.DictReader(io.StringIO(text))
    headers: list[str] = list(reader.fieldnames or [])
    rows = [
        {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        for row in reader
        if any((v or "").strip() for v in row.values())  # skip empty lines
    ]
    return ParsedCsv(headers=headers, rows=rows)


def _first_present(raw: dict[str, Any], candidates: tuple[str, ...]) -> str:
    for col in candidates:
        if col in raw and str(raw[col] or "").strip():
            return str(raw[col]).strip()
    return ""


def normalize_student(raw: dict[str, Any]) -> dict[str, str]:
    """Normalise one CSV row into the legacy ``Student`` shape.

    Mirrors ``normalizeStudent(raw)`` in csv-parser.js — same alias
    resolution (numero_estudante/numero/numeroAluno/id, etc).
    """
    return {
        "numero_estudante": _first_present(raw, IDENTIFIER_COLS),
        "nome": _first_present(raw, NAME_COLS),
        "turma": str(raw.get("turma") or "").strip(),
        "whatsapp": _first_present(raw, ("whatsapp", "telefone", "phone")),
    }


def normalize_grade(raw: dict[str, Any]) -> dict[str, str]:
    """Normalise one CSV row into the legacy ``Grade`` shape."""
    return {
        "numero_estudante": _first_present(raw, IDENTIFIER_COLS),
        "nome": _first_present(raw, NAME_COLS),
        "nota": _first_present(raw, VALUE_COLS),
        "turma": str(raw.get("turma") or "").strip(),
        "disciplina": _first_present(raw, SUBJECT_COLS),
    }


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def _has_any_col(headers: list[str], candidates: tuple[str, ...]) -> bool:
    return any(col in headers for col in candidates)


def validate_students_csv(headers: list[str], rows: list[dict[str, str]]) -> ValidationResult:
    if not rows:
        return ValidationResult(valid=False, error="Ficheiro CSV sem dados")
    if not _has_any_col(headers, IDENTIFIER_COLS):
        return ValidationResult(
            valid=False,
            error=f"Coluna de identificador em falta. Esperado: {', '.join(IDENTIFIER_COLS)}",
        )
    if not _has_any_col(headers, NAME_COLS):
        return ValidationResult(
            valid=False,
            error=f"Coluna de nome em falta. Esperado: {', '.join(NAME_COLS)}",
        )
    return ValidationResult(valid=True, error=None)


def validate_grades_csv(headers: list[str], rows: list[dict[str, str]]) -> ValidationResult:
    if not rows:
        return ValidationResult(valid=False, error="Ficheiro CSV sem dados")
    if not _has_any_col(headers, IDENTIFIER_COLS):
        return ValidationResult(
            valid=False,
            error=f"Coluna de identificador em falta. Esperado: {', '.join(IDENTIFIER_COLS)}",
        )
    return ValidationResult(valid=True, error=None)


def check_file_size(size: int) -> ValidationResult:
    """Enforce the 2 MB cap from AC-4."""
    if size > MAX_FILE_SIZE_BYTES:
        return ValidationResult(
            valid=False,
            error=(
                f"Ficheiro demasiado grande. Máximo: "
                f"{MAX_FILE_SIZE_BYTES // (1024 * 1024)} MB"
            ),
        )
    return ValidationResult(valid=True, error=None)
