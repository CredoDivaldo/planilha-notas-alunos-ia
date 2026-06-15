"""WhatsApp Chatbot endpoints (Stories 6.1, 6.2).

POST /api/v1/chatbot/webhook — Receives messages from Evolution API (Story 6.1).

AC-1: Webhook endpoint secured with X-Webhook-Token header.
AC-2: Invalid token returns 401.
AC-3: Student identified by normalized phone number.
AC-4: Unknown phone logged gracefully, no AI call made.
AC-5: Non-message events ignored (200 OK silently).

POST /api/v1/chatbot/test — Dry-run endpoint for grade query testing (Story 6.2).

AC-6: Professor-only endpoint returning AI response without sending WhatsApp.
"""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.services.ai_chatbot import AIGradeQueryService
from backend.app.services.chatbot_pipeline import ChatbotPipeline
from backend.app.services.chatbot_rate_limiter import ChatbotRateLimiter
from backend.app.utils.phone import normalize_phone

LOGGER = logging.getLogger("backend.chatbot.routes")

router = APIRouter(prefix="/api/v1/chatbot", tags=["chatbot"])

# Global chatbot pipeline and rate limiter (for Story 6.3)
_chatbot_pipeline: ChatbotPipeline | None = None
_rate_limiter: ChatbotRateLimiter | None = None


def get_chatbot_pipeline(request: Request) -> ChatbotPipeline:
    """Get or create the global chatbot pipeline.

    Args:
        request: FastAPI request object

    Returns:
        ChatbotPipeline instance
    """
    global _chatbot_pipeline, _rate_limiter

    if _chatbot_pipeline is None:
        # Get rate limit config from settings
        settings = request.app.state.settings
        daily_limit = getattr(settings, "chatbot_rate_limit_daily", 10)

        _rate_limiter = ChatbotRateLimiter(daily_limit=daily_limit)
        _chatbot_pipeline = ChatbotPipeline(rate_limiter=_rate_limiter)

    return _chatbot_pipeline


# -----------------------------------------------------------------------
# Request/Response Models
# -----------------------------------------------------------------------


class WebhookKeyData(BaseModel):
    """Evolution API message key."""

    model_config = ConfigDict(extra="allow")  # Allow additional fields
    remoteJid: str = Field(..., description="Sender phone + @s.whatsapp.net")
    fromMe: bool = Field(default=False)
    id: str = Field(...)


class WebhookMessageData(BaseModel):
    """Evolution API message content."""

    model_config = ConfigDict(extra="allow")

    conversation: str | None = Field(default=None, description="Text message content")


class WebhookDataPayload(BaseModel):
    """Evolution API webhook data payload."""

    model_config = ConfigDict(extra="allow")

    key: WebhookKeyData
    message: WebhookMessageData | None = Field(default=None)
    messageType: str | None = Field(default=None)


class WebhookPayload(BaseModel):
    """Evolution API webhook payload structure."""

    model_config = ConfigDict(extra="allow")

    event: str = Field(..., description="Event type (e.g., 'messages.upsert')")
    instance: str = Field(...)
    data: WebhookDataPayload


class WebhookResponse(BaseModel):
    """Success response."""

    status: str
    message: str
    request_id: str | None = None


class TestChatbotRequest(BaseModel):
    """Dry-run endpoint request (Story 6.2)."""

    student_number: str = Field(
        ..., description="Student number to query grades for"
    )
    message: str = Field(..., description="Student's question about grades")


class TestChatbotResponse(BaseModel):
    """Dry-run endpoint response (Story 6.2)."""

    status: str
    student_number: str
    ai_response: str
    grades_context: str
    ai_provider_called: bool
    request_id: str | None = None


# -----------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------


async def validate_webhook_token(request: Request) -> str:
    """Validate X-Webhook-Token header.

    AC-2: Missing or incorrect token returns 401.

    Args:
        request: FastAPI request object

    Returns:
        The token if valid

    Raises:
        HTTPException: 401 if token missing or incorrect
    """
    settings = request.app.state.settings
    # Accept token from header OR query param (Evolution API cannot set custom headers)
    provided_token = (
        request.headers.get("X-Webhook-Token")
        or request.query_params.get("token")
    )

    if not provided_token:
        LOGGER.warning(
            "webhook_auth_failed",
            extra={
                "reason": "missing_token",
                "remote_addr": request.client.host if request.client else "unknown",
            },
        )
        raise HTTPException(status_code=401, detail="Missing X-Webhook-Token header")

    # Get expected token from settings/env (will be set via config)
    expected_token = getattr(settings, "chatbot_webhook_token", None)
    if not expected_token:
        LOGGER.error(
            "webhook_config_error",
            extra={"reason": "CHATBOT_WEBHOOK_TOKEN not configured"},
        )
        raise HTTPException(status_code=500, detail="Webhook not configured")

    if provided_token != expected_token:
        LOGGER.warning(
            "webhook_auth_failed",
            extra={
                "reason": "invalid_token",
                "remote_addr": request.client.host if request.client else "unknown",
            },
        )
        raise HTTPException(status_code=401, detail="Invalid X-Webhook-Token")

    return provided_token


