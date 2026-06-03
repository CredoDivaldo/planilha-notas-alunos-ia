"""Integration tests for WhatsApp chatbot webhook endpoint (Story 6.1).

Tests webhook validation, student lookup, phone normalization, and error handling.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app


@pytest.fixture
def webhook_token() -> str:
    """Webhook token for testing."""
    return "test-webhook-token-123"


@pytest.fixture
def app_with_token(webhook_token: str) -> FastAPI:
    """Create app with webhook token configured."""
    settings = Settings(chatbot_webhook_token=webhook_token)
    return create_app(settings)


@pytest.fixture
def client(app_with_token: FastAPI) -> TestClient:
    """FastAPI test client."""
    return TestClient(app_with_token)


@pytest.fixture
def valid_webhook_payload() -> dict:
    """Valid webhook payload from Evolution API."""
    return {
        "event": "messages.upsert",
        "instance": "instance-name",
        "data": {
            "key": {
                "remoteJid": "244912345678@s.whatsapp.net",
                "fromMe": False,
                "id": "message-id-123",
            },
            "message": {"conversation": "Qual é a minha nota de Matemática?"},
            "messageType": "conversation",
        },
    }


class TestWebhookTokenValidation:
    """Test webhook token validation (AC-2)."""

    def test_missing_token_returns_401(self, client: TestClient) -> None:
        """Missing X-Webhook-Token returns 401."""
        response = client.post(
            "/api/v1/chatbot/webhook",
            json={"event": "messages.upsert", "instance": "test", "data": {}},
        )
        assert response.status_code == 401
        assert "X-Webhook-Token" in response.json()["detail"]

    def test_invalid_token_returns_401(
        self, client: TestClient, valid_webhook_payload: dict
    ) -> None:
        """Invalid X-Webhook-Token returns 401."""
        response = client.post(
            "/api/v1/chatbot/webhook",
            json=valid_webhook_payload,
            headers={"X-Webhook-Token": "wrong-token"},
        )
        assert response.status_code == 401

    def test_valid_token_accepted(
        self, client: TestClient, valid_webhook_payload: dict, webhook_token: str
    ) -> None:
        """Valid X-Webhook-Token is accepted."""
        with patch("backend.app.routers.chatbot.get_db_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.execute.return_value.fetchone.return_value = (1, "S001", "João Silva")

            response = client.post(
                "/api/v1/chatbot/webhook",
                json=valid_webhook_payload,
                headers={"X-Webhook-Token": webhook_token},
            )
            assert response.status_code == 200
            assert response.json()["status"] == "ok"


class TestWebhookEndpoint:
    """Test webhook endpoint behavior (AC-1, AC-3, AC-4, AC-5)."""

    def test_valid_message_student_found(
        self, client: TestClient, valid_webhook_payload: dict, webhook_token: str
    ) -> None:
        """Valid message with student found returns 200 (AC-3).

        Note: Story 6.3 adds end-to-end pipeline. Without AI provider configured,
        it logs a warning but still returns 200.
        """
        with patch("backend.app.routers.chatbot.get_db_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            # Simulate student found
            mock_db.execute.return_value.fetchone.return_value = (
                42,
                "S001",
                "João Silva",
            )

            response = client.post(
                "/api/v1/chatbot/webhook",
                json=valid_webhook_payload,
                headers={"X-Webhook-Token": webhook_token},
            )

            assert response.status_code == 200
            assert response.json()["status"] == "ok"
            # Story 6.3: now says "processed" instead of "queued"
            assert "processed" in response.json()["message"].lower()

    def test_unknown_phone_graceful_handling(
        self, client: TestClient, valid_webhook_payload: dict, webhook_token: str
    ) -> None:
        """Unknown phone number is handled gracefully (AC-4).

        Note: Story 6.3 processes the message silently. Without AI provider configured,
        it logs a warning but still returns 200.
        """
        with patch("backend.app.routers.chatbot.get_db_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db

            # Simulate student not found
            mock_db.execute.return_value.fetchone.return_value = None

            response = client.post(
                "/api/v1/chatbot/webhook",
                json=valid_webhook_payload,
                headers={"X-Webhook-Token": webhook_token},
            )

            assert response.status_code == 200
            assert response.json()["status"] == "ok"
            # AC-4: unknown phone returns 200 without calling AI or exposing data
            assert "received" in response.json()["message"].lower()

    def test_non_message_event_ignored(
        self, client: TestClient, webhook_token: str
    ) -> None:
        """Non-message events are ignored silently (AC-5)."""
        payload = {
            "event": "messages.update",  # Not messages.upsert
            "instance": "instance-name",
            "data": {"key": {"remoteJid": "244912345678@s.whatsapp.net"}},
        }

        response = client.post(
            "/api/v1/chatbot/webhook",
            json=payload,
            headers={"X-Webhook-Token": webhook_token},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_non_text_message_ignored(
        self, client: TestClient, webhook_token: str
    ) -> None:
        """Non-text messages (status, read receipts) are ignored (AC-5)."""
        payload = {
            "event": "messages.upsert",
            "instance": "instance-name",
            "data": {
                "key": {
                    "remoteJid": "244912345678@s.whatsapp.net",
                    "fromMe": False,
                    "id": "msg-1",
                },
                "message": {},  # No conversation field
                "messageType": "status",  # Not a conversation
            },
        }

        response = client.post(
            "/api/v1/chatbot/webhook",
            json=payload,
            headers={"X-Webhook-Token": webhook_token},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert "ignored" in response.json()["message"].lower()

    def test_phone_normalization_applied(
        self, client: TestClient, webhook_token: str
    ) -> None:
        """Phone normalization is applied before student lookup."""
        payload = {
            "event": "messages.upsert",
            "instance": "instance-name",
            "data": {
                "key": {
                    "remoteJid": "+244-91-234-5678@s.whatsapp.net",  # With formatting
                    "fromMe": False,
                    "id": "msg-1",
                },
                "message": {"conversation": "Olá"},
                "messageType": "conversation",
            },
        }

        with patch("backend.app.routers.chatbot.get_db_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.execute.return_value.fetchone.return_value = (1, "S001", "João")

            response = client.post(
                "/api/v1/chatbot/webhook",
                json=payload,
                headers={"X-Webhook-Token": webhook_token},
            )

            # Verify normalized phone was used in the student lookup query (first execute call)
            mock_db.execute.assert_called()
            first_call_args = mock_db.execute.call_args_list[0]
            assert "244912345678" in str(first_call_args)

    def test_malformed_payload_handling(
        self, client: TestClient, webhook_token: str
    ) -> None:
        """Malformed payloads are handled gracefully."""
        payload = {
            "event": "messages.upsert",
            "instance": "instance-name",
            "data": {},  # Missing key and message
        }

        response = client.post(
            "/api/v1/chatbot/webhook",
            json=payload,
            headers={"X-Webhook-Token": webhook_token},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_immediate_200_response(
        self, client: TestClient, valid_webhook_payload: dict, webhook_token: str
    ) -> None:
        """Valid message returns 200 OK immediately (AC-1)."""
        with patch("backend.app.routers.chatbot.get_db_session") as mock_session:
            mock_db = MagicMock()
            mock_session.return_value = mock_db
            mock_db.execute.return_value.fetchone.return_value = (1, "S001", "João")

            response = client.post(
                "/api/v1/chatbot/webhook",
                json=valid_webhook_payload,
                headers={"X-Webhook-Token": webhook_token},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "message" in data
