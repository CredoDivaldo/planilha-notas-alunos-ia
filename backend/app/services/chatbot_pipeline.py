"""Pipeline (linha de montagem) do chatbot — junta todos os passos por ordem.

PT: Este ficheiro coordena ("orquestra") tudo o que acontece quando chega uma
mensagem, passo a passo:
  1. Identificar o aluno (pelo telefone, por um registo guardado, ou pelo nome).
  2. Verificar o limite diário de mensagens.
  3. Pedir ao serviço de IA a resposta com base nas notas.
  4. Tratar falhas sem rebentar.
  5. Enviar a resposta de volta pelo WhatsApp.
  6. Registar a interacção.
Cada passo está numa função/serviço próprio; aqui é só a sequência.

End-to-end chatbot pipeline (Story 6.3).

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


def _norm_name(name: str) -> str:
    """Strip diacritics + lowercase + trim, for pushName matching."""
    import re
    import unicodedata

    decomposed = unicodedata.normalize("NFD", str(name or ""))
    no_accents = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", no_accents).lower().strip()

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
        # Recebe (ou cria) o limitador e o serviço de IA. Poder passá-los de fora
        # facilita os testes (injecção de dependências).
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

        # PASSO 1: identificar de quem é a mensagem.
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
                    # Reply in the same chat thread where the student sent the number
                    # (i.e. back to the @lid JID). Also send to the registered phone
                    # as fallback if different.
                    reply_targets = list(dict.fromkeys(filter(None, [lid, reply])))
                    for rt in reply_targets:
                        try:
                            await send_whatsapp_text(
                                instance=instance,
                                phone_number=rt,
                                message=LINK_OK_MSG.format(name=rec[2] or ""),
                                request_id=request_id,
                            )
                        except Exception:
                            pass
                    self._log_interaction(session, reply or lid or candidate, rec[0], "linked", request_id)
                    return {
                        "outcome": "linked", "student_id": rec[0], "phone": reply or "",
                        "message_sent": LINK_OK_MSG, "ai_called": False, "timestamp": timestamp,
                    }
                else:
                    # Looks like a number but no match — tell them, if we can reply
                    # (we have no phone here, so this only works once linked). Skip.
                    pass

        if not student_row:
            # Unknown sender: prompt them for their student number.
            # If we have a real phone use it; otherwise fall back to the full @lid
            # JID (Evolution API routes messages to @lid contacts via the JID directly).
            sent_msg = ASK_NUMBER_MSG
            reply_target = normalized_phone or lid
            if reply_target:
                try:
                    await send_whatsapp_text(
                        instance=instance,
                        phone_number=reply_target,
                        message=ASK_NUMBER_MSG,
                        request_id=request_id,
                    )
                except Exception as exc:
                    LOGGER.warning(
                        "chatbot_ask_number_send_failed",
                        extra={"reply_target": reply_target, "error": str(exc), "request_id": request_id},
                    )
                    sent_msg = ""
            else:
                sent_msg = ""  # could not deliver

            self._log_interaction(session, normalized_phone, None, "unknown_number", request_id)
            return {
                "outcome": "unknown_number", "student_id": None, "phone": normalized_phone,
                "message_sent": sent_msg, "ai_called": False, "timestamp": timestamp,
            }

        student_id, student_number, full_name, reply_phone = student_row
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

        # PASSO 2: verificar o limite diário. Se excedido, avisa e termina aqui.
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

        # PASSO 3: pedir à IA a resposta com base nas notas do aluno.
        ai_result = self.ai_service.generate_grade_response(
            session, student_id, student_number, message_text,
            request_id=request_id,
        )

        response_message = ai_result["response"]
        ai_called = ai_result["ai_called"]
        outcome = "success" if ai_called else "no_grades"

        # AC-3: Handle AI failures (already handled in ai_service, but track outcome)
        if not ai_called:
            # No grades published or AI failed
            if response_message == AI_FAILURE_MSG:
                outcome = "ai_failure"

        # Conta esta mensagem para o limite diário.
        self.rate_limiter.record(normalized_phone)

        # PASSO 4: enviar a resposta de volta pelo WhatsApp.
        await send_whatsapp_text(
            instance=instance,
            phone_number=normalized_phone,
            message=response_message,
            request_id=request_id,
        )

        # PASSO 5: registar a interacção (para auditoria/diagnóstico).
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
        """Return (id, student_number, name, reply_phone) from ``students``."""
        from sqlalchemy import text

        row = session.execute(
            text("SELECT id, student_number, full_name, phone FROM students WHERE student_number = :sn LIMIT 1"),
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
    ) -> tuple[int, str, str, str] | None:
        """Identify student by phone, saved @lid link, or pushName.

        Resolution order:
          1. ``students`` by phone (digits compare)
          2. saved ``chatbot_lid_links`` (@lid -> student_number)
          3. ``students`` by normalised pushName (unambiguous match)

        Returns (student_id, student_number, full_name, reply_phone) or None.
        """
        try:
            from sqlalchemy import text

            students = session.execute(
                text("SELECT id, student_number, full_name, phone FROM students")
            ).fetchall()

            # 1. Phone match (digits only)
            if normalized_phone:
                for s in students:
                    digits = "".join(ch for ch in str(s[3] or "") if ch.isdigit())
                    if digits and digits == normalized_phone:
                        return (s[0], s[1], s[2], digits)

            # 2. Saved @lid link
            if lid:
                linked_number = self._get_lid_link(session, lid)
                if linked_number:
                    rec = self._find_student_by_number(session, linked_number)
                    if rec:
                        LOGGER.info(
                            "chatbot_identified_by_lid",
                            extra={"lid": lid, "student_number": rec[1], "request_id": request_id},
                        )
                        return rec

            # 3. pushName match (unambiguous) — convenience for real names
            if push_name:
                target = _norm_name(push_name)
                matches = [s for s in students if target and _norm_name(s[2] or "") == target]
                if len(matches) == 1:
                    s = matches[0]
                    reply = "".join(ch for ch in str(s[3] or "") if ch.isdigit())
                    if reply:
                        LOGGER.info(
                            "chatbot_identified_by_pushname",
                            extra={"push_name": push_name, "student_number": s[1], "request_id": request_id},
                        )
                        return (s[0], s[1], s[2], reply)

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
