"""Portal API routes — read-only endpoints for authenticated students.

Endpoints:
  GET /api/v1/portal/me              — academic summary + contexts
  GET /api/v1/portal/me/grades       — current grades for all contexts
  GET /api/v1/portal/me/grades/{ctx} — grades for specific context
  GET /api/v1/portal/me/calendar     — published calendar events

All routes require valid student session (AC-2 enforcement).
All responses read ONLY from publication snapshots (AC-1).
No draft/internal data is exposed (AC-5).
"""
from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.portal.service import PortalAccessError, PortalService

LOGGER = logging.getLogger("backend.portal.routes")

router = APIRouter(prefix="/api/v1/portal", tags=["student-portal"])


# -----------------------------------------------------------------------
# Response schemas (Pydantic)
# -----------------------------------------------------------------------


class PublishedGrade(BaseModel):
    """Current published grade for a context."""

    model_config = ConfigDict(extra="forbid")

    snapshot_id: int
    snapshot_version: int
    score: float | None = None
    state: str
    formula_version: str | None = None
    published_at: str  # ISO8601


class ContextSummary(BaseModel):
    """Student's enrollment in a teaching assignment."""

    model_config = ConfigDict(extra="forbid")

    context_id: int
    turma: str
    subject: str
    semester_code: str
    semester_name: str
    shift_name: str
    academic_year: int
    enrollment_status: str
    current_grade: PublishedGrade | None = None


class AcademicSummary(BaseModel):
    """Student's complete academic profile."""

    model_config = ConfigDict(extra="forbid")

    student_id: int
    contexts: list[ContextSummary]


class ContextGrades(BaseModel):
    """Grades for a specific context."""

    model_config = ConfigDict(extra="forbid")

    student_id: int
    context_id: int
    turma: str
    subject: str
    current_grade: PublishedGrade | None = None


class CalendarEvent(BaseModel):
    """Published calendar event."""

    model_config = ConfigDict(extra="forbid")

    event_id: int
    event_type: str
    subject: str
    start_date: str  # ISO8601
    end_date: str | None = None
    location: str | None = None
    published_at: str  # ISO8601


class Calendar(BaseModel):
    """Student's published calendar."""

    model_config = ConfigDict(extra="forbid")

    student_id: int
    calendar_events: list[CalendarEvent]


class ErrorResponse(BaseModel):
    """Standard error response."""

    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    request_id: str | None = None


# -----------------------------------------------------------------------
# Dependency injection
# -----------------------------------------------------------------------


def get_db_session(request: Request) -> Generator[Session, None, None]:
    """Get database session from app state."""
    engine = request.app.state.engine
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_authenticated_student_id(request: Request) -> int:
    """Resolve the authenticated student's ``students.id`` from the session.

    Bearer token → user_sessions → users (role must be 'estudante') →
    students (linked by user_id). Raises 401 if not an authenticated student.
    """
    from datetime import UTC, datetime

    auth = request.headers.get("authorization", "")
    session_id = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else None
    if not session_id:
        raise HTTPException(status_code=401, detail="Não autenticado.")

    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        from backend.app.config import get_settings
        from backend.app.database import build_engine
        engine = build_engine(get_settings().database_url)

    now = datetime.now(UTC).replace(tzinfo=None)
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT u.id, u.role FROM user_sessions us"
                " JOIN users u ON u.id = us.user_id"
                " WHERE us.id = :sid AND us.is_active = true AND us.expires_at > :now LIMIT 1"
            ),
            {"sid": session_id, "now": now},
        ).fetchone()
        if row is None:
            raise HTTPException(status_code=401, detail="Sessão expirada.")
        if row[1] != "estudante":
            raise HTTPException(status_code=403, detail="Acesso reservado a estudantes.")
        srow = conn.execute(
            text("SELECT id FROM students WHERE user_id = :uid LIMIT 1"),
            {"uid": row[0]},
        ).fetchone()
        if srow is None:
            raise HTTPException(status_code=404, detail="Perfil de estudante não encontrado.")
        return int(srow[0])


# -----------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------


