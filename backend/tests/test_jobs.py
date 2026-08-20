from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    Base.metadata.create_all(engine)

    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


def create_invoice(client: TestClient) -> str:
    response = client.post(
        "/invoices",
        json={
            "original_filename": "invoice.pdf",
            "mime_type": "application/pdf",
            "size_bytes": 100,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_create_processing_job_returns_stable_identity(client: TestClient) -> None:
    invoice_id = create_invoice(client)
    payload = {"idempotency_key": "upload-invoice-1"}

    first = client.post(f"/invoices/{invoice_id}/jobs", json=payload)
    replay = client.post(f"/invoices/{invoice_id}/jobs", json=payload)

    assert first.status_code == 201
    assert replay.status_code == 200
    assert first.json() == replay.json()
    assert first.json()["invoice_id"] == invoice_id
    assert first.json()["status"] == "queued"
    assert first.json()["attempt_count"] == 0


def test_same_key_on_different_invoices_creates_separate_jobs(
    client: TestClient,
) -> None:
    first_invoice_id = create_invoice(client)
    second_invoice_id = create_invoice(client)
    payload = {"idempotency_key": "same-client-request"}

    first = client.post(f"/invoices/{first_invoice_id}/jobs", json=payload)
    second = client.post(f"/invoices/{second_invoice_id}/jobs", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


def test_processing_job_requires_existing_invoice(client: TestClient) -> None:
    response = client.post(
        "/invoices/missing-invoice/jobs",
        json={"idempotency_key": "job-1"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Invoice not found"}
