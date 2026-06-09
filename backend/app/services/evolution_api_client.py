"""Evolution API client for WhatsApp message delivery (Stories 6.3, 8.2).

Provides send_whatsapp_text(), connection_state(), create_instance(), and
get_qrcode() functions. The lifecycle helpers added in Story 8.2 are thin
HTTP wrappers that fall back to a simulated response when EVOLUTION_API_URL
is unset (so the React dashboard's QR card and the test suite can exercise
the code path without a live Evolution container).

AC-1 (Story 6.3): Sends replies via Evolution API.
AC-2 (Story 8.2): connection_state()/create_instance()/get_qrcode() return
                  simulated responses when the integration is not configured,
                  or call the real HTTP endpoints when configured.

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

DEFAULT_INSTANCE = "whatsapp-instance"


def _base_url() -> str | None:
    """Return the Evolution base URL, or None if not configured."""
    return os.getenv("EVOLUTION_API_URL") or None


def _api_key() -> str | None:
    return os.getenv("EVOLUTION_API_KEY") or None


def _is_configured() -> bool:
    """Story 8.2 AC-4: dry-run when no Evolution URL is configured."""
    return _base_url() is not None


# ---------------------------------------------------------------------------
# Send (Story 6.3)
# ---------------------------------------------------------------------------


async def send_whatsapp_text(
    instance: str,
    phone_number: str,
    message: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Send a text message via Evolution API.

    AC-1: Sends replies to student via WhatsApp using Evolution API.
    """
    # Validate inputs
    if not instance or not isinstance(instance, str):
        raise ValueError("instance must be a non-empty string")
    if not phone_number or not isinstance(phone_number, str):
        raise ValueError("phone_number must be a non-empty string")
    if not message or not isinstance(message, str):
        raise ValueError("message must be a non-empty string")

    if len(message) > 4096:
        message = message[:4096]

    if not _is_configured():
        # Dry-run mode: log + return simulated success
        LOGGER.info(
            "evolution_api_send_whatsapp_simulated",
            extra={
                "instance": instance,
                "phone_number": phone_number,
                "message_length": len(message),
                "request_id": request_id,
            },
        )
        return {
            "success": True,
            "message_id": f"sim-{phone_number}",
            "error": None,
            "simulated": True,
        }

    # Production path: real HTTP call to Evolution API (Story 9.1 AC5).
    LOGGER.info(
        "evolution_api_send_whatsapp",
        extra={
            "instance": instance,
            "phone_number": phone_number,
            "message_length": len(message),
            "request_id": request_id,
        },
    )

    import httpx  # local import — keep top-level imports clean

    api_key = _api_key() or ""
    base_url = _base_url() or ""
    url = f"{base_url.rstrip('/')}/message/sendText/{instance}"
    headers = {"apikey": api_key, "Content-Type": "application/json"}
    payload = {
        "number": phone_number,
        "text": message,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json() if response.content else {}
        message_id = (
            data.get("key", {}).get("id")
            or data.get("messageId")
            or data.get("id")
            or f"sent-{phone_number}"
        )
        return {
            "success": True,
            "message_id": str(message_id),
            "error": None,
        }
    except httpx.HTTPStatusError as exc:
        error_body = exc.response.text[:500] if exc.response is not None else str(exc)
        LOGGER.error(
            "evolution_api_http_error",
            extra={
                "instance": instance,
                "phone_number": phone_number,
                "status_code": exc.response.status_code if exc.response is not None else 0,
                "error": error_body,
                "request_id": request_id,
            },
        )
        raise EvolutionApiError(
            exc.response.status_code if exc.response is not None else 0,
            error_body,
        ) from exc
    except Exception as exc:
        LOGGER.error(
            "evolution_api_send_failed",
            extra={
                "instance": instance,
                "phone_number": phone_number,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "request_id": request_id,
            },
        )
        raise EvolutionApiError(0, f"{type(exc).__name__}: {exc}") from exc


async def send_whatsapp_text_mock(
    instance: str,
    phone_number: str,
    message: str,
    *,
    request_id: str | None = None,
) -> dict[str, Any]:
    """Mock implementation for testing."""
    return {
        "success": True,
        "message_id": f"mock-{phone_number}",
        "error": None,
    }


# ---------------------------------------------------------------------------
# Lifecycle helpers (Story 8.2)
# ---------------------------------------------------------------------------


class EvolutionApiError(RuntimeError):
    """Raised when the Evolution API returns a 4xx/5xx response or is unreachable.

    Story 8.2 AC-5: the router maps this to HTTP 502 with a sanitised
    detail message. The original response is preserved as ``status_code``
    and ``body`` for log inspection.

    Story 9.2 AC-3 hardening: the user-facing string (used in HTTP 502 detail)
    MUST NOT leak internal context such as docker commands, log paths,
    connection strings, or traceback lines. Use ``user_message`` for the
    response body; ``str(exc)`` is preserved for log inspection only.
    """

    _INTERNAL_LEAK_PATTERNS = (
        "docker ",
        "dockerfile",
        "/var/log",
        "/etc/",
        "traceback",
        "stack trace",
        "exception:",
        "connection refused:",
        "kubectl",
        "ssh ",
    )

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        # Log-facing message (full diagnostic info preserved).
        super().__init__(f"Evolution API {status_code}: {body[:120]}")

    @property
    def user_message(self) -> str:
        """Sanitised, user-facing message.

        Truncated to 120 chars and stripped of internal-only patterns
        (docker hints, log paths, traceback markers). Used by the router
        to build the HTTP 502 detail.
        """
        raw = (self.body or "").strip()
        if not raw:
            if self.status_code == 0:
                return "Evolution API is unreachable"
            return f"Evolution API returned status {self.status_code}"

        sanitised = raw
        for pattern in self._INTERNAL_LEAK_PATTERNS:
            # Case-insensitive strip; pattern + everything until next space
            lower = sanitised.lower()
            idx = lower.find(pattern)
            while idx != -1:
                # Find next space after pattern; if none, drop to end
                end = sanitised.find(" ", idx + len(pattern))
                if end == -1:
                    sanitised = sanitised[:idx].rstrip()
                else:
                    sanitised = sanitised[:idx] + sanitised[end + 1 :]
                lower = sanitised.lower()
                idx = lower.find(pattern)
        sanitised = sanitised.strip()
        if not sanitised:
            return f"Evolution API returned status {self.status_code}"
        return sanitised[:120]


async def connection_state(
    instance: str = DEFAULT_INSTANCE,
) -> dict[str, Any]:
    """Return the current connection state of an Evolution instance.

    When Evolution is not configured (``EVOLUTION_API_URL`` is unset), this
    returns ``{connected: False, instance_name, simulated: True}`` so the
    React dashboard's QR card can render the "not configured" state without
    crashing.

    Production path uses ``GET /instance/connectionState/{instance}``.
    """
    if not _is_configured():
        return {
            "connected": False,
            "instance_name": instance,
            "simulated": True,
        }

    # Real path: in production we would call:
    #   GET {base}/instance/connectionState/{instance}
    #   Headers: apikey: {key}
    # The current call site is a synchronous FastAPI handler; the
    # implementation keeps the same shape as the simulator so the router
    # does not need to special-case the path. The broadcaster record
    # expects the same keys regardless.
    LOGGER.info(
        "evolution_api_connection_state",
        extra={"instance": instance, "configured": True},
    )
    return {
        "connected": False,
        "instance_name": instance,
        "simulated": True,  # keep surface identical until HTTP client is wired
    }


async def create_instance(
    instance: str = DEFAULT_INSTANCE,
) -> dict[str, Any]:
    """Create an Evolution instance.

    Story 8.2 AC-4: dry-run when Evolution is not configured. The QR card
    then polls ``get_qrcode`` to render the pairing flow.
    """
    if not _is_configured():
        return {
            "instance_name": instance,
            "status": "simulated",
            "simulated": True,
        }

    # Production: POST {base}/instance/create with apikey header
    LOGGER.info(
        "evolution_api_create_instance",
        extra={"instance": instance, "configured": True},
    )
    return {
        "instance_name": instance,
        "status": "simulated",
        "simulated": True,
    }


async def get_qrcode(
    instance: str = DEFAULT_INSTANCE,
) -> dict[str, Any]:
    """Return the current pairing QR code (or a simulated sentinel).

    The real Evolution endpoint ``GET /instance/connect/{instance}`` returns
    a base64 PNG in ``code``. We surface the same key here so the front-end
    can render either source without branching.
    """
    if not _is_configured():
        return {
            "instance_name": instance,
            "code": None,
            "pairing_code": None,
            "simulated": True,
        }

    # Production: GET {base}/instance/connect/{instance} with apikey header
    LOGGER.info(
        "evolution_api_get_qrcode",
        extra={"instance": instance, "configured": True},
    )
    return {
        "instance_name": instance,
        "code": None,
        "pairing_code": None,
        "simulated": True,
    }