def get_db_session(request: Request) -> Session:
    """Get database session from app state.

    Args:
        request: FastAPI request object

    Returns:
        SQLAlchemy Session
    """
    SessionLocal = request.app.state.session_factory
    return SessionLocal()


# -----------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------


@router.post("/webhook", response_model=WebhookResponse)
async def receive_webhook(
    request: Request,
    token: str = Depends(validate_webhook_token),
) -> WebhookResponse:
    """Receive message webhook from Evolution API.

    AC-5: Non-message events return 200 silently.
    AC-1: Valid token → 200 OK immediately.
    AC-3: Student lookup by normalized phone.
    AC-4: Unknown phone → logged, no AI call.

    Args:
        request: FastAPI request object
        token: Validated webhook token

    Returns:
        WebhookResponse with 200 status
    """
    request_id = getattr(request.state, "request_id", None)

    # Parse raw JSON to handle flexible/malformed payloads
    try:
        payload_data = await request.json()
    except Exception as exc:
        LOGGER.warning(
            "webhook_json_parse_failed",
            extra={
                "error": str(exc),
                "request_id": request_id,
            },
        )
        return WebhookResponse(
            status="ok",
            message="Invalid JSON ignored",
            request_id=request_id,
        )

    # AC-5: Ignore non-message events silently
    event = payload_data.get("event")
    if event != "messages.upsert":
        LOGGER.debug(
            "webhook_event_ignored",
            extra={
                "event": event,
                "request_id": request_id,
            },
        )
        return WebhookResponse(
            status="ok",
            message="Event processed",
            request_id=request_id,
        )

    # Extract sender phone from remoteJid
    data = payload_data.get("data", {})
    key = data.get("key", {})
    message = data.get("message", {})

    if not key:
        LOGGER.warning(
            "webhook_malformed_payload",
            extra={
                "reason": "missing_key_data",
                "request_id": request_id,
            },
        )
        return WebhookResponse(
            status="ok",
            message="Malformed payload ignored",
            request_id=request_id,
        )

    remote_jid = key.get("remoteJid", "")

    # AC-5: Ignore non-text messages silently
    message_type = data.get("messageType")
    if message_type != "conversation" or not message.get("conversation"):
        LOGGER.debug(
            "webhook_non_text_message",
            extra={
                "remote_jid": remote_jid,
                "message_type": message_type,
                "request_id": request_id,
            },
        )
        return WebhookResponse(
            status="ok",
            message="Non-text message ignored",
            request_id=request_id,
        )

    # Modern WhatsApp may send remoteJid as "<id>@lid" (Linked ID), which is
    # NOT the phone number. Try several fields Evolution exposes for the real
    # phone number, in priority order.
    phone_candidates = [
        key.get("senderPn"),
        key.get("senderPhoneNumber"),
        data.get("senderPn"),
        key.get("participantPn"),
        key.get("participant"),
        remote_jid,
    ]
    # Log the raw shape so we can see exactly what Evolution sends
    LOGGER.warning(
        "webhook_phone_extraction remoteJid=%s pushName=%r senderPn=%s candidates=%s",
        remote_jid,
        data.get("pushName"),
        key.get("senderPn"),
        [c for c in phone_candidates if c],
    )

    # AC-3: Normalize phone — pick the first candidate that is NOT a @lid id
    normalized_phone = ""
    for cand in phone_candidates:
        if not cand:
            continue
        if "@lid" in str(cand):
            continue  # skip Linked-ID, not a real phone
        normalized_phone = normalize_phone(str(cand))
        if normalized_phone:
            break

    # WhatsApp pushName — used to identify the student when the inbound JID
    # is a @lid and no real phone number is present in the payload.
    push_name = data.get("pushName") or ""

    if not normalized_phone and not push_name:
        LOGGER.warning(
            "webhook_invalid_phone",
            extra={
                "remote_jid": remote_jid,
                "request_id": request_id,
            },
        )
        return WebhookResponse(
            status="ok",
            message="Invalid phone format",
            request_id=request_id,
        )

    # Get database session
    session = get_db_session(request)
    try:
        # Identification + self-registration is fully handled by the pipeline
        # (by phone, saved @lid link, pushName, or the student sending their
        # student number). We only need a usable identifier to proceed.
        if not normalized_phone and not push_name and "@lid" not in str(remote_jid):
            LOGGER.warning(
                "webhook_no_identifier",
                extra={"remote_jid": remote_jid, "request_id": request_id},
            )
            return WebhookResponse(
                status="ok",
                message="Message received",
                request_id=request_id,
            )

        message_text = message.get("conversation", "")

        # Story 6.3: Full pipeline (identify → rate limit → AI → send)
        # TODO: In production, this should be queued to a background task (Celery/RQ)
        # For now, we'll try to process inline if AI provider is available

        try:
            pipeline = get_chatbot_pipeline(request)
            instance = payload_data.get("instance", "default")

            # AC-1 through AC-6: Process message end-to-end
            result = await pipeline.process_message(
                session,
                normalized_phone,
                message_text,
                instance=instance,
                request_id=request_id,
                push_name=push_name,
                lid=remote_jid if "@lid" in str(remote_jid) else None,
            )

            LOGGER.warning(
                "webhook_pipeline_result outcome=%s student_id=%s ai_called=%s push_name=%r reply_phone=%s",
                result["outcome"],
                result["student_id"],
                result["ai_called"],
                push_name,
                result.get("phone"),
            )

        except ValueError as exc:
            # AI provider not configured (Story 6.3 incomplete)
            if "ANTHROPIC_API_KEY" in str(exc) or "OPENAI_API_KEY" in str(exc):
                LOGGER.warning(
                    "webhook_ai_provider_not_configured",
                    extra={
                        "normalized_phone": normalized_phone,
                        "error": str(exc),
                        "request_id": request_id,
                    },
                )
            else:
                raise

        except Exception as exc:
            LOGGER.error(
                "webhook_pipeline_error",
                extra={
                    "normalized_phone": normalized_phone,
                    "error": str(exc),
                    "request_id": request_id,
                },
            )

        return WebhookResponse(
            status="ok",
            message="Message received and processed",
            request_id=request_id,
        )

    finally:
        session.close()


