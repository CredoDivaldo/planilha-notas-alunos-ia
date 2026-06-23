"""Modelos de "contexto académico" — o coração da organização das notas.

PT: Um AcademicContext representa uma combinação única de professor + turma +
disciplina + semestre + turno. É a "fronteira" que diz a que aula pertence cada
nota e cada aluno. Semester e Shift são tabelas de referência (criadas pela
instituição). ClassEnrollment liga alunos a um contexto (a pauta da turma).

Academic context models for professor grade management (Story 5.4).

This module provides the core data model for scoping grades and student rosters
to specific academic contexts. Each context represents a unique combination of
professor, turma (class), subject, semester, and shift.

Models:
  - Semester: Reference table for academic terms
  - Shift: Reference table for class shifts
  - AcademicContext: Professor's scoped teaching assignment
  - ClassEnrollment: Student membership in a context
  - ContextSubjectConfiguration: Subject-specific rules per context
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, cast

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin

# ---------------------------------------------------------------------------
# Semester and Shift lifecycle constants
# ---------------------------------------------------------------------------

SEMESTER_STATUS_PLANNED = "planned"
SEMESTER_STATUS_ACTIVE = "active"
SEMESTER_STATUS_COMPLETED = "completed"
SEMESTER_STATUSES = (SEMESTER_STATUS_PLANNED, SEMESTER_STATUS_ACTIVE, SEMESTER_STATUS_COMPLETED)

SHIFT_STATUS_ACTIVE = "active"
SHIFT_STATUS_INACTIVE = "inactive"
SHIFT_STATUSES = (SHIFT_STATUS_ACTIVE, SHIFT_STATUS_INACTIVE)

# ---------------------------------------------------------------------------
# Academic context lifecycle constants
# ---------------------------------------------------------------------------

CONTEXT_STATUS_DRAFT = "draft"
CONTEXT_STATUS_ACTIVE = "active"
CONTEXT_STATUS_ARCHIVED = "archived"
CONTEXT_STATUSES = (CONTEXT_STATUS_DRAFT, CONTEXT_STATUS_ACTIVE, CONTEXT_STATUS_ARCHIVED)

# ---------------------------------------------------------------------------
# Class enrollment constants
# ---------------------------------------------------------------------------

ENROLLMENT_STATUS_ACTIVE = "active"
ENROLLMENT_STATUS_DROPPED = "dropped"
ENROLLMENT_STATUS_COMPLETED = "completed"
ENROLLMENT_STATUSES = (ENROLLMENT_STATUS_ACTIVE, ENROLLMENT_STATUS_DROPPED, ENROLLMENT_STATUS_COMPLETED)

# ---------------------------------------------------------------------------
# Audit event types
# ---------------------------------------------------------------------------

AUDIT_EVENT_CONTEXT_CREATED = "context_created"
AUDIT_EVENT_CONTEXT_ACTIVATED = "context_activated"
AUDIT_EVENT_CONTEXT_ARCHIVED = "context_archived"
AUDIT_EVENT_ENROLLMENT_ADDED = "enrollment_added"
AUDIT_EVENT_ENROLLMENT_DROPPED = "enrollment_dropped"
AUDIT_EVENT_ENROLLMENT_COMPLETED = "enrollment_completed"


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------


class Semester(Base, TimestampMixin):
    """Reference table for academic semesters.

    Controlled by institution; professors reference but do not create.
    Each semester has an academic year and start/end dates.
    """

    __tablename__ = "semesters"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Institution-assigned code (e.g., "2026-S1")
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    # Human-readable name (e.g., "2026 Semester 1")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Academic year (e.g., 2026)
    academic_year: Mapped[int] = mapped_column(Integer, nullable=False)
    # Semester number within year (1, 2, etc.)
    semester_number: Mapped[int] = mapped_column(Integer, nullable=False)
    # Lifecycle state: planned | active | completed
    status: Mapped[str] = mapped_column(
        String(40), server_default=SEMESTER_STATUS_PLANNED, nullable=False
    )
    # Dates when this semester runs
    start_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Shift(Base, TimestampMixin):
    """Reference table for class shifts (morning, afternoon, evening, etc.).

    Controlled by institution; professors reference but do not create.
    """

    __tablename__ = "shifts"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Institution-assigned code (e.g., "MORNING")
    code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    # Human-readable name (e.g., "Morning Shift")
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    # Display order (for UI sorting)
    shift_order: Mapped[int] = mapped_column(Integer, nullable=True)
    # Lifecycle state: active | inactive
    status: Mapped[str] = mapped_column(
        String(40), server_default=SHIFT_STATUS_ACTIVE, nullable=False
    )


class AcademicContext(Base, TimestampMixin):
    """Professor's scoped teaching assignment.

    A context uniquely identifies a professor's assignment to teach a subject
    in a specific turma (class/group) during a semester in a specific shift.

    Compound uniqueness ensures no duplicate assignments, and serves as the
    primary scoping boundary for grade entry, calculation, and publication.
    """

    __tablename__ = "academic_contexts"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK: users.id — professor (enforced at DB level via migration)
    professor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # Academic year (cached for query efficiency; derived from semester.academic_year)
    academic_year: Mapped[int] = mapped_column(Integer, nullable=False)
    # Class/group identifier (e.g., "10A", "11B") — must be unique per (professor, semester, shift)
    turma: Mapped[str] = mapped_column(String(60), nullable=False)
    # Subject being taught (e.g., "Mathematics", "Physics")
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    # FK: semesters.id
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # FK: shifts.id
    shift_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # Lifecycle state: draft | active | archived
    status: Mapped[str] = mapped_column(
        String(40), server_default=CONTEXT_STATUS_DRAFT, nullable=False
    )
    # Notes or additional metadata about this context
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # FK: teaching_assignments.id — 1:1 link to the normalized scoping entity
    teaching_assignment_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class ClassEnrollment(Base, TimestampMixin):
    """Student membership in an academic context (roster).

    Links students to contexts for grade entry validation.
    Tracks enrollment status lifecycle: active → dropped/completed.
    """

    __tablename__ = "class_enrollments"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK: academic_contexts.id
    academic_context_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # FK: users.id — student (enforced at DB level via migration)
    student_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # Enrollment status: active | dropped | completed
    enrollment_status: Mapped[str] = mapped_column(
        String(40), server_default=ENROLLMENT_STATUS_ACTIVE, nullable=False
    )
    # When student was dropped from context (NULL if still active/completed)
    dropped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # When student was marked completed (NULL if still active)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ContextSubjectConfiguration(Base, TimestampMixin):
    """Subject-specific configuration per academic context.

    Stores flexible JSON configuration for assessment counts, weights,
    formula versions, and derived state rules. Same subject in different
    contexts may have different configurations.
    """

    __tablename__ = "context_subject_configurations"

    id: Mapped[int] = mapped_column(primary_key=True)
    # FK: academic_contexts.id
    academic_context_id: Mapped[int] = mapped_column(Integer, nullable=False)
    # JSON blob with flexible structure:
    # {
    #   "formula_version": "v1.0",
    #   "assessment_count": 4,
    #   "weight_distribution": {"assessment": 0.5, "exam": 0.5},
    #   "minimum_grade": 2.0,
    #   "derived_state_rules": { ... }
    # }
    configuration_json: Mapped[str] = mapped_column(Text, nullable=False)

    # A configuração é guardada como texto JSON. Estes dois métodos convertem
    # entre texto (na BD) e dicionário Python (no código):
    def get_config(self) -> dict[str, Any]:
        """Lê o JSON guardado e devolve-o como dicionário Python."""
        return cast(dict[str, Any], json.loads(self.configuration_json))  # texto → dict

    def set_config(self, config: dict[str, Any]) -> None:
        """Recebe um dicionário e guarda-o como texto JSON."""
        self.configuration_json = json.dumps(config)  # dict → texto
