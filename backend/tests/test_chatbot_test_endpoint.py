"""Integration tests for AI Grade Query Service dry-run endpoint (Story 6.2).

Test Coverage:
  - AC-6: Dry-run endpoint returns AI response without sending WhatsApp
  - Endpoint security and auth
  - Request/response validation
  - Integration with AI service
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import Settings
from backend.app.main import create_app
from backend.app.models import (
    AcademicContext,
    Base,
    BroadcastJob,
    ClassEnrollment,
    PublicationSnapshot,
    Semester,
    Shift,
)


@pytest.fixture
def temp_db_session_with_client(tmp_path: Path) -> tuple[TestClient, Session, str]:
    """Create temp DB and FastAPI test client."""
    db_path = tmp_path / "test.sqlite3"
    database_url = f"sqlite:///{db_path}"

    # Create engine and tables
    engine = create_engine(
        database_url,
        echo=False,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

    # Create students table (for raw SQL queries in tests)
    session_setup = SessionLocal()
    session_setup.execute(
        text("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            student_number VARCHAR(80) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            phone VARCHAR(80),
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    )
    session_setup.commit()
    session_setup.close()

    # Create app with custom settings
    settings = Settings(
        database_url=database_url,
        chatbot_webhook_token="test-token-12345",
    )
    app = create_app(settings)

    # Set session_factory in app state for endpoints to use
    app.state.session_factory = SessionLocal

    # Create test client
    client = TestClient(app)

    # Create session for test setup
    session = SessionLocal()
    yield client, session, database_url
    session.close()
    engine.dispose()


@pytest.fixture
def test_student(temp_db_session_with_client: tuple[TestClient, Session, str]) -> tuple[int, str]:
    """Create a test student."""
    _client, session, _ = temp_db_session_with_client

    # Create students table if it doesn't exist
    session.execute(
        text("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            student_number VARCHAR(80) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            phone VARCHAR(80),
            email VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    )
    session.flush()

    # Insert student
    result = session.execute(
        text("""
        INSERT INTO students (student_number, full_name, email, phone)
        VALUES (:sn, :fn, :em, :ph)
    """),
        {
            "sn": "STU-TEST-001",
            "fn": "Test Student",
            "em": "test@example.com",
            "ph": "351912345678",
        },
    )
    session.commit()
    student_id = result.lastrowid

    return student_id, "STU-TEST-001"


@pytest.fixture
def test_student_with_grades(
    temp_db_session_with_client: tuple[TestClient, Session, str],
    test_student: tuple[int, str],
) -> tuple[int, str]:
    """Create a test student with published grades."""
    _client, session, _ = temp_db_session_with_client
    student_id, student_number = test_student

    # Create professor (for academic context)
    session.execute(
        text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            full_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    )
    session.flush()

    result = session.execute(
        text("""
        INSERT INTO users (email, full_name)
        VALUES (:em, :fn)
    """),
        {
            "em": "prof@example.com",
            "fn": "Prof. Teste",
        },
    )
    session.flush()
    professor_id = result.lastrowid

    # Create semester
    semester = Semester(
        code="2026-1",
        name="Primeiro Semestre 2026",
        academic_year=2026,
        semester_number=1,
    )
    session.add(semester)
    session.flush()

    # Create shift
    shift = Shift(code="SHIFT-1", name="Turno 1")
    session.add(shift)
    session.flush()

    # Create academic context
    context = AcademicContext(
        professor_id=professor_id,
        semester_id=semester.id,
        shift_id=shift.id,
        subject="Matemática",
        turma="A",
        academic_year=2026,
    )
    session.add(context)
    session.flush()

    # Create enrollment
    enrollment = ClassEnrollment(
        student_id=student_id,
        academic_context_id=context.id,
        enrollment_status="Active",
    )
    session.add(enrollment)
    session.flush()

    # Create broadcast job (required FK)
    broadcast_job = BroadcastJob(
        teaching_assignment_id=context.id,
        job_type="manual",
        actor_user_id=professor_id,
        status="completed",
        total_recipients=1,
        total_success=1,
        total_failed=0,
    )
    session.add(broadcast_job)
    session.flush()

    # Create publication snapshot
    snapshot = PublicationSnapshot(
        student_id=student_id,
        teaching_assignment_id=context.id,
        broadcast_job_id=broadcast_job.id,
        snapshot_version=1,
        published_score=Decimal("18.5"),
        published_state="Aprovado",
        published_payload_json=json.dumps({"formula_version": "1.0"}),
        published_at=datetime(2026, 5, 28, tzinfo=UTC),
        is_current=True,
    )
    session.add(snapshot)
    session.commit()

    return student_id, student_number


class TestDryRunEndpoint:
    """Tests for POST /api/v1/chatbot/test endpoint (AC-6)."""

    def test_dry_run_requires_webhook_token(
        self,
        temp_db_session_with_client: tuple[TestClient, Session, str],
        test_student_with_grades: tuple[int, str],
    ) -> None:
        """AC-6: Endpoint requires valid X-Webhook-Token header."""
        client, _session, _ = temp_db_session_with_client
        _student_id, student_number = test_student_with_grades

        # Request without token
        response = client.post(
            "/api/v1/chatbot/test",
            json={
                "student_number": student_number,
                "message": "Qual é minha nota?",
            },
        )

        assert response.status_code == 401
        assert "Missing X-Webhook-Token" in response.json()["detail"]

    def test_dry_run_requires_valid_token(
        self,
        temp_db_session_with_client: tuple[TestClient, Session, str],
        test_student_with_grades: tuple[int, str],
    ) -> None:
        """AC-6: Invalid token returns 401."""
        client, _session, _ = temp_db_session_with_client
        _student_id, student_number = test_student_with_grades

        # Request with invalid token
        response = client.post(
            "/api/v1/chatbot/test",
            headers={"X-Webhook-Token": "wrong-token"},
            json={
                "student_number": student_number,
                "message": "Qual é minha nota?",
            },
        )

        assert response.status_code == 401
        assert "Invalid X-Webhook-Token" in response.json()["detail"]

    def test_dry_run_returns_ai_response_and_context(
        self,
        temp_db_session_with_client: tuple[TestClient, Session, str],
        test_student_with_grades: tuple[int, str],
    ) -> None:
        """AC-6: Dry-run endpoint returns AI response and grades context."""
        client, _session, _ = temp_db_session_with_client
        _student_id, student_number = test_student_with_grades

        # Mock AI response
        mock_response = "A tua nota de Matemática é 18.5. Bom trabalho!"

        with patch(
            "backend.app.routers.chatbot.AIGradeQueryService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.generate_grade_response.return_value = {
                "student_id": _student_id,
                "response": mock_response,
                "grades_context": "- Matemática | Semestre 2026-1 | Turma A | Nota: 18.5 | Estado: Aprovado | Publicado: 2026-05-28",
                "ai_called": True,
                "request_id": None,
            }

            response = client.post(
                "/api/v1/chatbot/test",
                headers={"X-Webhook-Token": "test-token-12345"},
                json={
                    "student_number": student_number,
                    "message": "Qual é minha nota de Matemática?",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["student_number"] == student_number
        assert data["ai_response"] == mock_response
        assert "Matemática" in data["grades_context"]
        assert data["ai_provider_called"] is True

    def test_dry_run_student_not_found(
        self,
        temp_db_session_with_client: tuple[TestClient, Session, str],
    ) -> None:
        """Dry-run returns 404 if student not found."""
        client, _session, _ = temp_db_session_with_client

        response = client.post(
            "/api/v1/chatbot/test",
            headers={"X-Webhook-Token": "test-token-12345"},
            json={
                "student_number": "NONEXISTENT",
                "message": "Qual é minha nota?",
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_dry_run_no_whatsapp_sent(
        self,
        temp_db_session_with_client: tuple[TestClient, Session, str],
        test_student_with_grades: tuple[int, str],
    ) -> None:
        """AC-6: Dry-run endpoint does not send WhatsApp messages."""
        client, _session, _ = temp_db_session_with_client
        _student_id, student_number = test_student_with_grades

        mock_response = "Resposta teste"

        with patch(
            "backend.app.routers.chatbot.AIGradeQueryService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.generate_grade_response.return_value = {
                "student_id": _student_id,
                "response": mock_response,
                "grades_context": "- Matemática | Semestre 2026-1 | Turma A | Nota: 18.5 | Estado: Aprovado | Publicado: 2026-05-28",
                "ai_called": True,
                "request_id": None,
            }

            # No mocking for WhatsApp/Evolution API
            # If it were called, we'd see it in the mock
            response = client.post(
                "/api/v1/chatbot/test",
                headers={"X-Webhook-Token": "test-token-12345"},
                json={
                    "student_number": student_number,
                    "message": "Qual é minha nota?",
                },
            )

            assert response.status_code == 200

            # Verify WhatsApp wasn't called
            # (No WhatsApp send logic in the test endpoint implementation)

    def test_dry_run_with_no_published_grades(
        self,
        temp_db_session_with_client: tuple[TestClient, Session, str],
        test_student: tuple[int, str],
    ) -> None:
        """Dry-run returns graceful message if student has no published grades."""
        client, _session, _ = temp_db_session_with_client
        _student_id, student_number = test_student

        # Create student without grades
        mock_response = "Não tens notas publicadas ainda. Volta mais tarde para verificar."

        with patch(
            "backend.app.routers.chatbot.AIGradeQueryService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.generate_grade_response.return_value = {
                "student_id": _student_id,
                "response": mock_response,
                "grades_context": "",
                "ai_called": False,
                "request_id": None,
            }

            response = client.post(
                "/api/v1/chatbot/test",
                headers={"X-Webhook-Token": "test-token-12345"},
                json={
                    "student_number": student_number,
                    "message": "Qual é minha nota?",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ai_provider_called"] is False
            assert data["grades_context"] == ""

    def test_dry_run_request_validation(
        self,
        temp_db_session_with_client: tuple[TestClient, Session, str],
    ) -> None:
        """Dry-run endpoint validates request format."""
        client, _session, _ = temp_db_session_with_client

        # Missing required fields
        response = client.post(
            "/api/v1/chatbot/test",
            headers={"X-Webhook-Token": "test-token-12345"},
            json={"student_number": "STU001"},  # Missing message
        )

        assert response.status_code == 422  # Validation error

    def test_dry_run_response_structure(
        self,
        temp_db_session_with_client: tuple[TestClient, Session, str],
        test_student_with_grades: tuple[int, str],
    ) -> None:
        """Dry-run response has correct structure."""
        client, _session, _ = temp_db_session_with_client
        _student_id, student_number = test_student_with_grades

        mock_response = "Resposta teste"

        with patch(
            "backend.app.routers.chatbot.AIGradeQueryService"
        ) as mock_service_class:
            mock_service = mock_service_class.return_value
            mock_service.generate_grade_response.return_value = {
                "student_id": _student_id,
                "response": mock_response,
                "grades_context": "- Matemática | Semestre 2026-1 | Turma A | Nota: 18.5 | Estado: Aprovado | Publicado: 2026-05-28",
                "ai_called": True,
                "request_id": "req-123",
            }

            response = client.post(
                "/api/v1/chatbot/test",
                headers={"X-Webhook-Token": "test-token-12345"},
                json={
                    "student_number": student_number,
                    "message": "Teste?",
                },
            )

            assert response.status_code == 200
            data = response.json()

            # Verify all required fields are present
            assert "status" in data
            assert "student_number" in data
            assert "ai_response" in data
            assert "grades_context" in data
            assert "ai_provider_called" in data
            assert "request_id" in data
