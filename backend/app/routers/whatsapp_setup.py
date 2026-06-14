"""Per-professor WhatsApp instance setup router.

Each professor creates and manages their own Evolution instance so that their
students communicate via the professor's own WhatsApp number.

Routes under /api/v1/whatsapp/setup:
  GET  /api/v1/whatsapp/setup/status   — connection status for professor's instance
  POST /api/v1/whatsapp/setup/create   — create/recreate the professor's instance
  GET  /api/v1/whatsapp/setup/qr       — get QR code for the professor's instance
  POST /api/v1/whatsapp/setup/webhook  — configure webhook for professor's instance
  POST /api/v1/whatsapp/setup/disconnect — disconnect (logout) the professor's instance
"""
from __future__ import annotations

import logging
import os
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import text

from backend.app.services.evolution_api_client import (
    EvolutionApiError,
    configure_webhook,
    connection_state,
    create_instance,
    get_qrcode,
)

LOGGER = logging.getLogger("backend.whatsapp_setup")

router = APIRouter(prefix="/api/v1/whatsapp/setup", tags=["whatsapp-setup"])


# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _get_professor_id(request: Request) -> int:
    auth = request.headers.get("authorization", "")
    session_id = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else None
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado.")
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        from backend.app.config import get_settings
        from backend.app.database import build_engine
        engine = build_engine(get_settings().database_url)
    now = datetime.now(UTC).replace(tzinfo=None)
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT user_id FROM user_sessions"
                " WHERE id = :sid AND is_active = 1 AND expires_at > :now LIMIT 1"
            ),
            {"sid": session_id, "now": now},
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sessão expirada.")
    return int(row[0])


def _get_engine(request: Request):
    engine = getattr(request.app.state, "engine", None)
    if engine is None:
        from backend.app.config import get_settings
        from backend.app.database import build_engine
        engine = build_engine(get_settings().database_url)
    return engine


def _ensure_whatsapp_instance_column(engine) -> None:
    """Add whatsapp_instance column to users if it doesn't exist (idempotent)."""
    try:
        with engine.connect() as conn:
            columns = conn.execute(text("PRAGMA table_info(users)")).fetchall()
            col_names = [c[1] for c in columns]
            if "whatsapp_instance" not in col_names:
                conn.execute(text("ALTER TABLE users ADD COLUMN whatsapp_instance VARCHAR(120)"))
                conn.commit()
    except Exception as exc:
        LOGGER.warning("whatsapp_instance_column_ensure_failed", extra={"error": str(exc)})


def _get_professor_instance(engine, prof_id: int) -> str:
    """Get or generate the professor's Evolution instance name."""
    _ensure_whatsapp_instance_column(engine)
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT whatsapp_instance FROM users WHERE id = :uid LIMIT 1"),
            {"uid": prof_id},
        ).fetchone()
    if row and row[0]:
        return row[0]
    # Generate a deterministic instance name
    return f"prof-{prof_id}"


def _save_professor_instance(engine, prof_id: int, instance_name: str) -> None:
    with engine.connect() as conn:
        conn.execute(
            text("UPDATE users SET whatsapp_instance = :inst WHERE id = :uid"),
            {"inst": instance_name, "uid": prof_id},
        )
        conn.commit()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SetupStatusResponse(BaseModel):
    connected: bool
    instance_name: str
    simulated: bool = False
    configured: bool


class SetupCreateResponse(BaseModel):
    instance_name: str
    status: str
    simulated: bool = False


class SetupQrResponse(BaseModel):
    instance_name: str
    code: str | None
    pairing_code: str | None = None
    simulated: bool = False


class SetupWebhookRequest(BaseModel):
    webhook_url: str


class SetupWebhookResponse(BaseModel):
    configured: bool
    webhook_url: str


class SetupDisconnectResponse(BaseModel):
    disconnected: bool
    instance_name: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/status", response_model=SetupStatusResponse)
