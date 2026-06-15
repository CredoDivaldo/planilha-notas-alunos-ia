"""Grades router — student grades per academic context.

Routes (no /api/v1 prefix — matches frontend apiFetch paths):
  GET   /grades/?context_id={id}   — all students + grades for a context
  PATCH /grades/{grade_id}         — update a single grade value
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text

LOGGER = logging.getLogger("backend.grades")

router = APIRouter(tags=["grades"])


# ---------------------------------------------------------------------------
# Auth helper (same pattern as academic_contexts router)
# ---------------------------------------------------------------------------

def _get_professor_id(request: Request) -> int:
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

class GradeValueOut(BaseModel):
    gradeId: str
    value: float | None


class StudentRowOut(BaseModel):
    studentId: str
    studentNumber: str
    studentName: str
    phone: str | None = None
    components: dict[str, GradeValueOut]
    published: bool


class GradesListOut(BaseModel):
    students: list[StudentRowOut]


class GradePatchRequest(BaseModel):
    value: float | None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/grades/", response_model=GradesListOut)
async def get_grades(context_id: int, request: Request) -> GradesListOut:
    prof_id = _get_professor_id(request)
    engine = _get_engine(request)

    with engine.connect() as conn:
        # Verify context belongs to this professor
        ctx_row = conn.execute(
            text(
                "SELECT id, class_group_id, semester_id, shift_id, subject, subject_code"
                " FROM academic_contexts WHERE id = :cid AND professor_id = :pid LIMIT 1"
            ),
            {"cid": context_id, "pid": prof_id},
        ).fetchone()
        if ctx_row is None:
            raise HTTPException(status_code=404, detail="Contexto não encontrado.")

        # Find the teaching assignment for this context
        ta_row = conn.execute(
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
                "cgid": ctx_row[1],
                "semid": ctx_row[2],
                "shid": ctx_row[3],
                "subj": ctx_row[4],
                "code": ctx_row[5] or "",
            },
        ).fetchone()

        # Get assessment definitions (components) for this teaching assignment
        if ta_row:
            ad_rows = conn.execute(
                text(
                    "SELECT id, name, weight FROM assessment_definitions"
                    " WHERE teaching_assignment_id = :ta ORDER BY sort_order, id"
                ),
                {"ta": ta_row[0]},
            ).fetchall()
            assessment_defs = [(str(r[0]), r[1]) for r in ad_rows]
        else:
            assessment_defs = []

        # Get enrolled students for this context
        enrolled_rows = conn.execute(
            text(
                "SELECT ce.student_id, st.student_number, st.full_name, st.phone"
                " FROM class_enrollments ce"
                " JOIN students st ON st.id = ce.student_id"
                " WHERE ce.academic_context_id = :cid"
                "   AND (ce.enrollment_status IS NULL OR ce.enrollment_status = 'active')"
                " ORDER BY st.student_number"
            ),
            {"cid": context_id},
        ).fetchall()

        # Fall back to legacy_students when no class_enrollments exist for this context
        use_legacy = len(enrolled_rows) == 0
        if use_legacy:
            legacy_rows = conn.execute(
                text(
                    "SELECT id, student_number, name, whatsapp"
                    " FROM legacy_students WHERE academic_context_id = :cid"
                    " ORDER BY student_number"
                ),
                {"cid": context_id},
            ).fetchall()
            enrolled_rows = [(r[0], r[1], r[2], r[3]) for r in legacy_rows]

        # Build student rows
        student_rows: list[StudentRowOut] = []
        for student_id, student_number, full_name, phone in enrolled_rows:
            components: dict[str, GradeValueOut] = {}

            # Initialize all components with null
            for ad_id, _ in assessment_defs:
                components[ad_id] = GradeValueOut(gradeId="", value=None)

            # Fill legacy grade value when using legacy path
            grade_rows = []
            if use_legacy:
                lg_rows = conn.execute(
                    text(
                        "SELECT id, subject, value FROM legacy_grades"
                        " WHERE academic_context_id = :cid AND student_number = :sn"
                    ),
                    {"cid": context_id, "sn": student_number},
                ).fetchall()
                if lg_rows and assessment_defs:
                    for i, (lg_id, lg_subject, lg_value) in enumerate(lg_rows):
                        ad_id = assessment_defs[i][0] if i < len(assessment_defs) else str(i)
                        try:
                            components[ad_id] = GradeValueOut(gradeId=str(lg_id), value=float(lg_value))
                        except (TypeError, ValueError):
                            components[ad_id] = GradeValueOut(gradeId=str(lg_id), value=None)
            elif ta_row:
                grade_rows = conn.execute(
                    text(
                        "SELECT id, assessment_definition_id, raw_value, status"
                        " FROM grade_entries"
                        " WHERE student_id = :sid AND teaching_assignment_id = :ta"
                    ),
                    {"sid": student_id, "ta": ta_row[0]},
                ).fetchall()
                for grade_id, ad_id, raw_value, grade_status in grade_rows:
                    ad_id_str = str(ad_id)
                    if ad_id_str in components:
                        components[ad_id_str] = GradeValueOut(
                            gradeId=str(grade_id),
                            value=float(raw_value) if raw_value is not None else None,
                        )

            published = any(gs == "approved" for _, _, _, gs in grade_rows)

            student_rows.append(StudentRowOut(
                studentId=str(student_id),
                studentNumber=student_number or "",
                studentName=full_name or "",
                phone=phone or None,
                components=components,
                published=published,
            ))

        return GradesListOut(students=student_rows)


@router.patch("/grades/{grade_id}", response_model=GradeValueOut)
async def patch_grade(grade_id: int, body: GradePatchRequest, request: Request) -> GradeValueOut:
    prof_id = _get_professor_id(request)
    engine = _get_engine(request)
    now = datetime.now(UTC).replace(tzinfo=None)

    with engine.connect() as conn:
        # Verify the grade belongs to this professor's teaching assignment
        row = conn.execute(
            text(
                "SELECT ge.id FROM grade_entries ge"
                " JOIN teaching_assignments ta ON ta.id = ge.teaching_assignment_id"
                " WHERE ge.id = :gid AND ta.professor_id = :pid LIMIT 1"
            ),
            {"gid": grade_id, "pid": prof_id},
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Nota não encontrada.")
        conn.execute(
            text(
                "UPDATE grade_entries SET raw_value = :val, normalized_value = :val,"
                " updated_at = :now WHERE id = :gid"
            ),
            {"val": body.value, "now": now, "gid": grade_id},
        )
        conn.commit()
        return GradeValueOut(gradeId=str(grade_id), value=body.value)
