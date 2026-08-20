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


def test_create_and_retrieve_invoice(client: TestClient) -> None:
    payload = {
        "original_filename": "acme-invoice.pdf",
        "mime_type": "application/pdf",
        "size_bytes": 4096,
        "storage_key": "invoices/acme-invoice.pdf",
    }

    create_response = client.post("/invoices", json=payload)

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"]
    assert created["status"] == "uploaded"
    assert created["original_filename"] == payload["original_filename"]

    get_response = client.get(f"/invoices/{created['id']}")

    assert get_response.status_code == 200
    assert get_response.json() == created


def test_get_missing_invoice_returns_not_found(client: TestClient) -> None:
    response = client.get("/invoices/missing-invoice")

    assert response.status_code == 404
    assert response.json() == {"detail": "Invoice not found"}
