"""ORM models package for the Academic Platform."""
from __future__ import annotations

from backend.app.models.academic import AuditLog, CalculationResult, GradeEntry
from backend.app.models.base import Base, TimestampMixin
from backend.app.models.contexts import (
    AcademicContext,
    ClassEnrollment,
    ContextSubjectConfiguration,
    Semester,
    Shift,
)
from backend.app.models.publication import BroadcastJob, NotificationDelivery, PublicationSnapshot

__all__ = [
    "AcademicContext",
    "AuditLog",
    "Base",
    "BroadcastJob",
    "CalculationResult",
    "ClassEnrollment",
    "ContextSubjectConfiguration",
    "GradeEntry",
    "NotificationDelivery",
    "PublicationSnapshot",
    "Semester",
    "Shift",
    "TimestampMixin",
]
