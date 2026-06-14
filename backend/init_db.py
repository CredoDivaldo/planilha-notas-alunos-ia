"""Database initialisation script run before uvicorn starts.

Strategy:
- If the database is empty → run all Alembic migrations from scratch.
- If tables exist but no alembic_version tracking → stamp head (tables already
  match the final schema) and apply any ORM models missing from migrations.
- If alembic_version exists → run upgrade head normally (idempotent).
"""
from __future__ import annotations

import logging
import os
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
LOGGER = logging.getLogger("backend.init_db")


def main() -> None:
    db_url = os.environ.get("ACADEMIC_DATABASE_URL", "sqlite:///data/app.sqlite3")

    from sqlalchemy import create_engine, inspect as sa_inspect, text

    engine = create_engine(db_url)

    # Enable WAL for SQLite concurrency
    with engine.connect() as conn:
        if engine.dialect.name == "sqlite":
            conn.exec_driver_sql("PRAGMA journal_mode=WAL")
            conn.exec_driver_sql("PRAGMA foreign_keys=ON")
            conn.commit()

    inspector = sa_inspect(engine)
    existing_tables = set(inspector.get_table_names())
    has_alembic_tracking = "alembic_version" in existing_tables

    from alembic.config import Config
    from alembic import command as alembic_command

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)

    if not existing_tables:
        LOGGER.info("Fresh database — running all Alembic migrations")
        alembic_command.upgrade(cfg, "head")
    elif not has_alembic_tracking:
        LOGGER.info(
            "Tables exist without Alembic tracking — stamping head and patching missing tables"
        )
        alembic_command.stamp(cfg, "head")
        # Also create any ORM-only tables that might be missing
        from backend.app.models import Base
        Base.metadata.create_all(engine)
    else:
        LOGGER.info("Alembic tracking found — upgrading to head")
        alembic_command.upgrade(cfg, "head")

    engine.dispose()
    LOGGER.info("Database initialisation complete")


if __name__ == "__main__":
    main()
