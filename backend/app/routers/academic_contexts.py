"""Router dos CONTEXTOS ACADÉMICOS — CRUD das "turmas/disciplinas" do professor.

PT: Um contexto = uma disciplina que o professor dá a uma turma, num semestre/turno.
Aqui estão os 5 endpoints do CRUD (listar, ver, criar, editar, apagar). Criar um
contexto também "provisiona" automaticamente as entidades relacionadas (professor,
disciplina, turma, componentes de avaliação) — ver `_provision_context`.

Academic contexts router — CRUD for professor's teaching contexts.

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

from backend.app.services import academic_provisioning as ap

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


class ComponentIn(BaseModel):
    name: str
    weight: float


class ContextCreateRequest(BaseModel):
    turma: str
    disciplina: str
    semestre_id: int | None = None
    turno_id: int | None = None
    academic_year: str | None = None
    # Frontend sends string labels; accepted alongside ids
    semestre: str | None = None
    turno: str | None = None
    components: list[ComponentIn] = []


class ContextUpdateRequest(BaseModel):
    turma: str | None = None
    disciplina: str | None = None
    semestre_id: int | None = None
    turno_id: int | None = None
    semestre: str | None = None
    turno: str | None = None
    components: list[ComponentIn] | None = None


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


# "Provisionar" = garantir que existem todas as entidades de que o contexto depende.
# Cria-as se faltarem e devolve os ids da atribuição de ensino e da turma.
def _provision_context(
    conn: Any,
    user_id: int,
    disciplina: str,
    turma: str,
    sem_id: int,
    shift_id: int,
    components: list,
) -> tuple[int, int]:
    """Cria/garante as entidades relacionadas de um contexto. Devolve (ta_id, class_group_id)."""
    urow = conn.execute(
        text("SELECT display_name, username FROM users WHERE id = :id LIMIT 1"),
        {"id": user_id},
    ).fetchone()
    pname = (urow[0] or urow[1]) if urow else "Professor"
    prof_pk = ap.ensure_professor(conn, user_id, pname)
    subject_id = ap.ensure_subject(conn, disciplina)
    cg_id = ap.ensure_class_group(conn, turma)
    ta_id = ap.ensure_teaching_assignment(conn, prof_pk, subject_id, cg_id, sem_id, shift_id)
    ap.sync_components(
        conn, ta_id, [{"name": c.name, "weight": c.weight} for c in components]
    )
    return ta_id, cg_id


def _current_components(conn: Any, ta_id: int | None) -> list["ComponentIn"]:
    """Read existing components from assessment_definitions as ComponentIn list."""
    if not ta_id:
        return []
    rows = conn.execute(
        text(
            "SELECT name, weight FROM assessment_definitions"
            " WHERE teaching_assignment_id = :ta ORDER BY sort_order, id"
        ),
        {"ta": ta_id},
    ).fetchall()
    return [ComponentIn(name=r[0] or "", weight=float(r[1] or 0)) for r in rows]


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

    # Enrolled students count (normalized: class_enrollments)
    count_row = conn.execute(
        text(
            "SELECT count(*) FROM class_enrollments"
            " WHERE academic_context_id = :cid"
            " AND (enrollment_status IS NULL OR enrollment_status = 'active')"
        ),
        {"cid": ctx_id},
    ).fetchone()
    alunos_count = count_row[0] if count_row else 0

    # Components: read from assessment_definitions via teaching_assignment_id (col 11)
    components: list[GradeComponentOut] = []
    ta_id = row[11] if len(row) > 11 else None
    if ta_id:
        ad_rows = conn.execute(
            text(
                "SELECT name, weight FROM assessment_definitions"
                " WHERE teaching_assignment_id = :ta ORDER BY sort_order, id"
            ),
            {"ta": ta_id},
        ).fetchall()
        components = [
            GradeComponentOut(id=str(i), name=r[0] or "", weight=float(r[1] or 0))
            for i, r in enumerate(ad_rows)
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

# LER lista (GET): devolve todos os contextos do professor autenticado.
@router.get("/academic-contexts/", response_model=list[ContextItemOut])
async def list_contexts(request: Request) -> list[ContextItemOut]:
    prof_id = _get_professor_id(request)
    with _get_conn(request) as conn:
        rows = conn.execute(
            text(
                "SELECT id, professor_id, academic_year, semester_id, class_group_id,"
                "       subject, subject_code, turma, shift_id, created_at, updated_at, teaching_assignment_id"
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
                "       subject, subject_code, turma, shift_id, created_at, updated_at, teaching_assignment_id"
                " FROM academic_contexts WHERE id = :cid AND professor_id = :pid LIMIT 1"
            ),
            {"cid": context_id, "pid": prof_id},
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")
        return _build_context_item(conn, row, prof_id)


# CRIAR (POST): provisiona as entidades e insere o novo contexto.
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
            # Provision normalized entities (professor/subject/class_group/TA/components)
            ta_id, cg_id = _provision_context(
                conn, prof_id, body.disciplina, body.turma, sem_id, shift_id, body.components
            )
            result = conn.execute(
                text(
                    "INSERT INTO academic_contexts"
                    " (professor_id, academic_year, semester_id, subject, class_group_id,"
                    "  turma, shift_id, teaching_assignment_id, created_at, updated_at)"
                    " VALUES (:pid, :ay, :semid, :subj, :cgid, :turma, :shid, :taid, :now, :now)"
                    " RETURNING id"
                ),
                {
                    "pid": prof_id,
                    "ay": academic_year,
                    "semid": sem_id,
                    "subj": body.disciplina,
                    "cgid": cg_id,
                    "turma": body.turma,
                    "shid": shift_id,
                    "taid": ta_id,
                    "now": now,
                },
            )
            new_id = result.scalar_one()
            conn.commit()
            row = conn.execute(
                text(
                    "SELECT id, professor_id, academic_year, semester_id, class_group_id,"
                    "       subject, subject_code, turma, shift_id, created_at, updated_at, teaching_assignment_id"
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
                            "       subject, subject_code, turma, shift_id, created_at, updated_at, teaching_assignment_id"
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
        # Current values (row indices: 3=semester_id, 5=subject, 7=turma, 8=shift_id, 11=ta_id)
        new_disciplina = body.disciplina if body.disciplina is not None else row[5]
        new_turma = body.turma if body.turma is not None else row[7]
        new_sem = body.semestre_id if body.semestre_id is not None else row[3]
        new_shift = body.turno_id if body.turno_id is not None else row[8]

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

        # Re-provision normalized entities when teaching shape or components change
        reprovision = (
            body.disciplina is not None or body.turma is not None
            or body.semestre_id is not None or body.turno_id is not None
            or body.components is not None
        )
        if reprovision:
            components = body.components if body.components is not None else _current_components(conn, row[11])
            ta_id, cg_id = _provision_context(
                conn, prof_id, new_disciplina, new_turma, new_sem, new_shift, components
            )
            updates["taid"] = ta_id
            set_clauses.append("teaching_assignment_id = :taid")
            updates["cgid"] = cg_id
            set_clauses.append("class_group_id = :cgid")

        updates["pid"] = prof_id
        conn.execute(
            text(f"UPDATE academic_contexts SET {', '.join(set_clauses)} WHERE id = :cid AND professor_id = :pid"),
            updates,
        )
        conn.commit()
        updated = conn.execute(
            text(
                "SELECT id, professor_id, academic_year, semester_id, class_group_id,"
                "       subject, subject_code, turma, shift_id, created_at, updated_at, teaching_assignment_id"
                " FROM academic_contexts WHERE id = :cid"
            ),
            {"cid": context_id},
        ).fetchone()
        return _build_context_item(conn, updated, prof_id)


# APAGAR (DELETE): remove o contexto E tudo o que depende dele (notas, componentes,
# inscrições, atribuição de ensino) — apaga "em cascata" para não deixar lixo na BD.
@router.delete("/academic-contexts/{context_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_context(context_id: int, request: Request) -> None:
    prof_id = _get_professor_id(request)
    with _get_conn(request) as conn:
        row = conn.execute(
            text(
                "SELECT id, teaching_assignment_id FROM academic_contexts"
                " WHERE id = :cid AND professor_id = :pid LIMIT 1"
            ),
            {"cid": context_id, "pid": prof_id},
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")
        ta_id = row[1]
        # Remove dependent normalized rows scoped to this context's teaching assignment
        if ta_id:
            conn.execute(
                text("DELETE FROM grade_entries WHERE teaching_assignment_id = :ta"),
                {"ta": ta_id},
            )
            conn.execute(
                text("DELETE FROM assessment_definitions WHERE teaching_assignment_id = :ta"),
                {"ta": ta_id},
            )
        conn.execute(
            text("DELETE FROM class_enrollments WHERE academic_context_id = :cid"),
            {"cid": context_id},
        )
        conn.execute(
            text("DELETE FROM academic_contexts WHERE id = :cid"),
            {"cid": context_id},
        )
        if ta_id:
            conn.execute(
                text("DELETE FROM teaching_assignments WHERE id = :ta"),
                {"ta": ta_id},
            )
        conn.commit()
