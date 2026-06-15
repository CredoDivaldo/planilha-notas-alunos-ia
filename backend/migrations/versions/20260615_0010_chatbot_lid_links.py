"""Create chatbot_lid_links table for WhatsApp @lid -> student mapping.

WhatsApp LID privacy means inbound webhooks carry a '<id>@lid' instead of
the real phone number. We persist a mapping per (lid, instance) so that once
a student is identified, all future messages are recognised instantly.

Revision ID: 20260615_0010
Revises: 20260615_0009
Create Date: 2026-06-15
"""
import sqlalchemy as sa
from alembic import op

revision = "20260615_0010"
down_revision = "20260615_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chatbot_lid_links",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("lid", sa.String(length=80), nullable=False),
        sa.Column("instance", sa.String(length=120), nullable=True),
        sa.Column("student_number", sa.String(length=60), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "ix_chatbot_lid_links_lid_instance",
        "chatbot_lid_links",
        ["lid", "instance"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_chatbot_lid_links_lid_instance", table_name="chatbot_lid_links")
    op.drop_table("chatbot_lid_links")
