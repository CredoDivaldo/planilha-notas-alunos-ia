"""Legacy CSV ingest router (Story 8.1 — Epic 8 cutover).

Two endpoints, both ``multipart/form-data`` with a single ``file`` field:

* ``POST /api/v1/students/upload`` — students roster CSV
* ``POST /api/v1/grades/upload``   — grades CSV

The implementation reuses the pure helpers in
``backend.app.services.legacy_import`` and persists into the narrow
``legacy_students`` / ``legacy_grades`` / ``legacy_uploads`` tables
defined in ``backend.app.models.legacy_roster``.

Acceptance criteria mapping (see plan file §Story 8.1):

* AC1 — students upload returns ``{count, students}``
* AC2 — grades upload returns ``{count, grades}``
* AC3 — invalid CSV returns 400 with sanitised detail
* AC4 — file > 2 MB returns 400
* AC5 — bulk insert is transactional (single ``session.commit()``)
* AC6 — ``pytest backend/tests/test_ingest.py`` covers all of the above
"""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models import (
    LegacyGrade,
    LegacyStudent,
    LegacyUpload,
    UPLOAD_STATUS_FAILED,
    UPLOAD_STATUS_OK,
)
from backend.app.routers.chatbot import get_db_session
from backend.app.services.legacy_import import (
    check_file_size,
    normalize_grade,
    normalize_student,
    parse_csv,
    validate_grades_csv,
    validate_students_csv,
)

LOGGER = logging.getLogger("backend.ingest.routes")

router = APIRouter(prefix="/api/v1", tags=["ingest"])

MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # AC-4: 2 MB cap

# MIME types browsers may send for a CSV upload. We are permissive here
# because real-world uploads sometimes come through as ``text/plain`` or
# ``application/vnd.ms-excel`` depending on the OS.
ACCEPTED_CSV_MIME = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/octet-stream",
    "text/plain",
}


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class StudentRow(BaseModel):
    student_number: str
    name: str
    turma: str | None = None
    whatsapp: str | None = None


class StudentsUploadResponse(BaseModel):
    count: int
    students: list[StudentRow]


class GradeRow(BaseModel):
    student_number: str
    name: str | None = None
    turma: str | None = None
    subject: str | None = None
    value: str


class GradesUploadResponse(BaseModel):
    count: int
    grades: list[GradeRow]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _coerce_context_id(raw: str | int | None) -> int | None:
    """Accept ``?context_id=12`` query param; return ``int | None``."""
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid context_id; must be an integer.",
        )


def _validate_upload_file(file: UploadFile) -> None:
    """AC-3/AC-4: file size and MIME checks. Raises 400 on failure."""
    if file.content_type and file.content_type not in ACCEPTED_CSV_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported content_type: {file.content_type}",
        )
    if file.size is not None and file.size > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File exceeds 2MB limit",
        )


def _safe_detail(message: str) -> str:
    """Story 3.6 — keep error messages short; no internals leaked."""
    if len(message) > 240:
        return message[:237] + "..."
    return message


# ---------------------------------------------------------------------------
# Students upload
# ---------------------------------------------------------------------------


@router.post(
    "/students/upload",
    response_model=StudentsUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_students(
    request: Request,
    file: UploadFile = File(...),
    context_id: str | None = Query(default=None),
) -> StudentsUploadResponse:
    """AC-1: parse students CSV and persist idempotently.

    Bulk insert is transactional: a single ``session.commit()`` after all
    upserts (AC-5). Idempotency is provided by deleting prior rows for the
    same ``(academic_context_id, student_number)`` tuple before re-inserting.
    """
    _validate_upload_file(file)
    context_pk = _coerce_context_id(context_id)

    raw_bytes = await file.read()
    size_check = check_file_size(len(raw_bytes))
    if not size_check.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_detail(size_check.error or "Invalid file"),
        )

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV encoding; expected UTF-8",
        ) from exc

    parsed = parse_csv(text)
    validation = validate_students_csv(parsed.headers, parsed.rows)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_detail(validation.error or "Invalid CSV"),
        )

    normalised = [normalize_student(row) for row in parsed.rows]
    # Drop rows that are missing the required identifier — matches the
    # legacy behaviour where the dashboard simply skipped them.
    normalised = [n for n in normalised if n.get("numero_estudante") and n.get("nome")]

    session: Session = get_db_session(request)
    audit = LegacyUpload(
        kind="students",
        academic_context_id=context_pk,
        filename=file.filename,
        status=UPLOAD_STATUS_FAILED,
        rows_received=len(normalised),
        rows_persisted=0,
    )
    try:
        # Idempotent re-upload: remove the old rows for this tuple.
        if normalised:
            existing_numbers = [n["numero_estudante"] for n in normalised]
            q = session.query(LegacyStudent).filter(
                LegacyStudent.student_number.in_(existing_numbers)
            )
            if context_pk is not None:
                q = q.filter(LegacyStudent.academic_context_id == context_pk)
            else:
                q = q.filter(LegacyStudent.academic_context_id.is_(None))
            q.delete(synchronize_session=False)
        for n, raw in zip(normalised, parsed.rows):
            session.add(
                LegacyStudent(
                    academic_context_id=context_pk,
                    student_number=n["numero_estudante"],
                    name=n["nome"],
                    turma=n.get("turma") or None,
                    whatsapp=n.get("whatsapp") or None,
                    raw_row_json=json.dumps(raw, ensure_ascii=False),
                )
            )
        session.add(audit)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.exception("students_upload_failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_detail(f"Database error: {exc.__class__.__name__}"),
        ) from exc

    audit.status = UPLOAD_STATUS_OK
    audit.rows_persisted = len(normalised)
    session.commit()

    return StudentsUploadResponse(
        count=len(normalised),
        students=[
            StudentRow(
                student_number=n["numero_estudante"],
                name=n["nome"],
                turma=n.get("turma") or None,
                whatsapp=n.get("whatsapp") or None,
            )
            for n in normalised
        ],
    )


