"""End-to-end chatbot pipeline (Story 6.3).

Orchestrates the complete flow:
1. Identify student by phone (Story 6.1)
2. Check rate limit (AC-2)
3. Query grades + generate AI response (Story 6.2)
4. Handle failures gracefully (AC-3)
5. Send reply via WhatsApp (AC-1)
6. Log interaction (AC-5)

AC-1: Full flow delivers AI reply via WhatsApp.
AC-2: Rate limiting blocks excessive messages.
AC-3: AI failure does not crash the system.
AC-4: Unknown student receives clear message.
AC-5: Each interaction is logged.
"""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.app.services.ai_chatbot import AIGradeQueryService
from backend.app.services.chatbot_rate_limiter import ChatbotRateLimiter
from backend.app.services.evolution_api_client import send_whatsapp_text
from backend.app.utils.phone import normalize_phone

LOGGER = logging.getLogger("backend.chatbot.pipeline")

# Canned messages (Portuguese)
UNKNOWN_NUMBER_MSG = "O teu número não está registado na plataforma. Fala com o teu professor para registares o teu contacto."
RATE_LIMIT_MSG = "Atingiste o limite de mensagens para hoje. Tenta novamente amanhã."
AI_FAILURE_MSG = "Não foi possível processar o teu pedido agora. Tenta mais tarde."
NO_GRADES_MSG = "Ainda não tens notas publicadas. Aguarda a notificação do teu professor."


