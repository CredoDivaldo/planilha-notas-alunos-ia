"""Roster & teaching ORM models for the normalized academic schema.

These map 1:1 to the tables created in the initial migration
(``20260528_0001_initial_academic_schema``). They were previously accessed
only via raw SQL; declaring them as ORM models lets the application use a
single, coherent relational model (students → enrollments → grades →
publication) instead of the legacy CSV-shaped tables.

Following the project convention (see ``academic.py``), foreign keys are
declared as plain ``Integer`` columns — the DB-level FK constraints live in
the migration, which keeps in-memory test fixtures simple.
"""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Integer, Numeric, String, text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base, TimestampMixin


class Course(Base, TimestampMixin):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), server_default="active", nullable=False)


class ClassGroup(Base, TimestampMixin):
    __tablename__ = "class_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), server_default="active", nullable=False)


class Subject(Base, TimestampMixin):
    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(40), server_default="active", nullable=False)


class Student(Base, TimestampMixin):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    student_number: Mapped[str] = mapped_column(String(80), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_class_group_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    course_id: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Professor(Base, TimestampMixin):
    __tablename__ = "professors"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(80), nullable=True)


class TeachingAssignment(Base, TimestampMixin):
    """A professor teaching a subject to a class group in a semester/shift.

    The canonical scoping boundary for assessment definitions, grade entries
    and publication snapshots.
    """

    __tablename__ = "teaching_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    professor_id: Mapped[int] = mapped_column(Integer, nullable=False)
    class_group_id: Mapped[int] = mapped_column(Integer, nullable=False)
    subject_id: Mapped[int] = mapped_column(Integer, nullable=False)
    semester_id: Mapped[int] = mapped_column(Integer, nullable=False)
    shift_id: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        server_default=text("true"), nullable=False, default=True
    )


class AssessmentDefinition(Base, TimestampMixin):
    """A grading component (e.g. P1, P2, Frequência) within a teaching assignment."""

    __tablename__ = "assessment_definitions"

    id: Mapped[int] = mapped_column(primary_key=True)
    teaching_assignment_id: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    max_score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, server_default=text("0"), nullable=False, default=0)
