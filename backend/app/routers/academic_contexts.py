"""Academic contexts router — CRUD for professor's teaching contexts.

Routes (no /api/v1 prefix — matches frontend apiFetch paths):
  GET    /academic-contexts/           — list contexts for logged-in professor
  GET    /academic-contexts/{id}       — single context with components
  POST   /academic-contexts/           — create new context
  PUT    /academic-contexts/{id}       — update context
  DELETE /academic-contexts/{id}       — delete context
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text

LOGGER = logging.getLogger("backend.academic_contexts")

router = APIRouter(tags=["academic-contexts"])


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _get_professor_id(request: Request) -> int:
    """Extract professor user_id from Bearer token via user_sessions."""
    auth = request.headers.get("authorization", "")
    session_id = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else None
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado.")
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        from backend.app.config import get_settings
        from backend.app.database import build_engine
        engine = build_engine(get_settings().database_url)
    now = datetime.now(UTC).replace(tzinfo=None)
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT user_id FROM user_sessions"
                " WHERE id = :sid AND is_active = true AND expires_at > :now LIMIT 1"
            ),
            {"sid": session_id, "now": now},
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada.")
    return int(row[0])


def _get_conn(request: Request):
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        from backend.app.config import get_settings
        from backend.app.database import build_engine
        engine = build_engine(get_settings().database_url)
    return engine.connect()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class GradeComponentOut(BaseModel):
    id: str
    name: str
    weight: float


class DelegadoOut(BaseModel):
    id: str
    name: str
    studentNumber: str


class ContextItemOut(BaseModel):
    id: str
    turma: str
    disciplina: str
    semestre: str
    turno: str
    alunosCount: int
    delegado: DelegadoOut | None
    components: list[GradeComponentOut]


class ContextCreateRequest(BaseModel):
    turma: str
    disciplina: str
    semestre_id: int | None = None
    turno_id: int | None = None
    academic_year: str | None = None


class ContextUpdateRequest(BaseModel):
    turma: str | None = None
    disciplina: str | None = None
    semestre_id: int | None = None
    turno_id: int | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_default_ids(conn: Any, sem_id_hint: int | None, shift_id_hint: int | None) -> tuple[int, int]:
    """Return valid (semester_id, shift_id), creating stub records if the DB is empty."""
    now = datetime.now(UTC).replace(tzinfo=None)

    if sem_id_hint:
        sem_id = sem_id_hint
    else:
        row = conn.execute(text("SELECT id FROM semesters ORDER BY id LIMIT 1")).fetchone()
        if row:
            sem_id = row[0]
        else:
            r = conn.execute(
                text(
                    "INSERT INTO semesters (code, name, is_active, status, created_at, updated_at)"
                    " VALUES ('2026', '2026', true, 'active', :now, :now) RETURNING id"
                ),
                {"now": now},
            )
            sem_id = r.scalar_one()

    if shift_id_hint:
        shift_id = shift_id_hint
    else:
        row = conn.execute(text("SELECT id FROM shifts ORDER BY id LIMIT 1")).fetchone()
        if row:
            shift_id = row[0]
        else:
            r = conn.execute(
                text(
                    "INSERT INTO shifts (code, name, status, created_at, updated_at)"
                    " VALUES ('DIURNO', 'Diurno', 'active', :now, :now) RETURNING id"
                ),
                {"now": now},
            )
            shift_id = r.scalar_one()

    return sem_id, shift_id


def _build_context_item(conn: Any, row: Any, prof_id: int) -> ContextItemOut:
    ctx_id = row[0]

    # Semester name
    sem_row = conn.execute(
        text("SELECT name FROM semesters WHERE id = :id LIMIT 1"),
        {"id": row[3]},
    ).fetchone()
    semestre = sem_row[0] if sem_row else str(row[3])

    # Shift name
    shift_row = conn.execute(
        text("SELECT name FROM shifts WHERE id = :id LIMIT 1"),
        {"id": row[8]},
    ).fetchone()
    turno = shift_row[0] if shift_row else str(row[8])

    # Enrolled students count
    count_row = conn.execute(
        text(
            "SELECT count(*) FROM class_enrollments"
            " WHERE academic_context_id = :cid"
            " AND (enrollment_status IS NULL OR enrollment_status = 'active')"
        ),
        {"cid": ctx_id},
    ).fetchone()
    alunos_count = count_row[0] if count_row else 0

    # Assessment definitions (components) via teaching assignment
    ta_rows = conn.execute(
        text(
            "SELECT ta.id FROM teaching_assignments ta"
            " JOIN subjects s ON s.id = ta.subject_id"
            " WHERE ta.professor_id = :pid"
            "   AND ta.class_group_id = :cgid"
            "   AND ta.semester_id = :semid"
            "   AND ta.shift_id = :shid"
            "   AND (s.name = :subj OR s.code = :code)"
            " LIMIT 1"
        ),
        {
            "pid": prof_id,
            "cgid": row[4],
            "semid": row[3],
            "shid": row[8],
            "subj": row[5],
            "code": row[6] if row[6] else "",
        },
    ).fetchone()

    components: list[GradeComponentOut] = []
    if ta_rows:
        ad_rows = conn.execute(
            text(
                "SELECT id, name, weight FROM assessment_definitions"
                " WHERE teaching_assignment_id = :ta ORDER BY sort_order, id"
            ),
            {"ta": ta_rows[0]},
        ).fetchall()
        components = [
            GradeComponentOut(id=str(r[0]), name=r[1] or "", weight=float(r[2] or 1))
            for r in ad_rows
        ]

    # Delegado (if any active delegate assignment for this context)
    delg_row = conn.execute(
        text(
            "SELECT da.id, u.display_name, st.student_number"
            " FROM delegate_assignments da"
            " JOIN users u ON u.id = da.user_id"
            " LEFT JOIN students st ON st.user_id = da.user_id"
            " WHERE da.context_type = 'academic_context'"
            "   AND da.context_id = :ctx_id"
            "   AND da.state = 'active'"
            " LIMIT 1"
        ),
        {"ctx_id": str(ctx_id)},
    ).fetchone()
    delegado = None
    if delg_row:
        delegado = DelegadoOut(
            id=str(delg_row[0]),
            name=delg_row[1] or "",
            studentNumber=delg_row[2] or "",
        )

    return ContextItemOut(
        id=str(ctx_id),
        turma=row[7] or "",
        disciplina=row[5] or "",
        semestre=semestre,
        turno=turno,
        alunosCount=alunos_count,
        delegado=delegado,
        components=components,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/academic-contexts/", response_model=list[ContextItemOut])
async def list_contexts(request: Request) -> list[ContextItemOut]:
    prof_id = _get_professor_id(request)
    with _get_conn(request) as conn:
        rows = conn.execute(
            text(
                "SELECT id, professor_id, academic_year, semester_id, class_group_id,"
                "       subject, subject_code, turma, shift_id, created_at, updated_at"
                " FROM academic_contexts WHERE professor_id = :pid ORDER BY id"
            ),
            {"pid": prof_id},
        ).fetchall()
        return [_build_context_item(conn, r, prof_id) for r in rows]


@router.get("/academic-contexts/{context_id}", response_model=ContextItemOut)
async def get_context(context_id: int, request: Request) -> ContextItemOut:
    prof_id = _get_professor_id(request)
    with _get_conn(request) as conn:
        row = conn.execute(
            text(
                "SELECT id, professor_id, academic_year, semester_id, class_group_id,"
                "       subject, subject_code, turma, shift_id, created_at, updated_at"
                " FROM academic_contexts WHERE id = :cid AND professor_id = :pid LIMIT 1"
            ),
            {"cid": context_id, "pid": prof_id},
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")
        return _build_context_item(conn, row, prof_id)


@router.post("/academic-contexts/", status_code=status.HTTP_201_CREATED, response_model=ContextItemOut)
async def create_context(body: ContextCreateRequest, request: Request) -> ContextItemOut:
    prof_id = _get_professor_id(request)
    now = datetime.now(UTC).replace(tzinfo=None)
    try:
        academic_year = int(body.academic_year) if body.academic_year else datetime.now(UTC).year
    except (ValueError, TypeError):
        academic_year = datetime.now(UTC).year
    try:
        with _get_conn(request) as conn:
            sem_id, shift_id = _get_or_create_default_ids(conn, body.semestre_id, body.turno_id)
            result = conn.execute(
                text(
                    "INSERT INTO academic_contexts"
                    " (professor_id, academic_year, semester_id, subject,"
                    "  turma, shift_id, created_at, updated_at)"
                    " VALUES (:pid, :ay, :semid, :subj, :turma, :shid, :now, :now)"
                    " RETURNING id"
                ),
                {
                    "pid": prof_id,
                    "ay": academic_year,
                    "semid": sem_id,
                    "subj": body.disciplina,
                    "turma": body.turma,
                    "shid": shift_id,
                    "now": now,
                },
            )
            new_id = result.scalar_one()
            conn.commit()
            row = conn.execute(
                text(
                    "SELECT id, professor_id, academic_year, semester_id, class_group_id,"
                    "       subject, subject_code, turma, shift_id, created_at, updated_at"
                    " FROM academic_contexts WHERE id = :id"
                ),
                {"id": new_id},
            ).fetchone()
            if row is None:
                raise HTTPException(status_code=500, detail=f"Contexto criado (id={new_id}) mas não encontrado na BD")
            return _build_context_item(conn, row, prof_id)
    except HTTPException:
        raise
    except Exception as exc:
        # Duplicate context → return the existing one
        exc_str = str(exc)
        if "UniqueViolation" in exc_str or "unique constraint" in exc_str.lower():
            try:
                with _get_conn(request) as conn:
                    row = conn.execute(
                        text(
                            "SELECT id, professor_id, academic_year, semester_id, class_group_id,"
                            "       subject, subject_code, turma, shift_id, created_at, updated_at"
                            " FROM academic_contexts"
                            " WHERE professor_id = :pid AND turma = :turma AND subject = :subj"
                            " ORDER BY id LIMIT 1"
                        ),
                        {"pid": prof_id, "turma": body.turma, "subj": body.disciplina},
                    ).fetchone()
                    if row:
                        return _build_context_item(conn, row, prof_id)
            except Exception:
                pass
        LOGGER.exception("create_context_failed")
        raise HTTPException(status_code=500, detail=f"Erro ao criar contexto: {exc}") from exc


@router.put("/academic-contexts/{context_id}", response_model=ContextItemOut)
async def update_context(context_id: int, body: ContextUpdateRequest, request: Request) -> ContextItemOut:
    prof_id = _get_professor_id(request)
    with _get_conn(request) as conn:
        row = conn.execute(
            text(
                "SELECT id, professor_id, academic_year, semester_id, class_group_id,"
                "       subject, subject_code, turma, shift_id, created_at, updated_at"
                " FROM academic_contexts WHERE id = :cid AND professor_id = :pid LIMIT 1"
            ),
            {"cid": context_id, "pid": prof_id},
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")
        updates: dict[str, Any] = {"now": datetime.now(UTC).replace(tzinfo=None).isoformat(), "cid": context_id}
        set_clauses = ["updated_at = :now"]
        if body.turma is not None:
            updates["turma"] = body.turma
            set_clauses.append("turma = :turma")
        if body.disciplina is not None:
            updates["subject"] = body.disciplina
            set_clauses.append("subject = :subject")
        if body.semestre_id is not None:
            updates["semid"] = body.semestre_id
            set_clauses.append("semester_id = :semid")
        if body.turno_id is not None:
            updates["shid"] = body.turno_id
            set_clauses.append("shift_id = :shid")
        updates["pid"] = prof_id
        conn.execute(
            text(f"UPDATE academic_contexts SET {', '.join(set_clauses)} WHERE id = :cid AND professor_id = :pid"),
            updates,
        )
        conn.commit()
        updated = conn.execute(
            text(
                "SELECT id, professor_id, academic_year, semester_id, class_group_id,"
                "       subject, subject_code, turma, shift_id, created_at, updated_at"
                " FROM academic_contexts WHERE id = :cid"
            ),
            {"cid": context_id},
        ).fetchone()
        return _build_context_item(conn, updated, prof_id)


@router.delete("/academic-contexts/{context_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_context(context_id: int, request: Request) -> None:
    prof_id = _get_professor_id(request)
    with _get_conn(request) as conn:
        row = conn.execute(
            text("SELECT id FROM academic_contexts WHERE id = :cid AND professor_id = :pid LIMIT 1"),
            {"cid": context_id, "pid": prof_id},
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")
        conn.execute(
            text("DELETE FROM class_enrollments WHERE academic_context_id = :cid"),
            {"cid": context_id},
        )
        conn.execute(
            text("DELETE FROM academic_contexts WHERE id = :cid"),
            {"cid": context_id},
        )
        conn.commit()
