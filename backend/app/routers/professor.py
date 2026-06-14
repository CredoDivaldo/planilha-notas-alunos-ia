"""Professor-side endpoints (Story 8.2 — Epic 8 cutover).

Five endpoints, all under ``/api/v1``:

* ``POST /grades/match``                          — Story 8.2 AC-1
* ``POST /broadcast/``                            — Story 8.2 AC-2 / AC-4
* ``GET  /whatsapp/status``                       — Story 8.2 AC-3
* ``POST /whatsapp/instance/create``              — Story 8.2 AC-4
* ``GET  /whatsapp/instance/connect``             — Story 8.2 AC-4

The router delegates business logic to thin adapters in
``backend.app.publication.service`` (match + broadcast) and
``backend.app.services.evolution_api_client`` (WhatsApp lifecycle). It
never persists state itself — every endpoint reads the request body,
calls the right helper, and returns a JSON-serialisable summary that
matches the shape the React dashboard's
``PublishPage.tsx``/``DashboardPage.tsx`` already consume.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field

from backend.app.publication.service import compute_match, trigger_broadcast
from backend.app.services.evolution_api_client import (
    EvolutionApiError,
    _default_instance,
    configure_webhook,
    connection_state,
    create_instance,
    get_qrcode,
)

LOGGER = logging.getLogger("backend.professor.routes")

router = APIRouter(prefix="/api/v1", tags=["professor"])


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------


class MatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context_id: int | None = None


class MatchItem(BaseModel):
    numero_estudante: str
    nome: str
    turma: str
    whatsapp: str
    nota: str


class MatchResponse(BaseModel):
    matched: int
    unmatched: int
    invalid_phones: int
    items: list[MatchItem]


class BroadcastFailureItem(BaseModel):
    student_id: str
    student_name: str
    student_number: str
    reason: str


class BroadcastRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    context_id: int = Field(..., description="Academic context identifier")
    audience: Any | None = None  # 'all' | 'approved' | 'rejected' | list[str]
    channels: list[str] = Field(default_factory=lambda: ["portal"])
    message_template: str | None = None
    teaching_assignment_id: int | None = None
    actor_user_id: int | None = None
    class_group_id: int | None = None
    dry_run: bool = False
    mode: str | None = None  # legacy field from DashboardPage ('simulation'/'real')


class BroadcastResponse(BaseModel):
    simulated: bool
    portal_published: int = 0
    whatsapp_sent: int = 0
    failures: int = 0
    failure_list: list[BroadcastFailureItem] = Field(default_factory=list)
    broadcast_job_id: int | None = None
    total_recipients: int | None = None
    existing_current_snapshots: int | None = None
    channels: list[str] | None = None
    teaching_assignment_id: int | None = None


class WhatsAppStatusResponse(BaseModel):
    connected: bool
    instance_name: str
    simulated: bool = False


class WhatsAppInstanceCreateResponse(BaseModel):
    instance_name: str
    status: str
    simulated: bool = False


class WhatsAppConnectResponse(BaseModel):
    instance_name: str
    code: str | None = None
    pairing_code: str | None = None
    simulated: bool = False
    connected: bool = False


class WebhookConfigureRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    webhook_url: str


class WebhookConfigureResponse(BaseModel):
    configured: bool
    url: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_session(request: Request):
    """Return the FastAPI request's SQLAlchemy session.

    Mirrors the helper used by ``backend.app.routers.ingest`` — the
    in-memory test fixture wires a custom ``session_factory`` on
    ``app.state`` and the test never enters the ``lifespan`` context.
    """
    from backend.app.routers.chatbot import get_db_session
    from sqlalchemy.orm import Session

    sess = get_db_session(request)
    if not isinstance(sess, Session):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session unavailable",
        )
    return sess


def _resolve_teaching_assignment_id(
    session: Any, context_id: int
) -> int | None:
    """Look up the canonical teaching assignment for a context.

    The schema does not model ``TeachingAssignment`` as its own table —
    ``teaching_assignment_id`` is a free ``Integer`` column on
    ``GradeEntry`` / ``PublicationSnapshot``. We pick the smallest one
    present in the DB as a stable default for the dashboard flow.

    Returns ``None`` when no assignment exists (Story 8.2 keeps the
    router permissive — the dashboard will display "no context" rather
    than a 500).
    """
    try:
        from sqlalchemy import func, select

        from backend.app.models import GradeEntry

        row = session.execute(
            select(func.min(GradeEntry.teaching_assignment_id)).where(
                GradeEntry.academic_context_id == context_id
            )
        ).scalar()
    except Exception:
        return None
    return int(row) if row is not None else None


def _safe_detail(message: str) -> str:
    """Story 3.6 — keep error messages short; no internals leaked."""
    if len(message) > 240:
        return message[:237] + "..."
    return message


# ---------------------------------------------------------------------------
# POST /api/v1/grades/match
# ---------------------------------------------------------------------------


@router.post(
    "/grades/match",
    response_model=MatchResponse,
    status_code=status.HTTP_200_OK,
)
async def grades_match(request: Request, payload: MatchRequest | None = None) -> MatchResponse:
    """AC-1: reconcile students × grades and return counts + items.

    Body is optional (``{"context_id": <int>}``); when ``context_id`` is
    omitted, the matcher runs against all un-scoped rows.
    """
    session = _get_session(request)
    ctx_id = payload.context_id if payload else None
    try:
        result = compute_match(session, context_id=ctx_id)
    except Exception as exc:  # DB errors / etc.
        LOGGER.exception("grades_match_failed", extra={"context_id": ctx_id})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_safe_detail(f"Match failed: {exc.__class__.__name__}"),
        ) from exc

    return MatchResponse(
        matched=result["matched"],
        unmatched=result["unmatched"],
        invalid_phones=result["invalid_phones"],
        items=[MatchItem(**item) for item in result["items"]],
    )


# ---------------------------------------------------------------------------
# POST /api/v1/broadcast/
# ---------------------------------------------------------------------------


@router.post(
    "/broadcast/",
    response_model=BroadcastResponse,
    status_code=status.HTTP_200_OK,
)
async def broadcast(request: Request, payload: BroadcastRequest) -> BroadcastResponse:
    """AC-2 / AC-4: trigger the publication workflow.

    ``dry_run=True`` (or ``mode=='simulation'`` from the legacy dashboard
    field) returns ``{simulated: true, ...}`` and does not persist
    snapshots. Real runs create a ``BroadcastJob`` and ``PublicationSnapshot``
    rows via ``PublicationService``.
    """
    session = _get_session(request)
    dry_run = payload.dry_run or payload.mode == "simulation"

    teaching_assignment_id = payload.teaching_assignment_id
    if teaching_assignment_id is None:
        teaching_assignment_id = _resolve_teaching_assignment_id(
            session, payload.context_id
        )
    if teaching_assignment_id is None and not dry_run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No teaching assignment for this context",
        )

    actor_user_id = payload.actor_user_id or 1  # demo default

    try:
        result = await trigger_broadcast(
            session,
            teaching_assignment_id=teaching_assignment_id or 0,
            actor_user_id=actor_user_id,
            channels=payload.channels,
            dry_run=dry_run,
            class_group_id=payload.class_group_id,
        )
    except Exception as exc:
        LOGGER.exception("broadcast_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_safe_detail(f"Broadcast failed: {exc.__class__.__name__}"),
        ) from exc

    return BroadcastResponse(
        simulated=result.get("simulated", False),
        portal_published=result.get("portal_published", 0),
        whatsapp_sent=result.get("whatsapp_sent", 0),
        failures=result.get("failures", 0),
        failure_list=[
            BroadcastFailureItem(**f) for f in result.get("failure_list", [])
        ],
        broadcast_job_id=result.get("broadcast_job_id"),
        total_recipients=result.get("total_recipients"),
        existing_current_snapshots=result.get("existing_current_snapshots"),
        channels=result.get("channels"),
        teaching_assignment_id=result.get("teaching_assignment_id"),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/whatsapp/status
# ---------------------------------------------------------------------------


@router.get(
    "/whatsapp/status",
    response_model=WhatsAppStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def whatsapp_status() -> WhatsAppStatusResponse:
    """AC-3: surface the current Evolution instance state."""
    try:
        state = await connection_state()
    except EvolutionApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_safe_detail(f"Evolution API error: {exc.status_code}"),
        ) from exc
    return WhatsAppStatusResponse(
        connected=state.get("connected", False),
        instance_name=state.get("instance_name", "whatsapp-instance"),
        simulated=state.get("simulated", False),
    )


# ---------------------------------------------------------------------------
# POST /api/v1/whatsapp/instance/create
# ---------------------------------------------------------------------------


@router.post(
    "/whatsapp/instance/create",
    response_model=WhatsAppInstanceCreateResponse,
    status_code=status.HTTP_200_OK,
)
async def whatsapp_instance_create() -> WhatsAppInstanceCreateResponse:
    """AC-4: provision a new Evolution instance (or simulate it)."""
    try:
        result = await create_instance()
    except EvolutionApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_safe_detail(f"Evolution API error: {exc.status_code}"),
        ) from exc
    return WhatsAppInstanceCreateResponse(
        instance_name=result.get("instance_name", "whatsapp-instance"),
        status=result.get("status", "simulated"),
        simulated=result.get("simulated", False),
    )


# ---------------------------------------------------------------------------
# GET /api/v1/whatsapp/instance/connect
# ---------------------------------------------------------------------------


@router.get(
    "/whatsapp/instance/connect",
    response_model=WhatsAppConnectResponse,
    status_code=status.HTTP_200_OK,
)
async def whatsapp_instance_connect() -> WhatsAppConnectResponse:
    """AC-4: return the current pairing QR (or simulated sentinel)."""
    try:
        result = await get_qrcode()
    except EvolutionApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_safe_detail(f"Evolution API error: {exc.status_code}"),
        ) from exc
    return WhatsAppConnectResponse(
        instance_name=result.get("instance_name", "whatsapp-instance"),
        code=result.get("code"),
        pairing_code=result.get("pairing_code"),
        simulated=result.get("simulated", False),
        connected=False,
    )


# ---------------------------------------------------------------------------
# POST /api/v1/whatsapp/webhook/configure
# ---------------------------------------------------------------------------


@router.post(
    "/whatsapp/webhook/configure",
    response_model=WebhookConfigureResponse,
    status_code=status.HTTP_200_OK,
)
async def whatsapp_webhook_configure(
    payload: WebhookConfigureRequest,
) -> WebhookConfigureResponse:
    """Configure the Evolution webhook URL and default events."""
    try:
        result = await configure_webhook(
            instance=_default_instance(),
            webhook_url=payload.webhook_url,
        )
    except EvolutionApiError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=_safe_detail(f"Evolution API error: {exc.status_code}"),
        ) from exc
    return WebhookConfigureResponse(
        configured=result.get("configured", False),
        url=result.get("url", payload.webhook_url),
    )


__all__ = ["router"]
