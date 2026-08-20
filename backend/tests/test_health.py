import json
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_check_returns_service_metadata() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "Document Query Engine API",
        "version": "0.1.0",
        "environment": "development",
        "trace_id": response.headers["X-Trace-Id"],
    }
    UUID(response.headers["X-Trace-Id"])


def test_health_check_includes_configured_cors_origin(monkeypatch) -> None:
    import app.main as main_module
    from app.config import Settings

    monkeypatch.setattr(
        main_module,
        "get_settings",
        lambda: Settings(cors_origins="https://review.example.com"),
    )
    client = TestClient(main_module.create_app())

    response = client.get(
        "/health",
        headers={"Origin": "https://review.example.com"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://review.example.com"


def test_settings_sanitizes_cors_origin_list() -> None:
    from app.config import Settings

    settings = Settings(cors_origins="https://a.example.com, , https://b.example.com")

    assert settings.cors_origins_list == [
        "https://a.example.com",
        "https://b.example.com",
    ]


def test_health_check_preserves_valid_trace_id() -> None:
    client = TestClient(create_app())
    trace_id = "12345678-1234-4234-8234-123456789abc"

    response = client.get("/health", headers={"X-Trace-Id": trace_id})

    assert response.headers["X-Trace-Id"] == trace_id
    assert response.json()["trace_id"] == trace_id


def test_health_check_replaces_invalid_trace_id() -> None:
    client = TestClient(create_app())

    response = client.get("/health", headers={"X-Trace-Id": "not-a-uuid"})

    generated_trace_id = response.headers["X-Trace-Id"]
    UUID(generated_trace_id)
    assert generated_trace_id != "not-a-uuid"


def test_health_check_emits_structured_request_log(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = TestClient(create_app())
    caplog.set_level("INFO", logger="doc_query_engine.http")

    response = client.get(
        "/health?secret=not-logged",
        headers={"X-Trace-Id": "12345678-1234-4234-8234-123456789abc"},
    )

    events = [
        json.loads(record.message)
        for record in caplog.records
        if record.name == "doc_query_engine.http"
    ]
    assert response.status_code == 200
    assert events[-1] == {
        "duration_ms": events[-1]["duration_ms"],
        "event": "http_request_completed",
        "method": "GET",
        "path": "/health",
        "status_code": 200,
        "trace_id": "12345678-1234-4234-8234-123456789abc",
    }
    assert "secret" not in events[-1]
