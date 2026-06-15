"""Initial academic schema.

Revision ID: 20260528_0001
Revises:
Create Date: 2026-05-28 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260528_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> tuple[sa.Column[sa.DateTime], sa.Column[sa.DateTime]]:
    return (
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
    )


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="active", nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("code", name="uq_courses_code"),
    )
    op.create_index("ix_courses_code", "courses", ["code"])

    op.create_table(
        "semesters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=True),
        sa.Column("ends_on", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="planned", nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("code", name="uq_semesters_code"),
    )
    op.create_index("ix_semesters_code", "semesters", ["code"])

    op.create_table(
        "shifts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(length=40), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="active", nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("code", name="uq_shifts_code"),
    )
    op.create_index("ix_shifts_code", "shifts", ["code"])

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column(
            "must_change_password", sa.Boolean(), server_default=sa.text("true"), nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_username", "users", ["username"])
    op.create_index("ix_users_role", "users", ["role"])

    op.create_table(
        "class_groups",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=True),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="active", nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("code", name="uq_class_groups_code"),
    )
    op.create_index("ix_class_groups_code", "class_groups", ["code"])
    op.create_index("ix_class_groups_course_id", "class_groups", ["course_id"])

    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=True),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="active", nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("code", name="uq_subjects_code"),
    )
    op.create_index("ix_subjects_code", "subjects", ["code"])
    op.create_index("ix_subjects_course_id", "subjects", ["course_id"])

    op.create_table(
        "students",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("student_number", sa.String(length=80), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=80), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column(
            "current_class_group_id", sa.Integer(), sa.ForeignKey("class_groups.id"), nullable=True
        ),
        sa.Column("course_id", sa.Integer(), sa.ForeignKey("courses.id"), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("student_number", name="uq_students_student_number"),
        sa.UniqueConstraint("user_id", name="uq_students_user_id"),
    )
    op.create_index("ix_students_student_number", "students", ["student_number"])
    op.create_index("ix_students_current_class_group_id", "students", ["current_class_group_id"])

    op.create_table(
        "professors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=80), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint("user_id", name="uq_professors_user_id"),
    )
    op.create_index("ix_professors_user_id", "professors", ["user_id"])

    op.create_table(
        "teaching_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("professor_id", sa.Integer(), sa.ForeignKey("professors.id"), nullable=False),
        sa.Column("class_group_id", sa.Integer(), sa.ForeignKey("class_groups.id"), nullable=False),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=False),
        sa.Column("shift_id", sa.Integer(), sa.ForeignKey("shifts.id"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint(
            "professor_id",
            "class_group_id",
            "subject_id",
            "semester_id",
            "shift_id",
            name="uq_teaching_assignments_context",
        ),
    )
    op.create_index(
        "ix_teaching_assignments_context",
        "teaching_assignments",
        ["class_group_id", "subject_id", "semester_id", "shift_id"],
    )
    op.create_index(
        "ix_teaching_assignments_professor_id", "teaching_assignments", ["professor_id"]
    )

    op.create_table(
        "enrollments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("class_group_id", sa.Integer(), sa.ForeignKey("class_groups.id"), nullable=False),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=False),
        sa.Column("shift_id", sa.Integer(), sa.ForeignKey("shifts.id"), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="active", nullable=False),
        *_timestamps(),
        sa.UniqueConstraint(
            "student_id",
            "class_group_id",
            "semester_id",
            "shift_id",
            name="uq_enrollments_context",
        ),
    )
    op.create_index("ix_enrollments_student_id", "enrollments", ["student_id"])
    op.create_index(
        "ix_enrollments_context",
        "enrollments",
        ["class_group_id", "semester_id", "shift_id"],
    )

    op.create_table(
        "assessment_definitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "teaching_assignment_id",
            sa.Integer(),
            sa.ForeignKey("teaching_assignments.id"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=60), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("weight", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("max_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("sort_order", sa.Integer(), server_default=sa.text("0"), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint(
            "teaching_assignment_id",
            "code",
            name="uq_assessment_definitions_assignment_code",
        ),
    )
    op.create_index(
        "ix_assessment_definitions_assignment_id",
        "assessment_definitions",
        ["teaching_assignment_id"],
    )

    op.create_table(
        "grade_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column(
            "teaching_assignment_id",
            sa.Integer(),
            sa.ForeignKey("teaching_assignments.id"),
            nullable=False,
        ),
        sa.Column(
            "assessment_definition_id",
            sa.Integer(),
            sa.ForeignKey("assessment_definitions.id"),
            nullable=False,
        ),
        sa.Column("raw_value", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("normalized_value", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("status", sa.String(length=40), server_default="draft", nullable=False),
        sa.Column("source_upload_id", sa.String(length=120), nullable=True),
        sa.Column("updated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        *_timestamps(),
        sa.UniqueConstraint(
            "student_id",
            "assessment_definition_id",
            name="uq_grade_entries_student_assessment",
        ),
    )
    op.create_index("ix_grade_entries_student_id", "grade_entries", ["student_id"])
    op.create_index(
        "ix_grade_entries_assignment_status",
        "grade_entries",
        ["teaching_assignment_id", "status"],
    )

    op.create_table(
        "calculation_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column(
            "teaching_assignment_id",
            sa.Integer(),
            sa.ForeignKey("teaching_assignments.id"),
            nullable=False,
        ),
        sa.Column("formula_version", sa.String(length=80), nullable=False),
        sa.Column("computed_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column(
            "derived_state", sa.String(length=80), server_default="provisional", nullable=False
        ),
        sa.Column(
            "computed_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        *_timestamps(),
        sa.UniqueConstraint(
            "student_id",
            "teaching_assignment_id",
            "formula_version",
            name="uq_calculation_results_formula",
        ),
    )
    op.create_index(
        "ix_calculation_results_student_assignment",
        "calculation_results",
        ["student_id", "teaching_assignment_id"],
    )

    op.create_table(
        "broadcast_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "teaching_assignment_id",
            sa.Integer(),
            sa.ForeignKey("teaching_assignments.id"),
            nullable=True,
        ),
        sa.Column("class_group_id", sa.Integer(), sa.ForeignKey("class_groups.id"), nullable=True),
        sa.Column("job_type", sa.String(length=80), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("status", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("channels_json", sa.Text(), nullable=True),
        sa.Column("total_recipients", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_success", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("total_failed", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_broadcast_jobs_status", "broadcast_jobs", ["status"])
    op.create_index("ix_broadcast_jobs_assignment_id", "broadcast_jobs", ["teaching_assignment_id"])

    op.create_table(
        "publication_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column(
            "teaching_assignment_id",
            sa.Integer(),
            sa.ForeignKey("teaching_assignments.id"),
            nullable=False,
        ),
        sa.Column(
            "broadcast_job_id", sa.Integer(), sa.ForeignKey("broadcast_jobs.id"), nullable=False
        ),
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.Column("published_score", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("published_state", sa.String(length=80), nullable=False),
        sa.Column("published_payload_json", sa.Text(), nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "student_id",
            "teaching_assignment_id",
            "snapshot_version",
            name="uq_publication_snapshots_version",
        ),
    )
    op.create_index(
        "ix_publication_snapshots_student_current",
        "publication_snapshots",
        ["student_id", "is_current"],
    )
    op.create_index(
        "uq_publication_snapshots_one_current",
        "publication_snapshots",
        ["student_id", "teaching_assignment_id"],
        unique=True,
        sqlite_where=sa.text("is_current = 1"),
        postgresql_where=sa.text("is_current = true"),
    )

    op.create_table(
        "calendar_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "teaching_assignment_id",
            sa.Integer(),
            sa.ForeignKey("teaching_assignments.id"),
            nullable=True,
        ),
        sa.Column("class_group_id", sa.Integer(), sa.ForeignKey("class_groups.id"), nullable=True),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id"), nullable=True),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("starts_at", sa.DateTime(), nullable=False),
        sa.Column("ends_at", sa.DateTime(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("internal_status", sa.String(length=40), server_default="draft", nullable=False),
        sa.Column("created_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        *_timestamps(),
    )
    op.create_index(
        "ix_calendar_events_context",
        "calendar_events",
        ["class_group_id", "semester_id", "subject_id"],
    )
    op.create_index("ix_calendar_events_starts_at", "calendar_events", ["starts_at"])

    op.create_table(
        "published_calendar_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "calendar_event_id", sa.Integer(), sa.ForeignKey("calendar_events.id"), nullable=True
        ),
        sa.Column(
            "broadcast_job_id", sa.Integer(), sa.ForeignKey("broadcast_jobs.id"), nullable=False
        ),
        sa.Column("class_group_id", sa.Integer(), sa.ForeignKey("class_groups.id"), nullable=True),
        sa.Column("semester_id", sa.Integer(), sa.ForeignKey("semesters.id"), nullable=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id"), nullable=True),
        sa.Column("snapshot_version", sa.Integer(), nullable=False),
        sa.Column("published_payload_json", sa.Text(), nullable=False),
        sa.Column("is_current", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "published_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_published_calendar_snapshots_context_current",
        "published_calendar_snapshots",
        ["class_group_id", "semester_id", "subject_id", "is_current"],
    )

    op.create_table(
        "notification_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "broadcast_job_id", sa.Integer(), sa.ForeignKey("broadcast_jobs.id"), nullable=False
        ),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("channel", sa.String(length=40), nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("attempt", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("external_response_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
    )
    op.create_index(
        "ix_notification_deliveries_job_status",
        "notification_deliveries",
        ["broadcast_job_id", "status"],
    )

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("request_id", sa.String(length=120), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=120), nullable=False),
        sa.Column("entity_id", sa.String(length=120), nullable=True),
        sa.Column("before_json", sa.Text(), nullable=True),
        sa.Column("after_json", sa.Text(), nullable=True),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False
        ),
    )
    op.create_index("ix_audit_log_actor_user_id", "audit_log", ["actor_user_id"])
    op.create_index("ix_audit_log_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("ix_audit_log_request_id", "audit_log", ["request_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_request_id", table_name="audit_log")
    op.drop_index("ix_audit_log_entity", table_name="audit_log")
    op.drop_index("ix_audit_log_actor_user_id", table_name="audit_log")
    op.drop_table("audit_log")

    op.drop_index("ix_notification_deliveries_job_status", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")

    op.drop_index(
        "ix_published_calendar_snapshots_context_current",
        table_name="published_calendar_snapshots",
    )
    op.drop_table("published_calendar_snapshots")

    op.drop_index("ix_calendar_events_starts_at", table_name="calendar_events")
    op.drop_index("ix_calendar_events_context", table_name="calendar_events")
    op.drop_table("calendar_events")

    op.drop_index("uq_publication_snapshots_one_current", table_name="publication_snapshots")
    op.drop_index("ix_publication_snapshots_student_current", table_name="publication_snapshots")
    op.drop_table("publication_snapshots")

    op.drop_index("ix_broadcast_jobs_assignment_id", table_name="broadcast_jobs")
    op.drop_index("ix_broadcast_jobs_status", table_name="broadcast_jobs")
    op.drop_table("broadcast_jobs")

    op.drop_index(
        "ix_calculation_results_student_assignment",
        table_name="calculation_results",
    )
    op.drop_table("calculation_results")

    op.drop_index("ix_grade_entries_assignment_status", table_name="grade_entries")
    op.drop_index("ix_grade_entries_student_id", table_name="grade_entries")
    op.drop_table("grade_entries")

    op.drop_index(
        "ix_assessment_definitions_assignment_id",
        table_name="assessment_definitions",
    )
    op.drop_table("assessment_definitions")

    op.drop_index("ix_enrollments_context", table_name="enrollments")
    op.drop_index("ix_enrollments_student_id", table_name="enrollments")
    op.drop_table("enrollments")

    op.drop_index("ix_teaching_assignments_professor_id", table_name="teaching_assignments")
    op.drop_index("ix_teaching_assignments_context", table_name="teaching_assignments")
    op.drop_table("teaching_assignments")

    op.drop_index("ix_professors_user_id", table_name="professors")
    op.drop_table("professors")

    op.drop_index("ix_students_current_class_group_id", table_name="students")
    op.drop_index("ix_students_student_number", table_name="students")
    op.drop_table("students")

    op.drop_index("ix_subjects_course_id", table_name="subjects")
    op.drop_index("ix_subjects_code", table_name="subjects")
    op.drop_table("subjects")

    op.drop_index("ix_class_groups_course_id", table_name="class_groups")
    op.drop_index("ix_class_groups_code", table_name="class_groups")
    op.drop_table("class_groups")

    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    op.drop_index("ix_shifts_code", table_name="shifts")
    op.drop_table("shifts")

    op.drop_index("ix_semesters_code", table_name="semesters")
    op.drop_table("semesters")

    op.drop_index("ix_courses_code", table_name="courses")
    op.drop_table("courses")