# ---------------------------------------------------------------------------
# Grades upload
# ---------------------------------------------------------------------------


@router.post(
    "/grades/upload",
    response_model=GradesUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_grades(
    request: Request,
    file: UploadFile = File(...),
    context_id: str | None = Query(default=None),
    component_id: str | None = Query(default=None),
) -> GradesUploadResponse:
    """AC-2: parse grades CSV and persist idempotently.

    Same transactional / idempotent contract as ``/students/upload``.
    """
    _validate_upload_file(file)
    context_pk = _coerce_context_id(context_id)

    raw_bytes = await file.read()
    size_check = check_file_size(len(raw_bytes))
    if not size_check.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_detail(size_check.error or "Invalid file"),
        )

    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV encoding; expected UTF-8",
        ) from exc

    parsed = parse_csv(text)
    validation = validate_grades_csv(parsed.headers, parsed.rows)
    if not validation.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_detail(validation.error or "Invalid CSV"),
        )

    normalised = [normalize_grade(row) for row in parsed.rows]
    normalised = [n for n in normalised if n.get("numero_estudante") and n.get("nota")]

    session: Session = get_db_session(request)
    audit = LegacyUpload(
        kind="grades",
        academic_context_id=context_pk,
        filename=file.filename,
        status=UPLOAD_STATUS_FAILED,
        rows_received=len(normalised),
        rows_persisted=0,
    )
    try:
        if context_pk is not None and normalised:
            existing_numbers = [n["numero_estudante"] for n in normalised]
            q = (
                session.query(LegacyGrade)
                .filter(LegacyGrade.academic_context_id == context_pk)
                .filter(LegacyGrade.student_number.in_(existing_numbers))
            )
            # Scope idempotency to this component so other components aren't wiped
            if component_id is not None:
                q = q.filter(LegacyGrade.subject == component_id)
            q.delete(synchronize_session=False)
        for n, raw in zip(normalised, parsed.rows):
            session.add(
                LegacyGrade(
                    academic_context_id=context_pk,
                    student_number=n["numero_estudante"],
                    name=n.get("nome") or None,
                    turma=n.get("turma") or None,
                    # Store component_id as subject so GET /grades/ can map correctly
                    subject=component_id if component_id is not None else (n.get("disciplina") or None),
                    value=n["nota"],
                    raw_row_json=json.dumps(raw, ensure_ascii=False),
                )
            )
        session.add(audit)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.exception("grades_upload_failed")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_detail(f"Database error: {exc.__class__.__name__}"),
        ) from exc

    audit.status = UPLOAD_STATUS_OK
    audit.rows_persisted = len(normalised)
    session.commit()

    return GradesUploadResponse(
        count=len(normalised),
        grades=[
            GradeRow(
                student_number=n["numero_estudante"],
                name=n.get("nome") or None,
                turma=n.get("turma") or None,
                subject=n.get("disciplina") or None,
                value=n["nota"],
            )
            for n in normalised
        ],
    )


# ---------------------------------------------------------------------------
# Compatibility shims for the legacy path shape
# ---------------------------------------------------------------------------
#
# The legacy dashboard (Express, ``src/routes/students.js``) exposed:
#     GET /students/upload      -> HTML upload form
#     GET /grades/upload        -> HTML upload form
# These were the *browsable* entry points. The new router does not need
# to expose a GET handler (uploads are POST + multipart), but we keep the
# routes out of the API to make the cutover regression test in Story 8.6
# trivial: a GET to the legacy shape should still 404, and a POST to the
# new shape should be the only accepted verb.
__all__: list[Any] = ["router"]
