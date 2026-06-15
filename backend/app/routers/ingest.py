"""CSV ingest router — students roster and grades upload.

Two endpoints, both ``multipart/form-data`` with a single ``file`` field:

* ``POST /api/v1/students/upload?context_id=...``                — students roster CSV
* ``POST /api/v1/grades/upload?context_id=...&component_id=...`` — grades CSV

Persists into the normalized relational model via
``backend.app.services.academic_provisioning`` (``students`` /
``class_enrollments`` / ``grade_entries``). CSV parsing/validation reuses the
pure helpers in ``backend.app.services.legacy_import``.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.routers.chatbot import get_db_session
from backend.app.services import academic_provisioning as ap
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

MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # 2 MB cap

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
    if len(message) > 240:
        return message[:237] + "..."
    return message


def _context_info(session: Session, context_id: int) -> tuple[int | None, int | None]:
    """Return (teaching_assignment_id, class_group_id) for a context."""
    row = session.execute(
        text(
            "SELECT teaching_assignment_id, class_group_id FROM academic_contexts"
            " WHERE id = :cid LIMIT 1"
        ),
        {"cid": context_id},
    ).fetchone()
    return (row[0], row[1]) if row else (None, None)


async def _read_csv(file: UploadFile) -> str:
    raw_bytes = await file.read()
    size_check = check_file_size(len(raw_bytes))
    if not size_check.valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=_safe_detail(size_check.error or "Invalid file"),
        )
    try:
        return raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid CSV encoding; expected UTF-8",
        ) from exc


# ---------------------------------------------------------------------------
# Students upload
# ---------------------------------------------------------------------------


@router.post("/students/upload", response_model=StudentsUploadResponse, status_code=status.HTTP_200_OK)
async def upload_students(
    request: Request,
    file: UploadFile = File(...),
    context_id: str | None = Query(default=None),
) -> StudentsUploadResponse:
    """Parse a students CSV and persist into students + class_enrollments."""
    _validate_upload_file(file)
    context_pk = _coerce_context_id(context_id)
    if context_pk is None:
        raise HTTPException(status_code=400, detail="context_id é obrigatório.")

    text_data = await _read_csv(file)
    parsed = parse_csv(text_data)
    validation = validate_students_csv(parsed.headers, parsed.rows)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=_safe_detail(validation.error or "Invalid CSV"))

    normalised = [normalize_student(row) for row in parsed.rows]
    normalised = [n for n in normalised if n.get("numero_estudante") and n.get("nome")]

    session: Session = get_db_session(request)
    try:
        ta_id, cg_id = _context_info(session, context_pk)
        if ta_id is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")
        for n in normalised:
            sid = ap.ensure_student(
                session, n["numero_estudante"], n["nome"], n.get("whatsapp") or None, cg_id
            )
            ap.enroll_student(session, context_pk, sid)
        session.commit()
    except HTTPException:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.exception("students_upload_failed")
        raise HTTPException(status_code=400, detail=_safe_detail(f"Database error: {exc.__class__.__name__}")) from exc

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


@router.post("/grades/upload", response_model=GradesUploadResponse, status_code=status.HTTP_200_OK)
async def upload_grades(
    request: Request,
    file: UploadFile = File(...),
    context_id: str | None = Query(default=None),
    component_id: str | None = Query(default=None),
) -> GradesUploadResponse:
    """Parse a grades CSV and persist into grade_entries for one component."""
    _validate_upload_file(file)
    context_pk = _coerce_context_id(context_id)
    if context_pk is None:
        raise HTTPException(status_code=400, detail="context_id é obrigatório.")
    if component_id is None or component_id == "":
        raise HTTPException(status_code=400, detail="component_id é obrigatório.")

    text_data = await _read_csv(file)
    parsed = parse_csv(text_data)
    validation = validate_grades_csv(parsed.headers, parsed.rows)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=_safe_detail(validation.error or "Invalid CSV"))

    normalised = [normalize_grade(row) for row in parsed.rows]
    normalised = [n for n in normalised if n.get("numero_estudante") and n.get("nota")]

    session: Session = get_db_session(request)
    try:
        ta_id, cg_id = _context_info(session, context_pk)
        if ta_id is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")
        component_ids = ap.get_component_ids(session, ta_id)
        try:
            idx = int(component_id)
        except (TypeError, ValueError):
            idx = 0
        if not component_ids or idx >= len(component_ids):
            raise HTTPException(status_code=400, detail="Componente de avaliação inválido.")
        ad_id = component_ids[idx]

        user_id = _resolve_user_id(request, session)
        count = 0
        for n in normalised:
            sid = ap.ensure_student(session, n["numero_estudante"], n.get("nome") or "", None, cg_id)
            ap.enroll_student(session, context_pk, sid)
            # numeric coercion: store decimal value
            try:
                value = float(str(n["nota"]).replace(",", "."))
            except (TypeError, ValueError):
                continue
            ap.upsert_grade(session, sid, ta_id, ad_id, value, user_id)
            count += 1
        session.commit()
    except HTTPException:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.exception("grades_upload_failed")
        raise HTTPException(status_code=400, detail=_safe_detail(f"Database error: {exc.__class__.__name__}")) from exc

    return GradesUploadResponse(
        count=count,
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


def _resolve_user_id(request: Request, session: Session) -> int | None:
    """Resolve the acting professor user_id from the Bearer session token."""
    from datetime import UTC, datetime

    auth = request.headers.get("authorization", "")
    sid = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else None
    if not sid:
        return None
    now = datetime.now(UTC).replace(tzinfo=None)
    row = session.execute(
        text(
            "SELECT user_id FROM user_sessions"
            " WHERE id = :sid AND is_active = true AND expires_at > :now LIMIT 1"
        ),
        {"sid": sid, "now": now},
    ).fetchone()
    return int(row[0]) if row else None


__all__: list[Any] = ["router"]
