from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Planilha Notas Alunos API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///data/app.sqlite3"
    chatbot_webhook_token: str = ""


def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv("ACADEMIC_DATABASE_URL", Settings.database_url),
        chatbot_webhook_token=os.getenv("CHATBOT_WEBHOOK_TOKEN", ""),
    )
