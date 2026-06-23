"""Router de NOTAS — gere as notas dos alunos de cada contexto académico.

PT: Um "router" agrupa endpoints (URLs) relacionados. Aqui há dois:
  GET   /grades/?context_id={id}   → lista todos os alunos inscritos + as suas notas
  PATCH /grades/{grade_id}         → altera o valor de uma nota
O frontend chama estes endereços. Cada função decorada com @router.get/@router.patch
responde a um deles. As consultas à BD usam SQL com parâmetros (seguro).
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text

LOGGER = logging.getLogger("backend.grades")

# Objecto que recolhe as rotas deste ficheiro; é depois ligado à app no main.py.
router = APIRouter(tags=["grades"])


# ---------------------------------------------------------------------------
# Auxiliar de autenticação
# ---------------------------------------------------------------------------

# Descobre QUEM está a fazer o pedido a partir do cabeçalho "Authorization".
# Devolve o id do professor; se não houver sessão válida, lança erro 401.
def _get_professor_id(request: Request) -> int:
    auth = request.headers.get("authorization", "")
    # O cabeçalho vem como "Bearer <id_sessao>"; removemos o prefixo para ficar só o id.
    session_id = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else None
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado.")
    engine = _get_engine(request)
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


def _get_engine(request: Request):
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        from backend.app.config import get_settings
        from backend.app.database import build_engine
        engine = build_engine(get_settings().database_url)
    return engine


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

# Schemas Pydantic: descrevem o formato exacto dos dados que entram/saem da API.
# O FastAPI usa-os para validar e converter automaticamente para/de JSON.

class GradeValueOut(BaseModel):       # uma nota individual devolvida ao frontend
    gradeId: str
    value: float | None               # pode ser None (nota ainda não lançada)


class StudentRowOut(BaseModel):       # uma linha da pauta: aluno + as suas notas
    studentId: str
    studentNumber: str
    studentName: str
    phone: str | None = None
    components: dict[str, GradeValueOut]  # dicionário {posição: nota}
    published: bool


class GradesListOut(BaseModel):       # resposta do GET /grades/: lista de alunos
    students: list[StudentRowOut]


class GradePatchRequest(BaseModel):   # corpo do PATCH: o novo valor da nota
    value: float | None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

# GET /grades/?context_id=... → devolve a pauta completa (alunos + notas) de um contexto.
@router.get("/grades/", response_model=GradesListOut)
async def get_grades(context_id: int, request: Request) -> GradesListOut:
    prof_id = _get_professor_id(request)   # garante que está autenticado
    engine = _get_engine(request)

    with engine.connect() as conn:
        # Confirma que o contexto existe E pertence a este professor (segurança).
        ctx_row = conn.execute(
            text(
                "SELECT id, teaching_assignment_id FROM academic_contexts"
                " WHERE id = :cid AND professor_id = :pid LIMIT 1"
            ),
            {"cid": context_id, "pid": prof_id},
        ).fetchone()
        if ctx_row is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")
        ta_id = ctx_row[1]

        # Components (assessment_definitions) → position index used by the frontend
        ad_rows = conn.execute(
            text(
                "SELECT id FROM assessment_definitions"
                " WHERE teaching_assignment_id = :ta ORDER BY sort_order, id"
            ),
            {"ta": ta_id},
        ).fetchall() if ta_id else []
        ad_index = {r[0]: i for i, r in enumerate(ad_rows)}
        component_keys = [str(i) for i in range(len(ad_rows))]

        # Enrolled students for this context
        enrolled = conn.execute(
            text(
                "SELECT s.id, s.student_number, s.full_name, s.phone"
                " FROM class_enrollments ce"
                " JOIN students s ON s.id = ce.student_id"
                " WHERE ce.academic_context_id = :cid"
                "   AND (ce.enrollment_status IS NULL OR ce.enrollment_status = 'active')"
                " ORDER BY s.student_number"
            ),
            {"cid": context_id},
        ).fetchall()

        # Percorre cada aluno inscrito e monta a sua linha da pauta.
        student_rows: list[StudentRowOut] = []
        for student_id, student_number, full_name, phone in enrolled:
            # Começa com todas as notas vazias (dict comprehension: uma entrada por componente).
            components: dict[str, GradeValueOut] = {
                key: GradeValueOut(gradeId="", value=None) for key in component_keys
            }
            if ta_id:
                grade_rows = conn.execute(
                    text(
                        "SELECT id, assessment_definition_id, raw_value FROM grade_entries"
                        " WHERE student_id = :sid AND teaching_assignment_id = :ta"
                    ),
                    {"sid": student_id, "ta": ta_id},
                ).fetchall()
                for grade_id, ad_id, raw_value in grade_rows:
                    if ad_id in ad_index:
                        key = str(ad_index[ad_id])
                        components[key] = GradeValueOut(
                            gradeId=str(grade_id),
                            value=float(raw_value) if raw_value is not None else None,
                        )
                pub = conn.execute(
                    text(
                        "SELECT count(*) FROM publication_snapshots"
                        " WHERE student_id = :sid AND teaching_assignment_id = :ta"
                        "   AND is_current = true"
                    ),
                    {"sid": student_id, "ta": ta_id},
                ).fetchone()
                published = bool(pub and pub[0])
            else:
                published = False

            student_rows.append(StudentRowOut(
                studentId=str(student_id),
                studentNumber=student_number or "",
                studentName=full_name or "",
                phone=phone or None,
                components=components,
                published=published,
            ))

        return GradesListOut(students=student_rows)


# PATCH /grades/{grade_id} → altera o valor de uma única nota.
# {grade_id} na URL chega como argumento; `body` é o JSON enviado (validado pelo schema).
@router.patch("/grades/{grade_id}", response_model=GradeValueOut)
async def patch_grade(grade_id: int, body: GradePatchRequest, request: Request) -> GradeValueOut:
    prof_id = _get_professor_id(request)
    engine = _get_engine(request)
    now = datetime.now(UTC).replace(tzinfo=None)

    with engine.connect() as conn:
        # Verifica que a nota pertence mesmo a uma turma deste professor (segurança).
        row = conn.execute(
            text(
                "SELECT ge.id FROM grade_entries ge"
                " JOIN teaching_assignments ta ON ta.id = ge.teaching_assignment_id"
                " JOIN professors p ON p.id = ta.professor_id"
                " WHERE ge.id = :gid AND p.user_id = :uid LIMIT 1"
            ),
            {"gid": grade_id, "uid": prof_id},
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Nota não encontrada.")
        conn.execute(
            text(
                "UPDATE grade_entries SET raw_value = :val, normalized_value = :val,"
                " status = 'validated', updated_at = :now WHERE id = :gid"
            ),
            {"val": body.value, "now": now, "gid": grade_id},
        )
        conn.commit()  # confirma a alteração na BD
        return GradeValueOut(gradeId=str(grade_id), value=body.value)
