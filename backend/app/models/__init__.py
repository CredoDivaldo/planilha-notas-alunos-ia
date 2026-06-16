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
from backend.app.models.publication import (
    BroadcastJob,
    NotificationDelivery,
    PublicationSnapshot,
    PublishedCalendarSnapshot,
)
from backend.app.models.roster import (
    AssessmentDefinition,
    ClassGroup,
    Course,
    Professor,
    Student,
    Subject,
    TeachingAssignment,
)

__all__ = [
    "AcademicContext",
    "AssessmentDefinition",
    "AuditLog",
    "Base",
    "BroadcastJob",
    "CalculationResult",
    "ClassEnrollment",
    "ClassGroup",
    "ContextSubjectConfiguration",
    "Course",
    "GradeEntry",
    "Professor",
    "Student",
    "Subject",
    "TeachingAssignment",
    "NotificationDelivery",
    "PublicationSnapshot",
    "PublishedCalendarSnapshot",
    "Semester",
    "Shift",
    "TimestampMixin",
]
