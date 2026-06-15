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
ASK_NUMBER_MSG = (
    "Olá! 👋 Sou o assistente de notas. Para te identificar, envia o teu "
    "*número de estudante* (ex: 2026001)."
)
LINK_OK_MSG = "Registado com sucesso, {name}! ✅ Agora podes perguntar sobre as tuas notas."
LINK_NOT_FOUND_MSG = (
    "Não encontrei o número de estudante *{number}*. Verifica e tenta de novo, "
    "ou fala com o teu professor."
)


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
        lid: str | None = None,
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

        # AC-4: Identify student by phone / saved @lid link / pushName
        student_row = self._identify_student(
            session, normalized_phone, push_name=push_name, lid=lid, request_id=request_id
        )

        # Not identified yet — try the self-registration flow: if the message
        # text is a valid student number, link this @lid to that student.
        if not student_row and lid:
            candidate = "".join(ch for ch in (message_text or "") if ch.isdigit())
            if candidate:
                rec = self._find_student_by_number(session, candidate)
                if rec:
                    self._save_lid_link(session, lid, instance, rec[1])
                    reply = rec[3]
                    if reply:
                        await send_whatsapp_text(
                            instance=instance,
                            phone_number=reply,
                            message=LINK_OK_MSG.format(name=rec[2] or ""),
                            request_id=request_id,
                        )
                    self._log_interaction(session, reply or candidate, rec[0], "linked", request_id)
                    return {
                        "outcome": "linked", "student_id": rec[0], "phone": reply or "",
                        "message_sent": LINK_OK_MSG, "ai_called": False, "timestamp": timestamp,
                    }
                else:
                    # Looks like a number but no match — tell them, if we can reply
                    # (we have no phone here, so this only works once linked). Skip.
                    pass

        if not student_row:
            # Unknown sender. If we have a real phone (non-@lid student) we can
            # ask them to register; with @lid-only we cannot reply yet.
            sent_msg = ASK_NUMBER_MSG
            if normalized_phone:
                await send_whatsapp_text(
                    instance=instance,
                    phone_number=normalized_phone,
                    message=ASK_NUMBER_MSG,
                    request_id=request_id,
                )
            else:
                sent_msg = ""  # could not deliver

            self._log_interaction(session, normalized_phone, None, "unknown_number", request_id)
            return {
                "outcome": "unknown_number", "student_id": None, "phone": normalized_phone,
                "message_sent": sent_msg, "ai_called": False, "timestamp": timestamp,
            }

        student_id, student_number, full_name, is_legacy, reply_phone = student_row
        # Persist the @lid link for instant future recognition
        if lid:
            self._save_lid_link(session, lid, instance, student_number)
        # Use the phone from the matched record as the reply destination
        # (the inbound @lid is not a real phone number).
        normalized_phone = reply_phone or normalized_phone

        # Without a deliverable phone we cannot reply
        if not normalized_phone:
            self._log_interaction(session, "", student_id, "no_reply_phone", request_id)
            return {
                "outcome": "no_reply_phone", "student_id": student_id, "phone": "",
                "message_sent": "", "ai_called": False, "timestamp": timestamp,
            }

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
    def _find_student_by_number(
        session: Session, student_number: str
    ) -> tuple[int, str, str, str] | None:
        """Return (id, student_number, name, reply_phone) for a student number,
        checking ``students`` then ``legacy_students``. None if not found."""
        from sqlalchemy import text

        row = session.execute(
            text("SELECT id, student_number, full_name, phone FROM students WHERE student_number = :sn LIMIT 1"),
            {"sn": student_number},
        ).fetchone()
        if row:
            return (row[0], row[1], row[2], "".join(ch for ch in str(row[3] or "") if ch.isdigit()))
        row = session.execute(
            text("SELECT id, student_number, name, whatsapp FROM legacy_students WHERE student_number = :sn LIMIT 1"),
            {"sn": student_number},
        ).fetchone()
        if row:
            return (row[0], row[1], row[2], "".join(ch for ch in str(row[3] or "") if ch.isdigit()))
        return None

    @staticmethod
    def _get_lid_link(session: Session, lid: str, instance: str | None = None) -> str | None:
        """Return the linked student_number for a @lid, or None.

        The @lid is unique per contact, so we match on it alone (the saved
        row carries the instance, but a given @lid maps to one student)."""
        from sqlalchemy import text
        try:
            row = session.execute(
                text(
                    "SELECT student_number FROM chatbot_lid_links"
                    " WHERE lid = :lid ORDER BY id DESC LIMIT 1"
                ),
                {"lid": lid},
            ).fetchone()
            return row[0] if row else None
        except Exception as exc:
            LOGGER.warning("chatbot_get_lid_link_failed", extra={"error": str(exc), "lid": lid})
            return None

    @staticmethod
    def _save_lid_link(session: Session, lid: str, instance: str | None, student_number: str) -> None:
        """Upsert a @lid -> student_number mapping."""
        from sqlalchemy import text
        try:
            existing = session.execute(
                text("SELECT id FROM chatbot_lid_links WHERE lid = :lid AND instance = :inst LIMIT 1"),
                {"lid": lid, "inst": instance},
            ).fetchone()
            if existing:
                session.execute(
                    text("UPDATE chatbot_lid_links SET student_number = :sn WHERE id = :id"),
                    {"sn": student_number, "id": existing[0]},
                )
            else:
                session.execute(
                    text(
                        "INSERT INTO chatbot_lid_links (lid, instance, student_number, created_at)"
                        " VALUES (:lid, :inst, :sn, :now)"
                    ),
                    {"lid": lid, "inst": instance, "sn": student_number, "now": datetime.now(UTC).replace(tzinfo=None)},
                )
            session.commit()
        except Exception as exc:
            LOGGER.warning("chatbot_save_lid_link_failed", extra={"error": str(exc), "lid": lid})
            session.rollback()

    def _identify_student(
        self,
        session: Session,
        normalized_phone: str,
        push_name: str | None = None,
        lid: str | None = None,
        request_id: str | None = None,
    ) -> tuple[int, str, str, bool, str] | None:
        """Identify student by phone, saved @lid link, or pushName.

        Resolution order:
          1. ``students`` / ``legacy_students`` by phone
          2. saved ``chatbot_lid_links`` (@lid -> student_number)
          3. ``legacy_students`` by normalised pushName (unambiguous match)

        Returns (student_id, student_number, full_name, is_legacy, reply_phone)
        or None.
        """
        try:
            from sqlalchemy import text

            if normalized_phone:
                row = session.execute(
                    text("SELECT id, student_number, full_name, phone FROM students WHERE phone = :phone"),
                    {"phone": normalized_phone},
                ).fetchone()
                if row:
                    return (row[0], row[1], row[2], False, row[3] or normalized_phone)

            legacy_rows = session.execute(
                text("SELECT id, student_number, name, whatsapp FROM legacy_students")
            ).fetchall()

            # 1b. Phone match in legacy (digits only)
            if normalized_phone:
                for lr in legacy_rows:
                    digits = "".join(ch for ch in str(lr[3] or "") if ch.isdigit())
                    if digits and digits == normalized_phone:
                        return (lr[0], lr[1], lr[2], True, digits)

            # 2. Saved @lid link
            if lid:
                linked_number = self._get_lid_link(session, lid, None)
                if linked_number:
                    rec = self._find_student_by_number(session, linked_number)
                    if rec:
                        LOGGER.info(
                            "chatbot_identified_by_lid",
                            extra={"lid": lid, "student_number": rec[1], "request_id": request_id},
                        )
                        return (rec[0], rec[1], rec[2], True, rec[3])

            # 3. pushName match (unambiguous) — convenience for real names
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
                extra={"normalized_phone": normalized_phone, "push_name": push_name, "lid": lid, "request_id": request_id},
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
