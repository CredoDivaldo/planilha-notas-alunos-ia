"""Auth and role foundation: sessions, delegate assignments, credential delivery.

Adds:
- user_sessions table (server-side session store)
- delegate_assignments table (scoped delegate access with approval workflow)
- pending_credential_deliveries table (password delivery log, no cleartext)
- audit_log extended: auth_event_type, failure_reason columns
- users: role constraint enforced via CHECK (already string column from 0001)

Revision ID: 20260531_0002
Revises: 20260528_0001
Create Date: 2026-05-31 00:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260531_0002"
down_revision: str | None = "20260528_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Valid role values — enforced in application layer; documented here for reference.
# professor | student | delegate | admin_local
VALID_ROLES = ("professor", "student", "delegate", "admin_local")

# Valid delegate assignment states
VALID_DELEGATE_STATES = ("pending", "approved", "rejected")

# Valid credential delivery states
VALID_DELIVERY_STATES = ("pending", "sent", "failed")

# Valid auth audit event types
VALID_AUTH_EVENT_TYPES = (
    "login",
    "failed_login",
    "password_change",
    "delegate_assignment",
    "sensitive_op_approval_state_change",
    "logout",
    "session_rotation",
)


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # user_sessions — server-side session store                           #
    # Cookie only carries the session id; state lives here.               #
    # ------------------------------------------------------------------ #
    op.create_table(
        "user_sessions",
        sa.Column("id", sa.String(length=128), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("rotated_at", sa.DateTime(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("1"), nullable=False),
        # Metadata — no secrets stored here
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
    )
    op.create_index("ix_user_sessions_user_id", "user_sessions", ["user_id"])
    op.create_index(
        "ix_user_sessions_user_active",
        "user_sessions",
        ["user_id", "is_active"],
    )
    op.create_index("ix_user_sessions_expires_at", "user_sessions", ["expires_at"])

    # ------------------------------------------------------------------ #
    # delegate_assignments — scoped delegate access                       #
    # Delegates are students with limited operational access per context.  #
    # Sensitive actions require professor-validation (state workflow).     #
    # ------------------------------------------------------------------ #
    op.create_table(
        "delegate_assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        # context_type: e.g. "class_group", "teaching_assignment"
        sa.Column("context_type", sa.String(length=80), nullable=False),
        # context_id: FK value in the context table; stored as string for flexibility
        sa.Column("context_id", sa.String(length=80), nullable=False),
        # state: pending | approved | rejected
        sa.Column("state", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column(
            "requires_professor_validation",
            sa.Boolean(),
            server_default=sa.text("1"),
            nullable=False,
        ),
        sa.Column("assigned_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("validated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("validated_at", sa.DateTime(), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_delegate_assignments_user_id", "delegate_assignments", ["user_id"])
    op.create_index(
        "ix_delegate_assignments_context",
        "delegate_assignments",
        ["context_type", "context_id"],
    )
    op.create_index("ix_delegate_assignments_state", "delegate_assignments", ["state"])

    # ------------------------------------------------------------------ #
    # pending_credential_deliveries — password delivery log               #
    # Stores only delivery intent metadata — never cleartext passwords.   #
    # Delivery channel is configurable (TBD: WhatsApp, paper, email...).  #
    # ------------------------------------------------------------------ #
    op.create_table(
        "pending_credential_deliveries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        # delivery_channel: configurable — "whatsapp" | "paper" | "email" | "sms" | "tbd"
        sa.Column("delivery_channel", sa.String(length=80), server_default="tbd", nullable=False),
        # destination: obfuscated or masked — never store raw phone/email if avoidable
        sa.Column("destination_masked", sa.String(length=255), nullable=True),
        # state: pending | sent | failed
        sa.Column("state", sa.String(length=40), server_default="pending", nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        # Audit: who initiated delivery and when
        sa.Column("initiated_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_pending_credential_deliveries_user_id", "pending_credential_deliveries", ["user_id"]
    )
    op.create_index(
        "ix_pending_credential_deliveries_state", "pending_credential_deliveries", ["state"]
    )

    # ------------------------------------------------------------------ #
    # Extend audit_log with auth-specific columns                         #
    # New columns: auth_event_type, failure_reason                        #
    # Existing rows will have NULL for these columns — acceptable.        #
    # ------------------------------------------------------------------ #
    op.add_column(
        "audit_log",
        sa.Column("auth_event_type", sa.String(length=80), nullable=True),
    )
    op.add_column(
        "audit_log",
        sa.Column("failure_reason", sa.String(length=120), nullable=True),
    )
    op.create_index("ix_audit_log_auth_event_type", "audit_log", ["auth_event_type"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_auth_event_type", table_name="audit_log")
    op.drop_column("audit_log", "failure_reason")
    op.drop_column("audit_log", "auth_event_type")

    op.drop_index("ix_pending_credential_deliveries_state", table_name="pending_credential_deliveries")
    op.drop_index(
        "ix_pending_credential_deliveries_user_id", table_name="pending_credential_deliveries"
    )
    op.drop_table("pending_credential_deliveries")

    op.drop_index("ix_delegate_assignments_state", table_name="delegate_assignments")
    op.drop_index("ix_delegate_assignments_context", table_name="delegate_assignments")
    op.drop_index("ix_delegate_assignments_user_id", table_name="delegate_assignments")
    op.drop_table("delegate_assignments")

    op.drop_index("ix_user_sessions_expires_at", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_active", table_name="user_sessions")
    op.drop_index("ix_user_sessions_user_id", table_name="user_sessions")
    op.drop_table("user_sessions")
