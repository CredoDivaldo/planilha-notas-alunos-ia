from __future__ import annotations

import os
from dataclasses import dataclass


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

    return Settings(
        database_url=os.getenv("ACADEMIC_DATABASE_URL", Settings.database_url),
        chatbot_webhook_token=os.getenv("CHATBOT_WEBHOOK_TOKEN", ""),
        chatbot_rate_limit_daily=rate_limit,
    )
