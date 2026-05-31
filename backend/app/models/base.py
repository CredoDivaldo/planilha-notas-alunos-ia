"""Declarative base and common mixins for SQLAlchemy 2.x ORM models."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Project-wide declarative base.

    All ORM models should inherit from this class.  SQLAlchemy 2.x style.
    """


class TimestampMixin:
    """Adds ``created_at`` / ``updated_at`` columns that default to now.

    SQLite uses CURRENT_TIMESTAMP server defaults; application-level fallback
    is provided via ``default`` for cases where the row is inserted through
    the ORM (no raw SQL).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
