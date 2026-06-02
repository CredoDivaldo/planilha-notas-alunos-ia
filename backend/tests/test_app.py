from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from backend.app.config import Settings
from backend.app.main import create_app


def test_health_endpoint_sets_request_id_and_reports_sqlite_runtime(tmp_path: Path) -> None:
    database_path = tmp_path / "app.sqlite3"
    app = create_app(Settings(database_url=f"sqlite:///{database_path}"))

    with TestClient(app) as client:
        response = client.get("/api/v1/health", headers={"X-Request-ID": "test-request-id"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["api_prefix"] == "/api/v1"
    assert payload["request_id"] == "test-request-id"
    assert response.headers["X-Request-ID"] == "test-request-id"
    assert payload["database"]["dialect"] == "sqlite"
    assert payload["database"]["foreign_keys_enabled"] is True


def test_openapi_runtime_includes_health_contract(tmp_path: Path) -> None:
    database_path = tmp_path / "app.sqlite3"
    app = create_app(Settings(database_url=f"sqlite:///{database_path}"))

    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    payload = response.json()
    assert "/api/v1/health" in payload["paths"]