@router.get("/me", response_model=AcademicSummary, status_code=200)
async def get_academic_summary(
    request: Request,
    session: Session = Depends(get_db_session),  # noqa: B008
    authenticated_student_id: int = Depends(get_authenticated_student_id),  # noqa: B008
) -> AcademicSummary:
    """Get authenticated student's academic summary.

    AC-1: Reads ONLY published snapshots.
    AC-2: Uses authenticated student ID (no override).
    AC-3: Aggregates by context.

    Returns:
        AcademicSummary with all contexts and current grades.

    Raises:
        HTTPException(401): Not authenticated.
        HTTPException(500): Database error.
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        service = PortalService()
        result = service.get_academic_summary(
            session,
            authenticated_student_id,
            request_id=request_id,
        )
        return AcademicSummary(**result)
    except Exception as exc:
        LOGGER.exception(
            "get_academic_summary_failed",
            extra={"request_id": request_id, "student_id": authenticated_student_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch academic summary.",
        ) from exc


@router.get("/me/grades", response_model=dict[str, Any], status_code=200)
async def get_all_grades(
    request: Request,
    session: Session = Depends(get_db_session),  # noqa: B008
    authenticated_student_id: int = Depends(get_authenticated_student_id),  # noqa: B008
) -> dict[str, Any]:
    """Get authenticated student's current grades across all contexts.

    AC-1: Reads ONLY published snapshots.
    AC-2: Uses authenticated student ID.
    AC-3: Aggregates by context.

    Returns:
        {
            "student_id": int,
            "contexts": [ContextGrades, ...]
        }

    Raises:
        HTTPException(401): Not authenticated.
        HTTPException(500): Database error.
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        sid = authenticated_student_id
        snum_row = session.execute(
            text("SELECT student_number FROM students WHERE id = :id LIMIT 1"),
            {"id": sid},
        ).fetchone()
        student_number = snum_row[0] if snum_row else None

        # Current published snapshots for this student
        snaps = session.execute(
            text(
                "SELECT teaching_assignment_id, published_score, published_state"
                " FROM publication_snapshots"
                " WHERE student_id = :sid AND is_current = true"
            ),
            {"sid": sid},
        ).fetchall()

        subjects: list[dict[str, Any]] = []
        for ta_id, score, state in snaps:
            ctx = session.execute(
                text(
                    "SELECT ac.subject, ac.turma, ac.semester_id, sem.name"
                    " FROM academic_contexts ac"
                    " LEFT JOIN semesters sem ON sem.id = ac.semester_id"
                    " WHERE ac.teaching_assignment_id = :ta LIMIT 1"
                ),
                {"ta": ta_id},
            ).fetchone()
            if ctx is None:
                continue
            disciplina, turma, _sem_id, semestre = ctx[0], ctx[1], ctx[2], ctx[3]

            ad_rows = session.execute(
                text(
                    "SELECT id, name, weight FROM assessment_definitions"
                    " WHERE teaching_assignment_id = :ta ORDER BY sort_order, id"
                ),
                {"ta": ta_id},
            ).fetchall()
            grade_rows = session.execute(
                text(
                    "SELECT assessment_definition_id, raw_value FROM grade_entries"
                    " WHERE student_id = :sid AND teaching_assignment_id = :ta"
                ),
                {"sid": sid, "ta": ta_id},
            ).fetchall()
            values = {r[0]: (float(r[1]) if r[1] is not None else None) for r in grade_rows}
            components = [
                {
                    "id": str(i),
                    "name": ad[1] or "",
                    "weight": float(ad[2] or 0),
                    "value": values.get(ad[0]),
                    "published": True,
                }
                for i, ad in enumerate(ad_rows)
            ]
            nota_final = float(score) if score is not None else None
            resultado = (
                "aprovado" if state == "approved"
                else "reprovado" if state == "rejected"
                else None
            )
            subjects.append({
                "disciplina": disciplina or "",
                "semestre": semestre or "",
                "turma": turma or "",
                "components": components,
                "nota_final": nota_final,
                "resultado": resultado,
                "pendente": False,
            })

        first = subjects[0] if subjects else {}
        return {
            "student_number": student_number,
            "turma": first.get("turma"),
            "disciplina": first.get("disciplina"),
            "semestre": first.get("semestre"),
            "turno": None,
            "subjects": subjects,
        }
    except HTTPException:
        raise
    except Exception as exc:
        LOGGER.exception(
            "get_all_grades_failed",
            extra={"request_id": request_id, "student_id": authenticated_student_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch grades.",
        ) from exc


@router.get("/me/grades/{context_id}", response_model=ContextGrades, status_code=200)
async def get_context_grades(
    context_id: int,
    request: Request,
    session: Session = Depends(get_db_session),  # noqa: B008
    authenticated_student_id: int = Depends(get_authenticated_student_id),  # noqa: B008
) -> ContextGrades:
    """Get authenticated student's grades for a specific context.

    AC-1: Reads ONLY published snapshots.
    AC-2: Verifies student is enrolled in the context.
    AC-3: Single-context detail view.

    Parameters:
        context_id: Teaching assignment / academic context.

    Returns:
        ContextGrades with current snapshot.

    Raises:
        HTTPException(401): Not authenticated.
        HTTPException(403): Student not enrolled in context.
        HTTPException(404): Context not found.
        HTTPException(500): Database error.
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        service = PortalService()
        result = service.get_grades_by_context(
            session,
            authenticated_student_id,
            context_id,
            request_id=request_id,
        )
        return ContextGrades(**result)
    except PortalAccessError as exc:
        LOGGER.warning(
            "portal_access_denied",
            extra={
                "request_id": request_id,
                "student_id": authenticated_student_id,
                "context_id": context_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to the requested context is not permitted.",
        ) from exc
    except Exception as exc:
        LOGGER.exception(
            "get_context_grades_failed",
            extra={
                "request_id": request_id,
                "student_id": authenticated_student_id,
                "context_id": context_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch context grades.",
        ) from exc


@router.get("/me/calendar", response_model=dict[str, Any], status_code=200)
async def get_calendar(
    request: Request,
    session: Session = Depends(get_db_session),  # noqa: B008
    authenticated_student_id: int = Depends(get_authenticated_student_id),  # noqa: B008
) -> dict[str, Any]:
    """Get the authenticated student's published calendar events.

    Reads published ``calendar_events`` scoped to the contexts the student is
    enrolled in (plus context-less/global events). Returns the shape the
    student PortalPage expects: ``{events: [{id, date, time, type, title, location}]}``.
    """
    request_id = getattr(request.state, "request_id", None)
    try:
        sid = authenticated_student_id
        ctx_rows = session.execute(
            text("SELECT academic_context_id FROM class_enrollments WHERE student_id = :sid"),
            {"sid": sid},
        ).fetchall()
        ctx_ids = [str(r[0]) for r in ctx_rows if r[0] is not None]

        if ctx_ids:
            rows = session.execute(
                text(
                    "SELECT id, title, starts_at, ends_at, event_type, location, context_id"
                    " FROM calendar_events"
                    " WHERE internal_status = 'published'"
                    "   AND (context_id IN :ids OR context_id IS NULL OR context_id = '')"
                    " ORDER BY starts_at"
                ).bindparams(bindparam("ids", expanding=True)),
                {"ids": ctx_ids},
            ).fetchall()
        else:
            rows = session.execute(
                text(
                    "SELECT id, title, starts_at, ends_at, event_type, location, context_id"
                    " FROM calendar_events"
                    " WHERE internal_status = 'published' AND (context_id IS NULL OR context_id = '')"
                    " ORDER BY starts_at"
                )
            ).fetchall()

        events: list[dict[str, Any]] = []
        for r in rows:
            starts = r[2]
            if hasattr(starts, "strftime"):
                date_str = starts.strftime("%Y-%m-%d")
                time_str = starts.strftime("%H:%M")
            else:
                s = str(starts or "")
                date_str = s[:10]
                time_str = s[11:16] if len(s) >= 16 else None
            events.append({
                "id": str(r[0]),
                "title": r[1] or "",
                "date": date_str,
                "time": time_str,
                "type": r[4] or "evento",
                "location": r[5],
            })
        return {"events": events}
    except Exception as exc:
        LOGGER.exception(
            "get_calendar_failed",
            extra={"request_id": request_id, "student_id": authenticated_student_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch calendar.",
        ) from exc
