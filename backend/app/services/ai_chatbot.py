"""AI Grade Query Service (Stories 6.2, 9.0).

Provides AI-powered responses to student questions about their grades
using DeepSeek as the primary provider (Story 9.0 switch).
Legacy support for Claude and OpenAI preserved as fallbacks.

AC-1: AI model is called with student grade context.
AC-2: Response is in Portuguese and grade-specific.
AC-3: Unpublished grades are not exposed.
AC-4: Student with no published grades receives graceful response.
AC-5: AI API failure is handled without crashing.
AC-6: Dry-run endpoint returns AI response without sending WhatsApp.
"""
from __future__ import annotations

import html
import logging
import os
import re
from typing import Any

from sqlalchemy.orm import Session

from backend.app.models.contexts import AcademicContext, ClassEnrollment, Semester
from backend.app.models.publication import PublicationSnapshot
from backend.app.services.deepseek_provider import AIProvider, DeepSeekProvider

LOGGER = logging.getLogger("backend.ai_chatbot.service")

# Fallback message for AI API failures
FALLBACK_MESSAGE = "Não foi possível processar o teu pedido agora. Tenta mais tarde."

# Message for students with no published grades
NO_GRADES_MESSAGE = "Não tens notas publicadas ainda. Volta mais tarde para verificar."

# System prompt template (Portuguese)
SYSTEM_PROMPT_TEMPLATE = (
    "És um assistente académico. Responde APENAS com base nos dados de notas"
    " fornecidos abaixo. NÃO inventes notas, estados ou datas que não estejam"
    " nos dados. Responde em Português. Se a pergunta não for sobre notas"
    " académicas, redireciona educadamente.\n\n"
    "Dados publicados do estudante {student_number}:\n"
    "{grades_context}\n\n"
    "Pergunta do estudante: {student_message}"
)