@router.post("/test", response_model=TestChatbotResponse)
async def test_chatbot(
    request: Request,
    payload: TestChatbotRequest,
    token: str = Depends(validate_webhook_token),
) -> TestChatbotResponse:
    """Dry-run endpoint for AI grade query service (Story 6.2).

    AC-6: Professor-only endpoint returning AI response without sending WhatsApp.

    Args:
        request: FastAPI request object
        payload: Student number and message
        token: Validated webhook token (serves as access control)

    Returns:
        TestChatbotResponse with AI response and context used
    """
    request_id = getattr(request.state, "request_id", None)

    # Get database session
    session = get_db_session(request)
    try:
        # Look up student by student_number (students first, then legacy)
        is_legacy = False
        student_row = session.execute(
            text("SELECT id, student_number, full_name FROM students WHERE student_number = :sn"),
            {"sn": payload.student_number},
        ).fetchone()
        if not student_row:
            legacy_row = session.execute(
                text("SELECT id, student_number, name FROM legacy_students WHERE student_number = :sn LIMIT 1"),
                {"sn": payload.student_number},
            ).fetchone()
            if legacy_row:
                student_row = legacy_row
                is_legacy = True

        if not student_row:
            LOGGER.warning(
                "test_endpoint_student_not_found",
                extra={
                    "student_number": payload.student_number,
                    "request_id": request_id,
                },
            )
            raise HTTPException(
                status_code=404,
                detail=f"Student {payload.student_number} not found",
            )

        student_id, student_number, _full_name = student_row

        # Initialize AI service (surface config errors clearly)
        try:
            ai_service = AIGradeQueryService()
        except ValueError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"AI provider não configurado: {exc}",
            ) from exc

        # Generate AI response with grade context
        result = ai_service.generate_grade_response(
            session,
            student_id,
            student_number,
            payload.message,
            request_id=request_id,
            is_legacy=is_legacy,
        )

        LOGGER.info(
            "test_endpoint_success",
            extra={
                "student_id": student_id,
                "student_number": student_number,
                "ai_called": result["ai_called"],
                "response_length": len(result["response"]),
                "request_id": request_id,
            },
        )

        return TestChatbotResponse(
            status="ok",
            student_number=student_number,
            ai_response=result["response"],
            grades_context=result["grades_context"],
            ai_provider_called=result["ai_called"],
            request_id=request_id,
        )

    finally:
        session.close()
