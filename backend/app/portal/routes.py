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
    """Extract authenticated student ID from session.

    AC-2: Enforces that student cannot override their own ID.

    Returns the authenticated student_id from the session.
    Raises HTTPException(401) if not authenticated or not a student.

    Note: This is a placeholder. Full implementation requires:
    - Session validation middleware
    - Role checking (must be 'student', not 'professor')
    """
    # Placeholder: Extract from session cookie (sid)
    # In production:
    # 1. Validate session cookie
    # 2. Verify user role is 'student'
    # 3. Return user_id from session
    #
    # For now, raise 401 to force implementation of session layer.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated. Session validation not yet implemented.",
    )


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
        service = PortalService()
        summary = service.get_academic_summary(
            session,
            authenticated_student_id,
            request_id=request_id,
        )
        return {
            "student_id": summary["student_id"],
            "contexts": summary["contexts"],
        }
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


@router.get("/me/calendar", response_model=Calendar, status_code=200)
async def get_calendar(
    request: Request,
    session: Session = Depends(get_db_session),  # noqa: B008
    authenticated_student_id: int = Depends(get_authenticated_student_id),  # noqa: B008
) -> Calendar:
    """Get authenticated student's published calendar events.

    AC-4: Reads ONLY published calendar snapshots (draft excluded).
    AC-2: Uses authenticated student ID.
    AC-5: No internal audit history.

    Returns:
        Calendar with published events.

    Raises:
        HTTPException(401): Not authenticated.
        HTTPException(500): Database error.
    """
    request_id = getattr(request.state, "request_id", None)

    try:
        service = PortalService()
        result = service.get_calendar(
            session,
            authenticated_student_id,
            request_id=request_id,
        )
        return Calendar(**result)
    except Exception as exc:
        LOGGER.exception(
            "get_calendar_failed",
            extra={"request_id": request_id, "student_id": authenticated_student_id},
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch calendar.",
        ) from exc
