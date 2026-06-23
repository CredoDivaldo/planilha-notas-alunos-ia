"""Configurações da aplicação (variáveis de ambiente).

Centraliza tudo o que pode mudar entre máquinas/ambientes: nome da app, prefixo
da API, URL da base de dados, token do webhook e limites do chatbot. Os valores
vêm de variáveis de ambiente (ou do ficheiro .env) com valores por defeito.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv() -> None:
    """Carrega o ficheiro .env da raiz do projecto, se o python-dotenv existir."""
    try:
        from dotenv import load_dotenv  # type: ignore[import]
        root = Path(__file__).parent.parent.parent
        env_file = root / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=False)
    except ImportError:
        pass


_load_dotenv()


# @dataclass cria automaticamente o __init__ etc.; `frozen=True` torna a
# instância imutável (não se altera depois de criada). Cada linha = uma definição
# com o seu valor por defeito.
@dataclass(frozen=True)
class Settings:
    app_name: str = "Planilha Notas Alunos API"
    api_prefix: str = "/api/v1"
    database_url: str = "sqlite:///data/app.sqlite3"
    chatbot_webhook_token: str = ""
    chatbot_rate_limit_daily: int = 10


# Lê as variáveis de ambiente e devolve um Settings preenchido.
def get_settings() -> Settings:
    # Converte o limite diário para inteiro (com valor seguro se vier inválido).
    rate_limit_str = os.getenv("CHATBOT_RATE_LIMIT_DAILY", "10")
    try:
        rate_limit = int(rate_limit_str)
    except (ValueError, TypeError):
        rate_limit = 10

    # Procura a URL da BD por ordem de prioridade; o `or` usa o 1.º valor não-vazio.
    # Assim em produção (Railway) usa PostgreSQL e localmente cai no SQLite por defeito.
    db_url = (
        os.getenv("ACADEMIC_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or os.getenv("POSTGRES_URL")
        or Settings.database_url
    )
    # O Railway fornece "postgres://" mas o SQLAlchemy exige "postgresql://".
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    return Settings(
        database_url=db_url,
        chatbot_webhook_token=os.getenv("CHATBOT_WEBHOOK_TOKEN", ""),
        chatbot_rate_limit_daily=rate_limit,
    )