class ClaudeProvider(AIProvider):
    """Claude API provider via Anthropic SDK."""

    def __init__(self, api_key: str) -> None:
        """Initialize Claude provider.

        Args:
            api_key: Anthropic API key

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for claude provider")
        self.api_key = api_key

    def call(self, system_prompt: str, user_message: str) -> str:
        """Call Claude API.

        Args:
            system_prompt: System prompt with grade context
            user_message: User's question (sanitized)

        Returns:
            Claude-generated response

        Raises:
            Exception: If API call fails
        """
        try:
            import anthropic  # type: ignore

            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=os.getenv("AI_MODEL", "claude-haiku-4-5-20251001"),
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
            )

            # Extract text from response
            if response.content and len(response.content) > 0:
                content = response.content[0]
                if hasattr(content, "text"):
                    text: str = content.text
                    # Truncate to 1000 chars if needed
                    return text[:1000] if len(text) > 1000 else text
            return FALLBACK_MESSAGE

        except Exception as exc:
            LOGGER.error(
                "claude_api_error",
                extra={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            raise


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str) -> None:
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for openai provider")
        self.api_key = api_key

    def call(self, system_prompt: str, user_message: str) -> str:
        """Call OpenAI API.

        Args:
            system_prompt: System prompt with grade context
            user_message: User's question (sanitized)

        Returns:
            GPT-generated response

        Raises:
            Exception: If API call fails
        """
        try:
            import openai  # type: ignore

            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=os.getenv("AI_MODEL", "gpt-4o"),
                max_tokens=1000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message,
                    }
                ],
            )

            # Extract text from response
            if response.choices and len(response.choices) > 0:
                text = response.choices[0].message.content or FALLBACK_MESSAGE
                # Truncate to 1000 chars if needed
                return text[:1000] if len(text) > 1000 else text
            return FALLBACK_MESSAGE

        except Exception as exc:
            LOGGER.error(
                "openai_api_error",
                extra={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            raise


class AIGradeQueryService:
    """Service for AI-powered grade query responses."""

    def __init__(self) -> None:
        """Initialize the service and configure AI provider.

        Supports three providers:
        - 'deepseek': DeepSeek Chat (default, primary — Story 9.0)
        - 'claude': Anthropic Claude (legacy fallback)
        - 'openai': OpenAI GPT (legacy fallback)

        If API key is missing for the configured provider, raises ValueError.
        """
        provider_name = os.getenv("AI_PROVIDER", "deepseek").lower()

        if provider_name == "deepseek":
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            if not api_key:
                raise ValueError("DEEPSEEK_API_KEY is required for deepseek provider")
            self.provider: AIProvider = DeepSeekProvider(api_key)
        elif provider_name == "claude":
            api_key = os.getenv("ANTHROPIC_API_KEY", "") or os.getenv("AI_API_KEY", "")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY is required for claude provider")
            self.provider = ClaudeProvider(api_key)
        elif provider_name == "openai":
            api_key = os.getenv("OPENAI_API_KEY", "") or os.getenv("AI_API_KEY", "")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is required for openai provider")
            self.provider = OpenAIProvider(api_key)
        else:
            raise ValueError(
                f"Unknown AI_PROVIDER: {provider_name}. "
                "Must be 'deepseek', 'claude', or 'openai'"
            )

    def generate_grade_response(
        self,
        session: Session,
        student_id: int,
        student_number: str,
        message: str,
        *,
        request_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate AI response to student's grade question.

        AC-1: Fetches published grades and calls AI API.
        AC-2: Response in Portuguese, grade-specific.
        AC-3: Unpublished grades not exposed.
        AC-4: Graceful response if no grades published.
        AC-5: Handles AI API failure gracefully.

        Args:
            session: SQLAlchemy session
            student_id: Student's ID
            student_number: Student's number (for display)
            message: Student's question (sanitized)
            request_id: Optional correlation ID

        Returns:
            {
                "student_id": int,
                "response": str,
                "grades_context": str,
                "ai_called": bool,
                "request_id": str | None,
            }
        """
        # AC-1: Fetch student's published grades (publication_snapshots)
        grades_context = self._fetch_grades_context(
            session, student_id, request_id=request_id
        )

        # AC-4: If no published grades, return graceful message
        if not grades_context or grades_context.strip() == "":
            LOGGER.info(
                "no_published_grades",
                extra={
                    "student_id": student_id,
                    "student_number": student_number,
                    "request_id": request_id,
                },
            )
            return {
                "student_id": student_id,
                "response": NO_GRADES_MESSAGE,
                "grades_context": "",
                "ai_called": False,
                "request_id": request_id,
            }

        # AC-3: Sanitize student message against prompt injection
        sanitized_message = self._sanitize_message(message)

        # Build system prompt with grade context
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            student_number=student_number,
            grades_context=grades_context,
            student_message=sanitized_message,
        )

        # AC-1, AC-2: Call AI API and get response
        try:
            ai_response = self.provider.call(system_prompt, sanitized_message)

            LOGGER.info(
                "ai_response_generated",
                extra={
                    "student_id": student_id,
                    "student_number": student_number,
                    "response_length": len(ai_response),
                    "request_id": request_id,
                },
            )

            return {
                "student_id": student_id,
                "response": ai_response,
                "grades_context": grades_context,
                "ai_called": True,
                "request_id": request_id,
            }

        except Exception as exc:
            # AC-5: Handle AI API failure
            LOGGER.error(
                "ai_api_failure",
                extra={
                    "student_id": student_id,
                    "student_number": student_number,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "request_id": request_id,
                },
            )

            return {
                "student_id": student_id,
                "response": FALLBACK_MESSAGE,
                "grades_context": grades_context,
                "ai_called": False,
                "request_id": request_id,
            }

    def _fetch_grades_context(
        self,
        session: Session,
        student_id: int,
        *,
        request_id: str | None = None,
    ) -> str:
        """Fetch published grades for a student formatted for AI context.

        AC-1: Reads ONLY publication_snapshots WHERE is_current=True.
        AC-3: Never exposes internal grade_entries fields.

        Returns formatted context string like:
        "- Matemática | Semestre 2026-1 | Turma A | Nota: 17 | Estado: Aprovado
        | Publicado: 2026-05-28"
        """
        try:
            from sqlalchemy import text

            # Snapshots → academic_contexts (1:1 via teaching_assignment_id) → semester
            rows = session.execute(
                text(
                    "SELECT ac.subject, ac.turma, sem.name,"
                    "       ps.published_score, ps.published_state, ps.published_at"
                    " FROM publication_snapshots ps"
                    " JOIN academic_contexts ac"
                    "   ON ac.teaching_assignment_id = ps.teaching_assignment_id"
                    " LEFT JOIN semesters sem ON sem.id = ac.semester_id"
                    " WHERE ps.student_id = :sid AND ps.is_current = true"
                    " ORDER BY ac.academic_year DESC, ac.subject ASC"
                ),
                {"sid": student_id},
            ).fetchall()

            context_lines = []
            for subject, turma, sem_name, score, state, pub_at in rows:
                try:
                    score_str = f"{float(score):.1f}".rstrip("0").rstrip(".") if score is not None else "N/A"
                except (TypeError, ValueError):
                    score_str = "N/A"
                estado = {"approved": "Aprovado", "rejected": "Reprovado"}.get(state, state or "")
                context_lines.append(
                    f"- {subject} | Semestre {sem_name or ''} | Turma {turma or ''} |"
                    f" Nota: {score_str} | Estado: {estado}"
                )

            return "\n".join(context_lines) if context_lines else ""

        except Exception as exc:
            LOGGER.error(
                "grades_context_fetch_error",
                extra={
                    "student_id": student_id,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "request_id": request_id,
                },
            )
            return ""

    @staticmethod
    def _sanitize_message(message: str) -> str:
        """Sanitize student message against prompt injection.

        Simple sanitization:
        - Escape HTML entities
        - Limit length to 500 chars
        - Remove control characters
        """
        if not message:
            return ""

        # Escape HTML entities to prevent injection
        sanitized = html.escape(message)

        # Remove control characters
        sanitized = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", sanitized)

        # Limit to 500 characters
        if len(sanitized) > 500:
            sanitized = sanitized[:500]

        return sanitized.strip()
