from uuid import UUID

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
