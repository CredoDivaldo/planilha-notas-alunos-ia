"""Portal Service — read-only view of student's published academic data.

AC-1: Portal reads ONLY publication_snapshots WHERE is_current=True.
AC-2: Authenticated student identity scopes all queries.
AC-3: Academic summary aggregates by teaching_assignment (discipline/context).
AC-4: Calendar from published_calendar_snapshots only.
AC-5: No internal history, audit logs, or draft payloads exposed.
AC-6: Display formula metadata without recalculation.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.academic import AuditLog
from backend.app.models.contexts import AcademicContext, ClassEnrollment, Semester, Shift
from backend.app.models.publication import PublicationSnapshot, PublishedCalendarSnapshot

LOGGER = logging.getLogger("backend.portal.service")

# Audit action constant
ACTION_PORTAL_READ = "portal_read"


class PortalService:
    """Orchestrates read-only access to student's published academic data.

    All methods require:
    - session: Active SQLAlchemy session
    - authenticated_student_id: From session validation (never user-supplied)

    No portal query shall ever:
    - Read grade_entries or calculation_results
    - Expose previous snapshots (only is_current=True)
    - Return internal audit history or calculation payloads
    - Recalculate grades or formulas
    """

    def get_academic_summary(
        self,
        session: Session,
        authenticated_student_id: int,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Fetch student's academic summary: enrollments, contexts, current grades.

        AC-1: Reads ONLY publication_snapshots WHERE is_current=True.
        AC-2: Scope enforced by authenticated_student_id (ignores external override).
        AC-3: Aggregates by context (teaching_assignment).

        Returns:
        {
            "student_id": int,
            "contexts": [
                {
                    "context_id": int,
                    "turma": str,
                    "subject": str,
                    "semester_code": str,
                    "semester_name": str,
                    "shift_name": str,
                    "academic_year": int,
                    "enrollment_status": str,
                    "current_grade": PublishedGrade
                }
            ]
        }
        """
        # Query: student's current enrollments + contexts + latest snapshots
        # Note: AcademicContext.id is used as teaching_assignment_id in PublicationSnapshot
        stmt = select(
            ClassEnrollment.student_id,
            ClassEnrollment.enrollment_status,
            ClassEnrollment.academic_context_id,
            AcademicContext.id.label("context_id"),
            AcademicContext.turma,
            AcademicContext.subject,
            AcademicContext.academic_year,
            Semester.code.label("semester_code"),
            Semester.name.label("semester_name"),
            Shift.name.label("shift_name"),
            PublicationSnapshot.id.label("snapshot_id"),
            PublicationSnapshot.snapshot_version,
            PublicationSnapshot.published_score,
            PublicationSnapshot.published_state,
            PublicationSnapshot.published_payload_json,
            PublicationSnapshot.published_at,
        ).select_from(ClassEnrollment).join(
            AcademicContext,
            ClassEnrollment.academic_context_id == AcademicContext.id,
        ).join(
            Semester,
            AcademicContext.semester_id == Semester.id,
        ).join(
            Shift,
            AcademicContext.shift_id == Shift.id,
        ).outerjoin(
            PublicationSnapshot,
            (PublicationSnapshot.student_id == ClassEnrollment.student_id)
            & (PublicationSnapshot.teaching_assignment_id == AcademicContext.id)
            & (PublicationSnapshot.is_current == True),  # noqa: E712
        ).where(
            ClassEnrollment.student_id == authenticated_student_id
        ).order_by(
            AcademicContext.academic_year.desc(),
            Semester.code.desc(),
            AcademicContext.subject.asc(),
        )

        rows = session.execute(stmt).fetchall()

        # Log portal access (AC-8: audit trail)
        self._log_portal_access(
            session,
            action=ACTION_PORTAL_READ,
            entity_type="student_academic_summary",
            student_id=authenticated_student_id,
            request_id=request_id,
            result_count=len(rows),
        )

        if not rows:
            return {"student_id": authenticated_student_id, "contexts": []}

        # Aggregate by context
        contexts_by_id: dict[int, dict[str, Any]] = {}
        for row in rows:
            ctx_id = row.context_id
            if ctx_id not in contexts_by_id:
                contexts_by_id[ctx_id] = {
                    "context_id": ctx_id,
                    "turma": row.turma,
                    "subject": row.subject,
                    "semester_code": row.semester_code,
                    "semester_name": row.semester_name,
                    "shift_name": row.shift_name,
                    "academic_year": row.academic_year,
                    "enrollment_status": row.enrollment_status,
                    "current_grade": None,
                }

            # Populate current grade if snapshot exists (AC-6: render as-is)
            if row.snapshot_id:
                try:
                    payload = json.loads(row.published_payload_json) if row.published_payload_json else {}
                except json.JSONDecodeError:
                    LOGGER.warning(
                        "malformed_payload_json",
                        extra={"snapshot_id": row.snapshot_id, "request_id": request_id},
                    )
                    payload = {}
                contexts_by_id[ctx_id]["current_grade"] = {
                    "snapshot_id": row.snapshot_id,
                    "snapshot_version": row.snapshot_version,
                    "score": float(row.published_score) if row.published_score else None,
                    "state": row.published_state,
                    "formula_version": payload.get("formula_version"),
                    "published_at": row.published_at.isoformat() if row.published_at else None,
                }

        return {
            "student_id": authenticated_student_id,
            "contexts": list(contexts_by_id.values()),
        }

    def get_grades_by_context(
        self,
        session: Session,
        authenticated_student_id: int,
        context_id: int,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Fetch student's current grades for a specific context.

        AC-1: Reads ONLY is_current=True snapshots.
        AC-2: Scope enforced; rejects mismatched student.
        AC-3: Single context detail with all published snapshots.

        Parameters
        ----------
        session:
            SQLAlchemy session.
        authenticated_student_id:
            From session validation.
        context_id:
            Teaching assignment / academic context.
        request_id:
            Optional correlation ID.

        Returns:
        {
            "student_id": int,
            "context_id": int,
            "turma": str,
            "subject": str,
            "current_grade": PublishedGrade,
            "snapshot_version": int,
            "formula_version": str,
            "published_at": ISO8601
        }

        Raises:
        - PortalAccessError if student not enrolled in context.
        """
        # Verify student is enrolled in this context
        enrollment = session.query(ClassEnrollment).filter_by(
            academic_context_id=context_id,
            student_id=authenticated_student_id,
        ).first()

        if not enrollment:
            LOGGER.warning(
                "portal_unauthorized_context_access",
                extra={
                    "student_id": authenticated_student_id,
                    "context_id": context_id,
                    "request_id": request_id,
                },
            )
            raise PortalAccessError(
                f"Student {authenticated_student_id} not enrolled in context {context_id}"
            )

        # Fetch context metadata and current snapshot
        stmt = select(
            AcademicContext.turma,
            AcademicContext.subject,
            PublicationSnapshot.id.label("snapshot_id"),
            PublicationSnapshot.snapshot_version,
            PublicationSnapshot.published_score,
            PublicationSnapshot.published_state,
            PublicationSnapshot.published_payload_json,
            PublicationSnapshot.published_at,
        ).select_from(AcademicContext).outerjoin(
            PublicationSnapshot,
            (PublicationSnapshot.student_id == authenticated_student_id)
            & (PublicationSnapshot.teaching_assignment_id == context_id)
            & (PublicationSnapshot.is_current == True),  # noqa: E712
        ).where(
            AcademicContext.id == context_id
        )

        row = session.execute(stmt).first()
        if not row:
            raise PortalAccessError(f"Context {context_id} not found")

        # Log access
        self._log_portal_access(
            session,
            action=ACTION_PORTAL_READ,
            entity_type="context_grades",
            student_id=authenticated_student_id,
            request_id=request_id,
            context_id=context_id,
            result_count=1 if row.snapshot_id else 0,
        )

        result: dict[str, Any] = {
            "student_id": authenticated_student_id,
            "context_id": context_id,
            "turma": row.turma,
            "subject": row.subject,
            "current_grade": None,
        }

        if row.snapshot_id:
            try:
                payload = json.loads(row.published_payload_json) if row.published_payload_json else {}
            except json.JSONDecodeError:
                LOGGER.warning(
                    "malformed_payload_json",
                    extra={"snapshot_id": row.snapshot_id, "request_id": request_id},
                )
                payload = {}
            result["current_grade"] = {
                "snapshot_id": row.snapshot_id,
                "snapshot_version": row.snapshot_version,
                "score": float(row.published_score) if row.published_score else None,
                "state": row.published_state,
                "formula_version": payload.get("formula_version"),
                "published_at": row.published_at.isoformat() if row.published_at else None,
            }

        return result

    def get_calendar(
        self,
        session: Session,
        authenticated_student_id: int,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Fetch student's published calendar events.

        AC-4: Reads ONLY published_calendar_snapshots (draft excluded).
        AC-2: Scope enforced by authenticated_student_id.
        AC-5: No internal audit history.

        Note: Assumes published_calendar_snapshots table exists.
        If not yet implemented, returns empty list.

        Returns:
        {
            "student_id": int,
            "calendar_events": [
                {
                    "event_id": int,
                    "event_type": str,
                    "subject": str,
                    "start_date": ISO8601,
                    "end_date": ISO8601,
                    "location": str,
                    "published_at": ISO8601
                }
            ]
        }
        """
        # Resolve the student's enrolled academic_context_ids (AC-3: scope enforcement)
        enrolled_context_ids_stmt = select(ClassEnrollment.academic_context_id).where(
            ClassEnrollment.student_id == authenticated_student_id
        )
        enrolled_context_ids = [
            row[0] for row in session.execute(enrolled_context_ids_stmt).fetchall()
        ]

        if not enrolled_context_ids:
            self._log_portal_access(
                session,
                action=ACTION_PORTAL_READ,
                entity_type="calendar",
                student_id=authenticated_student_id,
                request_id=request_id,
                result_count=0,
            )
            return {"student_id": authenticated_student_id, "calendar_events": []}

        # AC-2: Only is_published=True events; AC-3: scoped to enrolled contexts;
        # Dev Notes: student_id IS NULL (class-wide) OR student_id = authenticated
        stmt = (
            select(PublishedCalendarSnapshot)
            .where(
                PublishedCalendarSnapshot.is_published == True,  # noqa: E712
                PublishedCalendarSnapshot.academic_context_id.in_(enrolled_context_ids),
                (
                    (PublishedCalendarSnapshot.student_id == None)  # noqa: E711
                    | (PublishedCalendarSnapshot.student_id == authenticated_student_id)
                ),
            )
            .order_by(PublishedCalendarSnapshot.start_date.asc())
        )

        rows = session.execute(stmt).scalars().all()

        calendar_events = []
        for row in rows:
            event: dict = {
                "event_id": row.id,
                "event_type": row.event_type,
                "subject": row.subject,
                "start_date": row.start_date.isoformat() if row.start_date else None,
                "end_date": row.end_date.isoformat() if row.end_date else None,
                "location": row.location,
                "published_at": row.published_at.isoformat() if row.published_at else None,
            }
            calendar_events.append(event)

        self._log_portal_access(
            session,
            action=ACTION_PORTAL_READ,
            entity_type="calendar",
            student_id=authenticated_student_id,
            request_id=request_id,
            result_count=len(calendar_events),
        )

        return {
            "student_id": authenticated_student_id,
            "calendar_events": calendar_events,
        }

    # -----------------------------------------------------------------------
    # Private helpers
    # -----------------------------------------------------------------------

    def _log_portal_access(
        self,
        session: Session,
        *,
        action: str,
        entity_type: str,
        student_id: int,
        request_id: str | None = None,
        context_id: int | None = None,
        result_count: int = 0,
    ) -> None:
        """Log portal access without exposing sensitive payloads.

        AC-8: Audit trail for compliance.
        """
        after_json = {
            "entity_type": entity_type,
            "student_id": student_id,
            "context_id": context_id,
            "result_count": result_count,
            "accessed_at": datetime.now(UTC).isoformat(),
        }

        audit = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=str(student_id),
            request_id=request_id,
            after_json=json.dumps(after_json),
            reason=f"Student portal read: {entity_type}",
        )
        session.add(audit)
        session.flush()

        LOGGER.info(
            "portal_access_logged",
            extra={
                "request_id": request_id,
                "student_id": student_id,
                "action": action,
                "entity_type": entity_type,
                "result_count": result_count,
            },
        )


class PortalAccessError(Exception):
    """Raised when student attempts unauthorized portal access."""

    pass
