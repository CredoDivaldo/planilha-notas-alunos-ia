from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    """Load .env from project root if python-dotenv is available."""
    try:
        from dotenv import load_dotenv  # type: ignore[import]
        root = Path(__file__).parent.parent.parent
        env_file = root / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=False)
    except ImportError:
        pass


_load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "Planilha Notas Alunos API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///data/app.sqlite3"
    chatbot_webhook_token: str = ""
    chatbot_rate_limit_daily: int = 10


def get_settings() -> Settings:
    # Parse rate limit as int
    rate_limit_str = os.getenv("CHATBOT_RATE_LIMIT_DAILY", "10")
    try:
        rate_limit = int(rate_limit_str)
    except (ValueError, TypeError):
        rate_limit = 10

    # Accept PostgreSQL URL from Railway's DATABASE_URL or POSTGRES_URL as well
    db_url = (
        os.getenv("ACADEMIC_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or Settings.database_url
    )
    # Railway provides postgres:// but SQLAlchemy needs postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return Settings(
        database_url=db_url,
        chatbot_webhook_token=os.getenv("CHATBOT_WEBHOOK_TOKEN", ""),
        chatbot_rate_limit_daily=rate_limit,
    )
