"""AI Grade Query Service (Story 6.2).

Provides AI-powered responses to student questions about their grades
using Baidu QianFan ERNIE as the primary provider (free tier).
Legacy support for Claude and OpenAI preserved.

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
from backend.app.services.baidu_provider import AIProvider, BaiduProvider

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
        - 'baidu': Baidu QianFan ERNIE (free tier, default)
        - 'claude': Anthropic Claude (legacy)
        - 'openai': OpenAI GPT (legacy)

        If API key is missing for the configured provider, raises ValueError.
        """
        provider_name = os.getenv("AI_PROVIDER", "baidu").lower()

        if provider_name == "baidu":
            api_key = os.getenv("BAIDU_API_KEY", "")
            if not api_key:
                raise ValueError("BAIDU_API_KEY is required for baidu provider")
            self.provider: AIProvider = BaiduProvider(api_key)
        elif provider_name == "claude":
            api_key = os.getenv("AI_API_KEY", "")
            if not api_key:
                raise ValueError("AI_API_KEY is required for claude provider")
            self.provider = ClaudeProvider(api_key)
        elif provider_name == "openai":
            api_key = os.getenv("AI_API_KEY", "")
            if not api_key:
                raise ValueError("AI_API_KEY is required for openai provider")
            self.provider = OpenAIProvider(api_key)
        else:
            raise ValueError(
                f"Unknown AI_PROVIDER: {provider_name}. Must be 'baidu', 'claude', or 'openai'"
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
            from sqlalchemy import select

            # Query: student's enrollments + contexts + current snapshots
            stmt = select(
                AcademicContext.subject,
                AcademicContext.turma,
                Semester.code.label("semester_code"),
                Semester.name.label("semester_name"),
                PublicationSnapshot.id.label("snapshot_id"),
                PublicationSnapshot.published_score,
                PublicationSnapshot.published_state,
                PublicationSnapshot.published_at,
            ).select_from(ClassEnrollment).join(
                AcademicContext,
                ClassEnrollment.academic_context_id == AcademicContext.id,
            ).join(
                Semester,
                AcademicContext.semester_id == Semester.id,
            ).outerjoin(
                PublicationSnapshot,
                (PublicationSnapshot.student_id == ClassEnrollment.student_id)
                & (PublicationSnapshot.teaching_assignment_id == AcademicContext.id)
                & (PublicationSnapshot.is_current == True),  # noqa: E712
            ).where(
                ClassEnrollment.student_id == student_id
            ).order_by(
                AcademicContext.academic_year.desc(),
                Semester.code.desc(),
                AcademicContext.subject.asc(),
            )

            rows = session.execute(stmt).fetchall()

            # Format grades context
            context_lines = []
            for row in rows:
                if row.snapshot_id:
                    # AC-1: Only include published snapshots
                    score_str = f"{row.published_score:.1f}".rstrip("0").rstrip(".") \
                        if row.published_score is not None else "N/A"
                    published_date = row.published_at.strftime("%Y-%m-%d") \
                        if row.published_at else "Unknown"

                    line = (
                        f"- {row.subject} | "
                        f"Semestre {row.semester_code} | "
                        f"Turma {row.turma} | "
                        f"Nota: {score_str} | "
                        f"Estado: {row.published_state} | "
                        f"Publicado: {published_date}"
                    )
                    context_lines.append(line)
                # AC-3: Do NOT include entries without publication_snapshot

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
