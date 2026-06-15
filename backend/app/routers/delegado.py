"""Delegado portal router.

Routes under /api/v1/delegado (matches frontend paths):
  GET /api/v1/delegado/students       — students in delegado's context
  GET /api/v1/delegado/system-status  — system status summary
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text

LOGGER = logging.getLogger("backend.delegado")

router = APIRouter(prefix="/api/v1/delegado", tags=["delegado"])


def _get_user_id(request: Request) -> int:
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


class DelegateStudent(BaseModel):
    id: str
    studentNumber: str
    name: str
    phone: str | None = None


class SystemStatus(BaseModel):
    totalStudents: int
    totalContexts: int
    publishedGrades: int
    activeContexts: int


@router.get("/students", response_model=list[DelegateStudent])
async def get_students(request: Request) -> list[DelegateStudent]:
    user_id = _get_user_id(request)
    engine = _get_engine(request)
    with engine.connect() as conn:
        # Return only students enrolled in contexts where this user is an active delegate
        rows = conn.execute(
            text(
                "SELECT DISTINCT s.id, s.student_number, s.full_name, s.phone"
                " FROM students s"
                " JOIN class_enrollments ce ON ce.student_id = s.id"
                " JOIN delegate_assignments da"
                "   ON CAST(da.context_id AS INTEGER) = ce.academic_context_id"
                " WHERE da.user_id = :uid"
                "   AND da.context_type = 'academic_context'"
                "   AND da.state = 'active'"
                "   AND (ce.enrollment_status IS NULL OR ce.enrollment_status = 'active')"
                " ORDER BY s.student_number LIMIT 100"
            ),
            {"uid": user_id},
        ).fetchall()
        return [
            DelegateStudent(
                id=str(r[0]),
                studentNumber=r[1] or "",
                name=r[2] or "",
                phone=r[3],
            )
            for r in rows
        ]


@router.get("/system-status", response_model=SystemStatus)
async def get_system_status(request: Request) -> SystemStatus:
    _get_user_id(request)
    engine = _get_engine(request)
    with engine.connect() as conn:
        total_students = conn.execute(text("SELECT count(*) FROM students")).fetchone()[0]
        total_contexts = conn.execute(text("SELECT count(*) FROM academic_contexts")).fetchone()[0]
        published_grades = conn.execute(
            text("SELECT count(*) FROM grade_entries WHERE status = 'approved'")
        ).fetchone()[0]
        return SystemStatus(
            totalStudents=total_students,
            totalContexts=total_contexts,
            publishedGrades=published_grades,
            activeContexts=total_contexts,
        )
