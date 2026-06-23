"""Ligação à base de dados (SQLAlchemy).

Cria o "engine" — o objecto que abre ligações à BD — e trata das particularidades
do SQLite (criar a pasta do ficheiro, activar chaves estrangeiras e o modo WAL).
Funciona tanto para SQLite (local) como para PostgreSQL (produção).
"""
from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

from sqlalchemy import Engine, create_engine, event, text

LOGGER = logging.getLogger("backend.database")


# Extrai o caminho do ficheiro a partir de uma URL "sqlite:///...". Devolve None
# se não for SQLite (ex.: PostgreSQL não usa ficheiro local).
def sqlite_path_from_url(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite:///"):
        return None
    return Path(database_url.removeprefix("sqlite:///"))


# Garante que a pasta onde o ficheiro SQLite vai viver existe (cria se preciso).
def ensure_sqlite_directory(database_url: str) -> Path | None:
    sqlite_path = sqlite_path_from_url(database_url)
    if sqlite_path is not None:
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    return sqlite_path


# Constrói o "engine" da BD a partir da URL. É a peça central do SQLAlchemy.
def build_engine(database_url: str) -> Engine:
    connect_args: dict[str, Any] = {}
    if database_url.startswith("sqlite"):
        # Permite usar a mesma ligação em várias threads (necessário com o FastAPI).
        connect_args["check_same_thread"] = False

    engine = create_engine(database_url, connect_args=connect_args, future=True)

    if database_url.startswith("sqlite"):

        # Sempre que uma nova ligação SQLite é aberta, aplica estes ajustes ("PRAGMA"):
        # foreign_keys=ON força integridade referencial; journal_mode=WAL melhora
        # a concorrência (permite ler enquanto se escreve).
        @event.listens_for(engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection: Any, _connection_record: Any) -> None:
            cursor = dbapi_connection.cursor()
            try:
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.execute("PRAGMA journal_mode=WAL")
            except sqlite3.DatabaseError as exc:
                LOGGER.warning("sqlite_pragma_failed", extra={"error": str(exc)})
            finally:
                cursor.close()

    return engine


# Inspecciona o estado actual da BD (que dialecto, se WAL/chaves estrangeiras
# estão activas). Usado no /health para diagnóstico.
def inspect_sqlite_runtime(engine: Engine) -> dict[str, str | bool]:
    if engine.dialect.name != "sqlite":
        return {"dialect": engine.dialect.name, "wal_enabled": False}

    with engine.connect() as connection:
        journal_mode = str(connection.execute(text("PRAGMA journal_mode")).scalar_one()).lower()
        foreign_keys = int(connection.execute(text("PRAGMA foreign_keys")).scalar_one())

    return {
        "dialect": "sqlite",
        "journal_mode": journal_mode,
        "wal_enabled": journal_mode == "wal",
        "foreign_keys_enabled": foreign_keys == 1,
    }
