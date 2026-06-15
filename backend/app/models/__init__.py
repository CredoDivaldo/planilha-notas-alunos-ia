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
from backend.app.models.legacy_roster import (
    LegacyGrade,
    LegacyStudent,
    LegacyUpload,
    UPLOAD_STATUS_OK,
    UPLOAD_STATUSES,
    UPLOAD_STATUS_FAILED,
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
    "LegacyGrade",
    "LegacyStudent",
    "LegacyUpload",
    "NotificationDelivery",
    "PublicationSnapshot",
    "PublishedCalendarSnapshot",
    "Semester",
    "Shift",
    "TimestampMixin",
    "UPLOAD_STATUS_OK",
    "UPLOAD_STATUS_FAILED",
    "UPLOAD_STATUSES",
]
