"""Base comum dos modelos ORM (SQLAlchemy 2.x).

PT: Um "modelo ORM" é uma classe Python que representa uma tabela da base de dados;
cada atributo é uma coluna. Todos os modelos do projecto herdam de `Base`. O
`TimestampMixin` é um "bloco reutilizável" que acrescenta as colunas de datas
(criado_em / actualizado_em) a qualquer modelo que o inclua.
"""
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

    # Coluna preenchida automaticamente com a data/hora de criação do registo.
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    # Igual à anterior, mas `onupdate` actualiza-a sempre que o registo muda.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=text("CURRENT_TIMESTAMP"),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
