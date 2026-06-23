"""Provider de IA DeepSeek — adaptador concreto para a API do DeepSeek.

PT: O DeepSeek oferece uma API "compatível com OpenAI", por isso reutilizamos o
cliente `openai` apontando para o endereço do DeepSeek. Aqui está a classe-base
abstracta `AIProvider` (o contrato) e a sua implementação `DeepSeekProvider`.

DeepSeek AI Provider (Story 9.0 — Provider Switch).

Integrates with DeepSeek's chat API via the OpenAI-compatible SDK.
DeepSeek exposes https://api.deepseek.com as an OpenAI-compatible endpoint,
allowing reuse of the `openai` Python client with a custom base_url.

Reference: https://platform.deepseek.com/api-docs/

This replaces the previous Baidu QianFan provider (baidu_provider.py),
which was removed as part of the Epic 9 prep switch.
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any

LOGGER = logging.getLogger("backend.deepseek_provider")


# Classe abstracta (ABC = Abstract Base Class): define o "contrato" comum a todos
# os providers de IA, mas não pode ser usada directamente. Cada provider real (DeepSeek,
# Claude, OpenAI) herda dela e é OBRIGADO a implementar o método `call`.
class AIProvider(ABC):
    """Classe-base abstracta para os providers de IA (define o método obrigatório)."""

    @abstractmethod  # marca o método como obrigatório nas subclasses
    def call(self, system_prompt: str, user_message: str) -> str:
        """Call the AI provider with given prompts.

        Args:
            system_prompt: System prompt with grade context
            user_message: User's question (sanitized)

        Returns:
            AI-generated response

        Raises:
            Exception: If API call fails or key is missing
        """
        raise NotImplementedError


class DeepSeekProvider(AIProvider):
    """DeepSeek API provider via OpenAI-compatible SDK."""

    DEFAULT_BASE_URL = "https://api.deepseek.com"
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(self, api_key: str) -> None:
        """Initialize DeepSeek provider.

        Args:
            api_key: DeepSeek API key (from platform.deepseek.com/api_keys)

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY is required for deepseek provider")
        self.api_key = api_key
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", self.DEFAULT_BASE_URL)
        self.model = os.getenv("AI_MODEL", self.DEFAULT_MODEL)

    def call(self, system_prompt: str, user_message: str) -> str:
        """Call DeepSeek chat completions API.

        Args:
            system_prompt: System prompt with grade context
            user_message: User's question (sanitized)

        Returns:
            DeepSeek-generated response (truncated to 1000 chars)

        Raises:
            Exception: If API call fails
        """
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self.api_key, base_url=self.base_url)

            response: Any = client.chat.completions.create(
                model=self.model,
                max_tokens=1000,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )

            if response.choices and len(response.choices) > 0:
                text = response.choices[0].message.content or ""
                return text[:1000] if len(text) > 1000 else text

            LOGGER.warning(
                "deepseek_response_no_choices",
                extra={"response_type": type(response).__name__},
            )
            return "Erro ao processar resposta do serviço de IA."

        except Exception as exc:
            LOGGER.error(
                "deepseek_api_error",
                extra={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            raise
