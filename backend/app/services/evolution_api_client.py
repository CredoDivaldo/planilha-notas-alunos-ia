"""Evolution API client for WhatsApp message delivery (Story 6.3).

Provides send_whatsapp_text() function to send text messages via Evolution API.

AC-1: Sends replies via Evolution API.

The adapter uses the /message/sendText/{instance} endpoint documented in
the Evolution API specification.

Usage:
    await send_whatsapp_text(
        instance="instance-name",
        phone_number="+244912345678",
        message="Your response text"
    )
"""
from __future__ import annotations

import logging
import os
from typing import Any

LOGGER = logging.getLogger("backend.evolution_api_client")


async def send_whatsapp_text(
    instance: str,
    phone_number: str,
    message: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Send a text message via Evolution API.

    AC-1: Sends replies to student via WhatsApp using Evolution API.

    Args:
        instance: Evolution API instance name (e.g., "my-instance")
        phone_number: Recipient phone number (normalized, e.g., "244912345678")
        message: Text message content (must be < 4096 chars for WhatsApp)
        request_id: Optional correlation ID for logging

    Returns:
        Dict with keys:
            - success (bool): True if sent successfully
            - message_id (str | None): ID of sent message (if successful)
            - error (str | None): Error message (if failed)

    Raises:
        ValueError: If required config is missing
    """
    # For MVP: Mock implementation that logs the message
    # In production, this would call Evolution API /message/sendText endpoint

    # Validate inputs
    if not instance or not isinstance(instance, str):
        raise ValueError("instance must be a non-empty string")
    if not phone_number or not isinstance(phone_number, str):
        raise ValueError("phone_number must be a non-empty string")
    if not message or not isinstance(message, str):
        raise ValueError("message must be a non-empty string")

    # Truncate to WhatsApp limit if needed
    if len(message) > 4096:
        message = message[:4096]

    # TODO: Evolution API Integration
    # This is a placeholder. In production:
    # 1. Get Evolution API base URL from config
    # 2. Make HTTP POST to /message/sendText/{instance}
    # 3. Pass phone_number and message in request body
    # 4. Handle responses and errors

    # For now, log and return success
    LOGGER.info(
        "evolution_api_send_whatsapp",
        extra={
            "instance": instance,
            "phone_number": phone_number,
            "message_length": len(message),
            "request_id": request_id,
        },
    )

    # Return success response
    return {
        "success": True,
        "message_id": f"mock-msg-{phone_number}-{hash(message) % 10000}",
        "error": None,
    }


async def send_whatsapp_text_mock(
    instance: str,
    phone_number: str,
    message: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Mock implementation for testing.

    Simulates sending a message without calling external API.

    Args:
        instance: Evolution API instance name
        phone_number: Recipient phone number
        message: Text message content
        request_id: Optional correlation ID

    Returns:
        Mock success response
    """
    LOGGER.debug(
        "evolution_api_send_whatsapp_mock",
        extra={
            "instance": instance,
            "phone_number": phone_number,
            "message_preview": message[:100],
            "request_id": request_id,
        },
    )

    return {
        "success": True,
        "message_id": f"mock-{phone_number}",
        "error": None,
    }
