"""Baidu QianFan AI Provider (Story 6.2).

Integrates with Baidu's ERNIE model via the qianfan Python SDK.
Provides free-tier access to ERNIE-3.5 for grade query responses.

Reference: https://github.com/baidubce/bce-qianfan-sdk
"""
from __future__ import annotations

import logging
import os
from abc import ABC, abstractmethod
from typing import Any

LOGGER = logging.getLogger("backend.baidu_provider")


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
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


class BaiduProvider(AIProvider):
    """Baidu QianFan API provider via qianfan SDK."""

    def __init__(self, api_key: str) -> None:
        """Initialize Baidu provider.

        Args:
            api_key: Baidu QianFan API key (from console.bce.baidu.com/qianfan)

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("BAIDU_API_KEY is required for baidu provider")
        self.api_key = api_key
        self.model = os.getenv("AI_MODEL", "ernie-3.5-8k")

    def call(self, system_prompt: str, user_message: str) -> str:
        """Call Baidu QianFan API.

        Args:
            system_prompt: System prompt with grade context
            user_message: User's question (sanitized)

        Returns:
            ERNIE-generated response

        Raises:
            Exception: If API call fails
        """
        try:
            import qianfan

            # Initialize client
            client = qianfan.ChatCompletion(api_key=self.api_key)

            # Call the model with messages format
            response: Any = client.do(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
                max_output_tokens=1000,
            )

            # Extract text from response
            # qianfan returns a dict-like object with 'result' key
            if response and isinstance(response, dict):
                if "result" in response:
                    text = str(response["result"])
                    # Truncate to 1000 chars if needed
                    return text[:1000] if len(text) > 1000 else text
                elif "body" in response and isinstance(response["body"], dict):
                    # Handle nested response structure
                    body: Any = response["body"]
                    if "result" in body:
                        text = str(body["result"])
                        return text[:1000] if len(text) > 1000 else text

            LOGGER.warning(
                "baidu_response_format_unexpected",
                extra={
                    "response_type": type(response),
                    "response_keys": (
                        list(response.keys())
                        if isinstance(response, dict)
                        else "N/A"
                    ),
                },
            )
            return "Erro ao processar resposta do serviço de IA."

        except Exception as exc:
            LOGGER.error(
                "baidu_api_error",
                extra={
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                },
            )
            raise
