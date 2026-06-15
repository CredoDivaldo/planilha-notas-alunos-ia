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
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.publication.service import compute_match, trigger_broadcast
from backend.app.services.evolution_api_client import (
    EvolutionApiError,
    _default_instance,
    configure_webhook,
    connection_state,
    create_instance,
    get_qrcode,
    send_whatsapp_text,
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

    context_id: int | None = Field(None, description="Academic context identifier")

    @field_validator("context_id", mode="before")
    @classmethod
    def _coerce_empty_string(cls, v: object) -> object:
        if v == "" or v is None:
            return None
        return v
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


def _nota_str(nota_final: float) -> str:
    return str(int(nota_final)) if nota_final == int(nota_final) else str(nota_final)


async def _normalized_broadcast(
    session: Any,
    context_id: int,
    teaching_assignment_id: int,
    dry_run: bool,
    message_template: str | None,
    instance_name: str | None,
    audience: Any,
    channels: list[str],
    actor_user_id: int | None,
) -> dict[str, Any]:
    """Publish grades using the normalized model.

    Computes each enrolled student's weighted final grade from
    ``grade_entries`` + ``assessment_definitions``, creates
    ``publication_snapshots`` (portal visibility), and sends one WhatsApp
    message per recipient with placeholders substituted.
    """
    from sqlalchemy import text as _text

    from backend.app.publication.service import PublicationService
    from backend.app.services.message_templates import render_message_template

    # Context info: disciplina, semester name
    ctx_row = session.execute(
        _text("SELECT subject, semester_id FROM academic_contexts WHERE id = :cid LIMIT 1"),
        {"cid": context_id},
    ).fetchone()
    disciplina = (ctx_row[0] if ctx_row else "") or ""
    semestre = ""
    if ctx_row and ctx_row[1]:
        sem_row = session.execute(
            _text("SELECT name FROM semesters WHERE id = :sid LIMIT 1"),
            {"sid": ctx_row[1]},
        ).fetchone()
        semestre = (sem_row[0] if sem_row else "") or ""

    # Components and weights
    ad_rows = session.execute(
        _text(
            "SELECT id, weight FROM assessment_definitions"
            " WHERE teaching_assignment_id = :ta ORDER BY sort_order, id"
        ),
        {"ta": teaching_assignment_id},
    ).fetchall()
    comp_ids = [r[0] for r in ad_rows]
    weights = {r[0]: float(r[1] or 0) for r in ad_rows}

    # Enrolled students
    students = session.execute(
        _text(
            "SELECT s.id, s.student_number, s.full_name, s.phone"
            " FROM class_enrollments ce JOIN students s ON s.id = ce.student_id"
            " WHERE ce.academic_context_id = :cid"
            "   AND (ce.enrollment_status IS NULL OR ce.enrollment_status = 'active')"
            " ORDER BY s.student_number"
        ),
        {"cid": context_id},
    ).fetchall()

    instance = instance_name or _default_instance()
    audience_list = audience if isinstance(audience, list) else None
    sent = 0
    failures: list[dict] = []
    recipients = 0
    grade_data: list[dict] = []

    for sid, snum, sname, sphone in students:
        grows = session.execute(
            _text(
                "SELECT assessment_definition_id, raw_value FROM grade_entries"
                " WHERE student_id = :s AND teaching_assignment_id = :ta"
            ),
            {"s": sid, "ta": teaching_assignment_id},
        ).fetchall()
        vals = {adid: (float(v) if v is not None else None) for adid, v in grows}
        # Only complete students (all components present) are published
        if not comp_ids or any(vals.get(cid) is None for cid in comp_ids):
            continue
        total = sum(vals[cid] * weights[cid] / 100 for cid in comp_ids)
        nota_final = round(total * 10) / 10
        approved = nota_final >= 10

        # Audience filter
        if audience == "approved" and not approved:
            continue
        if audience == "rejected" and approved:
            continue
        if audience_list is not None and str(sid) not in audience_list and (snum or "") not in audience_list:
            continue

        recipients += 1
        grade_data.append({
            "student_id": sid,
            "published_score": nota_final,
            "published_state": "approved" if approved else "rejected",
            "payload": {"value": nota_final, "whatsapp": sphone},
        })

        if dry_run or "whatsapp" not in channels:
            continue
        if not sphone:
            failures.append({
                "student_id": str(sid), "student_name": sname or "",
                "student_number": snum or "", "reason": "Sem número WhatsApp cadastrado",
            })
            continue
        msg = render_message_template(
            message_template,
            nome=sname or "", disciplina=disciplina, semestre=semestre,
            nota=_nota_str(nota_final), resultado="Aprovado" if approved else "Reprovado",
            numero=snum or "",
        )
        try:
            await send_whatsapp_text(instance, sphone, msg)
            sent += 1
        except Exception as exc:
            LOGGER.warning("broadcast_send_failed", extra={"error": str(exc), "student": snum})
            failures.append({
                "student_id": str(sid), "student_name": sname or "",
                "student_number": snum or "", "reason": str(exc)[:200],
            })

    # Publish snapshots (portal visibility) — real runs only
    portal_published = 0
    if not dry_run and grade_data:
        svc = PublicationService()
        job = svc.create_broadcast_job(
            session,
            teaching_assignment_id=teaching_assignment_id,
            actor_user_id=actor_user_id or 1,
            job_type="grade_publication",
            channels=channels,
        )
        svc.create_publication_snapshots(session, job, grade_data)
        session.commit()
        portal_published = len(grade_data)

    return {
        "simulated": dry_run,
        "portal_published": portal_published,
        "whatsapp_sent": sent,
        "failures": len(failures),
        "failure_list": failures,
        "total_recipients": recipients,
    }


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

    # Extract authenticated professor's user_id and WhatsApp instance via raw engine
    _prof_user_id: int | None = None
    _prof_instance: str | None = None
    try:
        from datetime import UTC, datetime
        from sqlalchemy import text as _text
        _engine = getattr(request.app.state, "engine", None)
        if _engine:
            _auth = request.headers.get("authorization", "")
            _sid = _auth.removeprefix("Bearer ").strip() if _auth.startswith("Bearer ") else None
            if _sid:
                _now = datetime.now(UTC).replace(tzinfo=None)
                with _engine.connect() as _conn:
                    _row = _conn.execute(
                        _text("SELECT user_id FROM user_sessions WHERE id = :sid AND is_active = true AND expires_at > :now LIMIT 1"),
                        {"sid": _sid, "now": _now},
                    ).fetchone()
                    if _row:
                        _prof_user_id = int(_row[0])
                        _inst_row = _conn.execute(
                            _text("SELECT whatsapp_instance FROM users WHERE id = :uid LIMIT 1"),
                            {"uid": _prof_user_id},
                        ).fetchone()
                        # Use DB value if present, otherwise deterministic fallback (same logic as _get_professor_instance)
                        _prof_instance = (_inst_row[0] if _inst_row and _inst_row[0] else None) or f"prof-{_prof_user_id}"
    except Exception:
        pass

    # Resolve the teaching assignment from the academic context (1:1 link)
    teaching_assignment_id = payload.teaching_assignment_id
    if teaching_assignment_id is None and payload.context_id is not None:
        from sqlalchemy import text as _t
        _r = session.execute(
            _t("SELECT teaching_assignment_id FROM academic_contexts WHERE id = :cid LIMIT 1"),
            {"cid": payload.context_id},
        ).fetchone()
        teaching_assignment_id = _r[0] if _r and _r[0] else None

    if teaching_assignment_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum contexto selecionado. Selecione um contexto académico antes de disparar.",
        )

    try:
        result = await _normalized_broadcast(
            session,
            context_id=payload.context_id,
            teaching_assignment_id=teaching_assignment_id,
            dry_run=dry_run,
            message_template=payload.message_template,
            instance_name=_prof_instance,
            audience=payload.audience,
            channels=payload.channels,
            actor_user_id=_prof_user_id or payload.actor_user_id,
        )
    except Exception as exc:
        LOGGER.exception("broadcast_failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=_safe_detail(f"Broadcast failed: {exc.__class__.__name__}: {exc}"),
        ) from exc

    return BroadcastResponse(
        simulated=result.get("simulated", False),
        portal_published=result.get("portal_published", 0),
        whatsapp_sent=result.get("whatsapp_sent", 0),
        failures=result.get("failures", 0),
        failure_list=[
            BroadcastFailureItem(**f) for f in result.get("failure_list", [])
        ],
        total_recipients=result.get("total_recipients"),
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
