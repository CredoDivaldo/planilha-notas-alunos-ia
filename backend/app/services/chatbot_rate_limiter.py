"""Limitador de uso do chatbot (rate limiting).

PT: Impede que um mesmo número de telefone faça demasiadas perguntas por dia
(por defeito 10). Guarda em memória, num dicionário, quantas mensagens cada número
já enviou hoje; à meia-noite (UTC) o contador "reinicia-se" naturalmente porque a
data muda. É simples e suficiente para um MVP (perde-se ao reiniciar o servidor).

Implements daily rate limiting keyed by normalized phone number.
AC-2: Blocks excessive messages (configurable daily limit).

This is an in-memory rate limiter suitable for MVP deployments.
It resets daily at UTC midnight.

Usage:
    limiter = ChatbotRateLimiter(daily_limit=10)
    if limiter.is_blocked(normalized_phone):
        # Send rate limit message
    else:
        # Process message
        limiter.record(normalized_phone)
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime

LOGGER = logging.getLogger("backend.chatbot.rate_limiter")


class ChatbotRateLimiter:
    """In-memory rate limiter for chatbot messages."""

    def __init__(self, daily_limit: int = 10) -> None:
        """Initialize the rate limiter.

        Args:
            daily_limit: Maximum messages per day per phone number (default: 10)
        """
        self.daily_limit = daily_limit
        # Dicionário onde se guarda, por número, quantas mensagens enviou e em que dia:
        # {telefone: {"count": nº, "date": "AAAA-MM-DD"}}
        self._counters: dict[str, dict] = {}

    def _get_date_key(self) -> str:
        """Get today's date in YYYY-MM-DD format (UTC).

        Returns:
            Date string in YYYY-MM-DD format
        """
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def is_blocked(self, normalized_phone: str) -> bool:
        """Check if a phone number has exceeded the daily limit.

        AC-2: Returns True if the phone has already sent >= daily_limit messages today.

        Args:
            normalized_phone: Normalized phone number (e.g., "244912345678")

        Returns:
            True if blocked (limit reached or exceeded), False otherwise
        """
        if not normalized_phone or normalized_phone not in self._counters:
            return False

        entry = self._counters[normalized_phone]
        today = self._get_date_key()

        # Se o último registo é de outro dia, hoje ainda não enviou nada → não bloqueado.
        if entry.get("date") != today:
            return False

        # Bloqueado se já atingiu (ou passou) o limite diário.
        count = entry.get("count", 0)
        blocked = count >= self.daily_limit

        if blocked:
            LOGGER.info(
                "chatbot_rate_limit_blocked",
                extra={
                    "normalized_phone": normalized_phone,
                    "count": count,
                    "daily_limit": self.daily_limit,
                    "date": today,
                },
            )

        return blocked

    def record(self, normalized_phone: str) -> None:
        """Record a message from a phone number.

        AC-2: Increments daily counter for this phone. Resets on date change.

        Args:
            normalized_phone: Normalized phone number
        """
        if not normalized_phone:
            return

        today = self._get_date_key()

        if normalized_phone not in self._counters:
            self._counters[normalized_phone] = {"count": 0, "date": today}

        entry = self._counters[normalized_phone]

        # Reset if date has changed
        if entry.get("date") != today:
            entry["count"] = 0
            entry["date"] = today

        # Increment counter
        entry["count"] += 1

        LOGGER.debug(
            "chatbot_rate_limit_recorded",
            extra={
                "normalized_phone": normalized_phone,
                "count": entry["count"],
                "daily_limit": self.daily_limit,
                "date": today,
            },
        )

    def get_count(self, normalized_phone: str) -> int:
        """Get current message count for a phone number (for testing).

        Args:
            normalized_phone: Normalized phone number

        Returns:
            Current message count for today (0 if not found or date mismatch)
        """
        if not normalized_phone or normalized_phone not in self._counters:
            return 0

        entry = self._counters[normalized_phone]
        today = self._get_date_key()

        if entry.get("date") != today:
            return 0

        return entry.get("count", 0)

    def reset(self) -> None:
        """Reset all counters (for testing).

        Args:
            None

        Returns:
            None
        """
        self._counters.clear()
        LOGGER.debug("chatbot_rate_limit_reset")