class ChatbotPipeline:
    """End-to-end chatbot pipeline (AC-1 through AC-6)."""

    def __init__(
        self,
        rate_limiter: ChatbotRateLimiter | None = None,
        ai_service: AIGradeQueryService | None = None,
    ) -> None:
        """Initialize the chatbot pipeline.

        Args:
            rate_limiter: Optional custom rate limiter (for testing).
                If None, a new instance is created.
            ai_service: Optional custom AI service (for testing).
                If None, a new instance is created.
        """
        self.rate_limiter = rate_limiter or ChatbotRateLimiter()
        self.ai_service = ai_service or AIGradeQueryService()

    async def process_message(
        self,
        session: Session,
        normalized_phone: str,
        message_text: str,
        instance: str = "default",
        *,
        request_id: str | None = None,
        push_name: str | None = None,
    ) -> dict[str, Any]:
        """Process a chatbot message end-to-end.

        Implements the full pipeline:
        1. AC-4: Identify student by phone
        2. AC-2: Check rate limit
        3. Story 6.2: Generate AI response
        4. AC-3: Handle failures
        5. AC-1: Send reply via WhatsApp
        6. AC-5: Log interaction

        Args:
            session: SQLAlchemy session
            normalized_phone: Normalized phone number (e.g., "244912345678")
            message_text: Student's message
            instance: Evolution API instance name
            request_id: Optional correlation ID

        Returns:
            Dict with keys:
                - outcome (str): "success" | "unknown_number" | "rate_limited" | "ai_failure"
                - student_id (int | None): Student ID if identified
                - phone (str): Normalized phone
                - message_sent (str): Message sent to student
                - ai_called (bool): Whether AI was called
                - timestamp (str): ISO timestamp
        """
        timestamp = datetime.now(UTC).isoformat()

        # AC-4: Identify student by phone (or pushName when WhatsApp sends @lid)
        student_row = self._identify_student(
            session, normalized_phone, push_name=push_name, request_id=request_id
        )

        if not student_row:
            # Unknown number: send registration message (only if we have a
            # destination phone — with @lid and no match we can't reply)
            if normalized_phone:
                await send_whatsapp_text(
                    instance=instance,
                    phone_number=normalized_phone,
                    message=UNKNOWN_NUMBER_MSG,
                    request_id=request_id,
                )

            outcome_dict = {
                "outcome": "unknown_number",
                "student_id": None,
                "phone": normalized_phone,
                "message_sent": UNKNOWN_NUMBER_MSG,
                "ai_called": False,
                "timestamp": timestamp,
            }

            self._log_interaction(session, normalized_phone, None, "unknown_number", request_id)
            return outcome_dict

        student_id, student_number, full_name, is_legacy, reply_phone = student_row
        # Use the phone from the matched record as the reply destination
        # (the inbound @lid is not a real phone number).
        normalized_phone = reply_phone or normalized_phone

        # AC-2: Check rate limit
        if self.rate_limiter.is_blocked(normalized_phone):
            # Rate limit reached: send limit message
            await send_whatsapp_text(
                instance=instance,
                phone_number=normalized_phone,
                message=RATE_LIMIT_MSG,
                request_id=request_id,
            )

            outcome_dict = {
                "outcome": "rate_limited",
                "student_id": student_id,
                "phone": normalized_phone,
                "message_sent": RATE_LIMIT_MSG,
                "ai_called": False,
                "timestamp": timestamp,
            }

            self._log_interaction(
                session, normalized_phone, student_id, "rate_limited", request_id
            )
            return outcome_dict

        # Story 6.2: Generate AI response
        ai_result = self.ai_service.generate_grade_response(
            session, student_id, student_number, message_text,
            request_id=request_id, is_legacy=is_legacy,
        )

        response_message = ai_result["response"]
        ai_called = ai_result["ai_called"]
        outcome = "success" if ai_called else "no_grades"

        # AC-3: Handle AI failures (already handled in ai_service, but track outcome)
        if not ai_called:
            # No grades published or AI failed
            if response_message == AI_FAILURE_MSG:
                outcome = "ai_failure"

        # Record rate limit for next message
        self.rate_limiter.record(normalized_phone)

        # AC-1: Send reply via WhatsApp
        await send_whatsapp_text(
            instance=instance,
            phone_number=normalized_phone,
            message=response_message,
            request_id=request_id,
        )

        # AC-5: Log interaction
        self._log_interaction(
            session, normalized_phone, student_id, outcome, request_id, ai_called
        )

        outcome_dict = {
            "outcome": outcome,
            "student_id": student_id,
            "phone": normalized_phone,
            "message_sent": response_message,
            "ai_called": ai_called,
            "timestamp": timestamp,
        }

        LOGGER.info(
            "chatbot_pipeline_complete",
            extra={
                "student_id": student_id,
                "outcome": outcome,
                "ai_called": ai_called,
                "request_id": request_id,
            },
        )

        return outcome_dict

    @staticmethod
    def _identify_student(
        session: Session,
        normalized_phone: str,
        push_name: str | None = None,
        request_id: str | None = None,
    ) -> tuple[int, str, str, bool, str] | None:
        """Identify student by phone, or by WhatsApp pushName when the
        inbound JID is a @lid (Linked ID) with no real phone number.

        Resolution order:
          1. ``students`` table by phone
          2. ``legacy_students`` by phone (digits-only compare)
          3. ``legacy_students`` by normalised pushName (unambiguous match)

        Returns:
            (student_id, student_number, full_name, is_legacy, reply_phone)
            where ``reply_phone`` is the destination number to answer on,
            taken from the matched record. None if not identified.
        """
        try:
            from sqlalchemy import text

            if normalized_phone:
                row = session.execute(
                    text(
                        "SELECT id, student_number, full_name, phone FROM students WHERE phone = :phone"
                    ),
                    {"phone": normalized_phone},
                ).fetchone()
                if row:
                    return (row[0], row[1], row[2], False, row[3] or normalized_phone)

            legacy_rows = session.execute(
                text(
                    "SELECT id, student_number, name, whatsapp FROM legacy_students"
                )
            ).fetchall()

            # 2. Phone match (digits only)
            if normalized_phone:
                for lr in legacy_rows:
                    digits = "".join(ch for ch in str(lr[3] or "") if ch.isdigit())
                    if digits and digits == normalized_phone:
                        return (lr[0], lr[1], lr[2], True, digits)

            # 3. pushName match (for the @lid case). Requires an unambiguous,
            # single name match with a usable reply phone on record.
            if push_name:
                from backend.app.services.legacy_import import normalize_name

                target = normalize_name(push_name)
                matches = [
                    lr for lr in legacy_rows
                    if target and normalize_name(lr[2] or "") == target
                ]
                if len(matches) == 1:
                    lr = matches[0]
                    reply = "".join(ch for ch in str(lr[3] or "") if ch.isdigit())
                    if reply:
                        LOGGER.info(
                            "chatbot_identified_by_pushname",
                            extra={"push_name": push_name, "student_number": lr[1], "request_id": request_id},
                        )
                        return (lr[0], lr[1], lr[2], True, reply)

            LOGGER.debug(
                "chatbot_student_not_found",
                extra={"normalized_phone": normalized_phone, "push_name": push_name, "request_id": request_id},
            )
            return None

        except Exception as exc:
            LOGGER.error(
                "chatbot_student_lookup_error",
                extra={
                    "normalized_phone": normalized_phone,
                    "error": str(exc),
                    "request_id": request_id,
                },
            )
            return None

    @staticmethod
    def _log_interaction(
        session: Session,
        normalized_phone: str,
        student_id: int | None,
        outcome: str,
        request_id: str | None = None,
        ai_called: bool = False,
    ) -> None:
        """Log a chatbot interaction.

        AC-5: Log timestamp, phone, outcome, student ID, and whether AI was called.

        Args:
            session: SQLAlchemy session
            normalized_phone: Normalized phone number
            student_id: Student ID if identified
            outcome: Outcome type ("success", "unknown_number", "rate_limited", etc.)
            request_id: Optional correlation ID
            ai_called: Whether AI was called
        """
        try:
            from sqlalchemy import text

            timestamp = datetime.now(UTC).isoformat()

            # Insert into chatbot_interactions table (if it exists)
            # For now, we'll just log structurally
            LOGGER.info(
                "chatbot_interaction_logged",
                extra={
                    "normalized_phone": normalized_phone,
                    "student_id": student_id,
                    "outcome": outcome,
                    "ai_called": ai_called,
                    "timestamp": timestamp,
                    "request_id": request_id,
                },
            )

        except Exception as exc:
            LOGGER.error(
                "chatbot_interaction_logging_error",
                extra={
                    "normalized_phone": normalized_phone,
                    "student_id": student_id,
                    "error": str(exc),
                    "request_id": request_id,
                },
            )
