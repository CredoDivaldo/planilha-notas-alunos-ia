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

def _default_instance() -> str:
    return os.getenv("EVOLUTION_INSTANCE") or "whatsapp-instance"

DEFAULT_INSTANCE = "whatsapp-instance"


def _base_url() -> str | None:
    """Return the Evolution base URL, or None if not configured."""
    return os.getenv("EVOLUTION_API_URL") or os.getenv("EVOLUTION_BASE_URL") or None


def _api_key() -> str | None:
    return os.getenv("EVOLUTION_API_KEY") or None


def _is_configured() -> bool:
    """Story 8.2 AC-4: dry-run when no Evolution URL is configured."""
    return _base_url() is not None


def _headers() -> dict[str, str]:
    return {"apikey": _api_key() or "", "Content-Type": "application/json"}


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
    instance: str | None = None,
) -> dict[str, Any]:
    """Return the current connection state of an Evolution instance.

    Uses /instance/connectionState (real-time state from Baileys) as primary.
    Falls back to /instance/fetchInstances if connectionState fails.
    """
    inst = instance or _default_instance()
    if not _is_configured():
        return {"connected": False, "instance_name": inst, "simulated": True}

    import httpx

    base = (_base_url() or "").rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            # Primary: connectionState — real-time Baileys state
            resp = await client.get(f"{base}/instance/connectionState/{inst}", headers=_headers())
        if resp.status_code == 200:
            data = resp.json()
            status = (
                data.get("instance", {}).get("state")
                or data.get("instance", {}).get("status")
                or data.get("state")
                or ""
            ).lower()
            connected = status in ("open", "connected", "online")
            return {"connected": connected, "instance_name": inst, "simulated": False}
        # Fallback: fetchInstances
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp2 = await client.get(f"{base}/instance/fetchInstances", headers=_headers())
        if resp2.status_code == 200:
            instances = resp2.json() if isinstance(resp2.json(), list) else []
            for item in instances:
                if isinstance(item, dict) and item.get("name") == inst:
                    status = (item.get("connectionStatus") or "").lower()
                    connected = status in ("open", "connected", "online")
                    return {"connected": connected, "instance_name": inst, "simulated": False}
        LOGGER.warning("evolution_api_connection_state_non200", extra={"status": resp.status_code})
        return {"connected": False, "instance_name": inst, "simulated": False}
    except Exception as exc:
        LOGGER.warning("evolution_api_connection_state_failed", extra={"error": str(exc)})
        return {"connected": False, "instance_name": inst, "simulated": False}


async def create_instance(
    instance: str | None = None,
) -> dict[str, Any]:
    """Create an Evolution instance."""
    inst = instance or _default_instance()
    if not _is_configured():
        return {"instance_name": inst, "status": "simulated", "simulated": True}

    import httpx

    base = (_base_url() or "").rstrip("/")
    url = f"{base}/instance/create"
    payload = {
        "instanceName": inst,
        "integration": os.getenv("EVOLUTION_INTEGRATION") or "WHATSAPP-BAILEYS",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=_headers())
        if resp.status_code in (200, 201):
            data = resp.json()
            return {
                "instance_name": data.get("instanceName") or inst,
                "status": data.get("status") or "created",
                "simulated": False,
            }
        LOGGER.warning("evolution_api_create_instance_failed", extra={"status": resp.status_code})
        raise EvolutionApiError(resp.status_code, resp.text[:500])
    except EvolutionApiError:
        raise
    except Exception as exc:
        LOGGER.error("evolution_api_create_instance_error", extra={"error": str(exc)})
        raise EvolutionApiError(0, str(exc)) from exc


async def get_qrcode(
    instance: str | None = None,
) -> dict[str, Any]:
    """Return the current pairing QR code from Evolution API."""
    inst = instance or _default_instance()
    if not _is_configured():
        return {"instance_name": inst, "code": None, "pairing_code": None, "simulated": True}

    import httpx

    base = (_base_url() or "").rstrip("/")
    url = f"{base}/instance/connect/{inst}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers=_headers())
        if resp.status_code == 200:
            data = resp.json()
            code = data.get("code") or data.get("qrcode") or data.get("base64")
            pairing = data.get("pairingCode") or data.get("pairing_code")
            return {
                "instance_name": inst,
                "code": code,
                "pairing_code": pairing,
                "simulated": False,
            }
        LOGGER.warning("evolution_api_get_qrcode_failed", extra={"status": resp.status_code})
        return {"instance_name": inst, "code": None, "pairing_code": None, "simulated": False}
    except Exception as exc:
        LOGGER.warning("evolution_api_get_qrcode_error", extra={"error": str(exc)})
        return {"instance_name": inst, "code": None, "pairing_code": None, "simulated": False}


async def configure_webhook(
    instance: str | None = None,
    webhook_url: str = "",
    events: list[str] | None = None,
) -> dict[str, Any]:
    """Configure the webhook for an Evolution instance.

    Calls POST /webhook/set/{instance} to register the webhook URL and
    the list of events to forward. Falls back to simulated mode when
    EVOLUTION_API_URL is not configured.
    """
    inst = instance or _default_instance()
    if events is None:
        events = ["MESSAGES_UPSERT", "CONNECTION_UPDATE"]

    if not _is_configured():
        LOGGER.info(
            "evolution_api_configure_webhook_simulated",
            extra={"instance": inst, "webhook_url": webhook_url},
        )
        return {"configured": True, "url": webhook_url, "simulated": True}

    import httpx

    base = (_base_url() or "").rstrip("/")
    url = f"{base}/webhook/set/{inst}"
    payload = {
        "webhook": {
            "enabled": True,
            "url": webhook_url,
            "webhookBase64": False,
            "webhookByEvents": False,
            "events": events,
        }
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload, headers=_headers())
        if resp.status_code in (200, 201):
            return {"configured": True, "url": webhook_url, "simulated": False}
        LOGGER.warning(
            "evolution_api_configure_webhook_failed",
            extra={"status": resp.status_code, "body": resp.text[:200]},
        )
        raise EvolutionApiError(resp.status_code, resp.text[:500])
    except EvolutionApiError:
        raise
    except Exception as exc:
        LOGGER.error("evolution_api_configure_webhook_error", extra={"error": str(exc)})
        raise EvolutionApiError(0, str(exc)) from exc
