"""Router de IMPORTAÇÃO de CSV — carregar pautas de alunos e notas a partir de ficheiros.

PT: Permite ao professor enviar (upload) um ficheiro CSV para o sistema:
  POST /api/v1/students/upload  → cria/actualiza alunos e inscreve-os no contexto
  POST /api/v1/grades/upload    → grava as notas de uma componente de avaliação
O ficheiro é lido, validado e normalizado antes de gravar. Tudo é feito dentro de
uma transação: se algo falhar a meio, faz-se `rollback` e nada fica gravado.

CSV ingest router — students roster and grades upload.

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
from backend.app.services.csv_parsing import (
    check_file_size,
    match_grade_columns,
    normalize_grade,
    normalize_student,
    parse_csv,
    validate_grades_csv,
    validate_students_csv,
)

LOGGER = logging.getLogger("backend.ingest.routes")

router = APIRouter(prefix="/api/v1", tags=["ingest"])

MAX_UPLOAD_BYTES = 2 * 1024 * 1024  # limite de 2 MB por ficheiro

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


class ComponentMatchOut(BaseModel):
    csv_column: str
    component_name: str
    component_index: int
    count: int


class MultiGradesUploadResponse(BaseModel):
    total: int
    components: list[ComponentMatchOut]
    unmatched_columns: list[str]


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


# POST /students/upload → recebe o CSV de alunos (File(...)) e o context_id (na URL).
@router.post("/students/upload", response_model=StudentsUploadResponse, status_code=status.HTTP_200_OK)
async def upload_students(
    request: Request,
    file: UploadFile = File(...),
    context_id: str | None = Query(default=None),
) -> StudentsUploadResponse:
    """Lê um CSV de alunos e grava-os em students + class_enrollments."""
    _validate_upload_file(file)                 # valida tipo e tamanho do ficheiro
    context_pk = _coerce_context_id(context_id)  # converte o context_id para inteiro
    if context_pk is None:
        raise HTTPException(status_code=400, detail="context_id é obrigatório.")

    text_data = await _read_csv(file)            # lê o conteúdo do ficheiro
    parsed = parse_csv(text_data)                # transforma o texto em linhas/colunas
    validation = validate_students_csv(parsed.headers, parsed.rows)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=_safe_detail(validation.error or "Invalid CSV"))

    # Normaliza (uniformiza) cada linha e filtra as que não têm número nem nome.
    normalised = [normalize_student(row) for row in parsed.rows]
    normalised = [n for n in normalised if n.get("numero_estudante") and n.get("nome")]

    session: Session = get_db_session(request)
    try:
        ta_id, cg_id = _context_info(session, context_pk)
        if ta_id is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")
        # Para cada aluno: garante que existe na BD e inscreve-o no contexto.
        for n in normalised:
            sid = ap.ensure_student(
                session, n["numero_estudante"], n["nome"], n.get("whatsapp") or None, cg_id
            )
            ap.enroll_student(session, context_pk, sid)
        session.commit()  # tudo correu bem → grava definitivamente
    except HTTPException:
        session.rollback()  # erro de validação → desfaz tudo
        raise
    except SQLAlchemyError as exc:
        session.rollback()  # erro de BD → desfaz tudo (não fica meio-importado)
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


# POST /grades/upload → importa as notas de UMA componente de avaliação (ex.: P1).
@router.post("/grades/upload", response_model=GradesUploadResponse, status_code=status.HTTP_200_OK)
async def upload_grades(
    request: Request,
    file: UploadFile = File(...),
    context_id: str | None = Query(default=None),
    component_id: str | None = Query(default=None),
) -> GradesUploadResponse:
    """Lê um CSV de notas e grava-as em grade_entries para uma componente."""
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
            # Converte a nota para número decimal; troca a vírgula por ponto
            # (em PT escreve-se "13,5" mas o float usa "13.5"). Se falhar, salta a linha.
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


@router.post("/grades/upload-multi", response_model=MultiGradesUploadResponse, status_code=status.HTTP_200_OK)
async def upload_grades_multi(
    request: Request,
    file: UploadFile = File(...),
    context_id: str | None = Query(default=None),
) -> MultiGradesUploadResponse:
    """Import a CSV with multiple grade columns matched to assessment components."""
    _validate_upload_file(file)
    context_pk = _coerce_context_id(context_id)
    if context_pk is None:
        raise HTTPException(status_code=400, detail="context_id é obrigatório.")

    text_data = await _read_csv(file)
    parsed = parse_csv(text_data)
    validation = validate_grades_csv(parsed.headers, parsed.rows)
    if not validation.valid:
        raise HTTPException(status_code=400, detail=_safe_detail(validation.error or "Invalid CSV"))

    session: Session = get_db_session(request)
    try:
        ta_id, cg_id = _context_info(session, context_pk)
        if ta_id is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")

        component_ids = ap.get_component_ids(session, ta_id)
        component_names_rows = session.execute(
            text(
                "SELECT name FROM assessment_definitions"
                " WHERE teaching_assignment_id = :ta ORDER BY sort_order, id"
            ),
            {"ta": ta_id},
        ).fetchall()
        component_names = [r[0] for r in component_names_rows]

        if not component_ids:
            raise HTTPException(status_code=400, detail="Nenhuma componente de avaliação definida.")

        matches = match_grade_columns(parsed.headers, component_names)
        if not matches:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Nenhuma coluna do CSV corresponde às componentes: "
                    f"{', '.join(component_names)}. "
                    f"Colunas do CSV: {', '.join(parsed.headers)}"
                ),
            )

        from backend.app.services.csv_parsing import _normalize_for_match, NON_GRADE_COLS, IDENTIFIER_COLS, NAME_COLS
        matched_headers = {m.csv_column for m in matches}
        non_grade = {h for h in parsed.headers if _normalize_for_match(h) in {_normalize_for_match(c) for c in NON_GRADE_COLS}}
        unmatched = [h for h in parsed.headers if h not in matched_headers and h not in non_grade]

        user_id = _resolve_user_id(request, session)
        results: list[ComponentMatchOut] = []

        for match in matches:
            ad_id = component_ids[match.component_index]
            count = 0
            for row in parsed.rows:
                student_num = ""
                for col in IDENTIFIER_COLS:
                    if col in row and str(row[col] or "").strip():
                        student_num = str(row[col]).strip()
                        break
                if not student_num:
                    continue

                raw_value = str(row.get(match.csv_column) or "").strip()
                if not raw_value:
                    continue
                try:
                    value = float(raw_value.replace(",", "."))
                except (TypeError, ValueError):
                    continue

                student_name = ""
                for col in NAME_COLS:
                    if col in row and str(row[col] or "").strip():
                        student_name = str(row[col]).strip()
                        break

                sid = ap.ensure_student(session, student_num, student_name, None, cg_id)
                ap.enroll_student(session, context_pk, sid)
                ap.upsert_grade(session, sid, ta_id, ad_id, value, user_id)
                count += 1

            results.append(ComponentMatchOut(
                csv_column=match.csv_column,
                component_name=match.component_name,
                component_index=match.component_index,
                count=count,
            ))

        session.commit()
    except HTTPException:
        session.rollback()
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        LOGGER.exception("multi_grades_upload_failed")
        raise HTTPException(status_code=400, detail=_safe_detail(f"Database error: {exc.__class__.__name__}")) from exc

    return MultiGradesUploadResponse(
        total=sum(r.count for r in results),
        components=results,
        unmatched_columns=unmatched,
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