async def setup_status(request: Request) -> SetupStatusResponse:
    """Get the professor's WhatsApp instance connection status."""
    prof_id = _get_professor_id(request)
    engine = _get_engine(request)
    instance_name = _get_professor_instance(engine, prof_id)
    configured = not instance_name.startswith("prof-") or True  # always configured if name saved

    try:
        state = await connection_state(instance_name)
    except EvolutionApiError as exc:
        raise HTTPException(status_code=502, detail=f"Evolution API error: {exc.status_code}") from exc

    return SetupStatusResponse(
        connected=state.get("connected", False),
        instance_name=instance_name,
        simulated=state.get("simulated", False),
        configured=True,
    )


@router.post("/create", response_model=SetupCreateResponse)
async def setup_create(request: Request) -> SetupCreateResponse:
    """Create (or recreate) the professor's Evolution instance."""
    prof_id = _get_professor_id(request)
    engine = _get_engine(request)
    instance_name = _get_professor_instance(engine, prof_id)

    try:
        result = await create_instance(instance_name)
    except EvolutionApiError as exc:
        raise HTTPException(status_code=502, detail=f"Evolution API error: {exc.status_code}") from exc

    # Save the instance name to the professor's profile
    _save_professor_instance(engine, prof_id, instance_name)

    return SetupCreateResponse(
        instance_name=result.get("instance_name", instance_name),
        status=result.get("status", "created"),
        simulated=result.get("simulated", False),
    )


@router.get("/qr", response_model=SetupQrResponse)
async def setup_qr(request: Request) -> SetupQrResponse:
    """Get the QR code for the professor's WhatsApp instance."""
    prof_id = _get_professor_id(request)
    engine = _get_engine(request)
    instance_name = _get_professor_instance(engine, prof_id)

    try:
        result = await get_qrcode(instance_name)
    except EvolutionApiError as exc:
        raise HTTPException(status_code=502, detail=f"Evolution API error: {exc.status_code}") from exc

    return SetupQrResponse(
        instance_name=instance_name,
        code=result.get("code"),
        pairing_code=result.get("pairing_code"),
        simulated=result.get("simulated", False),
    )


@router.post("/webhook", response_model=SetupWebhookResponse)
async def setup_webhook(body: SetupWebhookRequest, request: Request) -> SetupWebhookResponse:
    """Configure the Evolution webhook for the professor's instance."""
    prof_id = _get_professor_id(request)
    engine = _get_engine(request)
    instance_name = _get_professor_instance(engine, prof_id)

    try:
        await configure_webhook(
            instance=instance_name,
            webhook_url=body.webhook_url,
            events=["MESSAGES_UPSERT", "CONNECTION_UPDATE"],
        )
    except EvolutionApiError as exc:
        raise HTTPException(status_code=502, detail=f"Evolution API error: {exc.status_code}") from exc

    return SetupWebhookResponse(configured=True, webhook_url=body.webhook_url)


@router.post("/disconnect", response_model=SetupDisconnectResponse)
async def setup_disconnect(request: Request) -> SetupDisconnectResponse:
    """Logout/disconnect the professor's WhatsApp instance."""
    prof_id = _get_professor_id(request)
    engine = _get_engine(request)
    instance_name = _get_professor_instance(engine, prof_id)

    base_url = os.getenv("EVOLUTION_API_URL") or os.getenv("EVOLUTION_BASE_URL")
    api_key = os.getenv("EVOLUTION_API_KEY") or ""

    if not base_url:
        return SetupDisconnectResponse(disconnected=True, instance_name=instance_name)

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(
                f"{base_url.rstrip('/')}/instance/logout/{instance_name}",
                headers={"apikey": api_key, "Content-Type": "application/json"},
            )
        return SetupDisconnectResponse(
            disconnected=resp.status_code in (200, 204),
            instance_name=instance_name,
        )
    except Exception as exc:
        LOGGER.warning("whatsapp_disconnect_failed", extra={"error": str(exc)})
        return SetupDisconnectResponse(disconnected=False, instance_name=instance_name)
