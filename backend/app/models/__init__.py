"""Pacote dos modelos ORM da Plataforma Académica.

PT: Este ficheiro junta num só sítio todos os modelos (tabelas) espalhados pelos
vários ficheiros, para o resto do código os poder importar com uma única linha:
`from backend.app.models import Student, GradeEntry, ...`. O `__all__` lista o
que é "público" deste pacote.
"""
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
