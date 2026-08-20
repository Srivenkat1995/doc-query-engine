from collections.abc import Generator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import create_app
from app.models import Invoice, InvoiceIssue


def test_dashboard_lists_and_filters_exception_counts() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        session.add_all(
            [
                Invoice(
                    id="clean-invoice",
                    original_filename="clean.pdf",
                    mime_type="application/pdf",
                    size_bytes=10,
                ),
                Invoice(
                    id="review-invoice",
                    original_filename="review.pdf",
                    mime_type="application/pdf",
                    size_bytes=20,
                    vendor="Acme",
                    total=1250,
                    due_date="2026-09-30",
                ),
            ]
        )
        session.add(
            InvoiceIssue(
                invoice_id="review-invoice",
                code="total_mismatch",
                message="Mismatch",
                details={"difference": "1.00"},
            )
        )
        session.commit()

    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)
        all_response = client.get("/invoices")
        review_response = client.get("/invoices?needs_review=true")
        filtered_response = client.get(
            "/invoices?vendor=acme&total_min=1000&due_date_before=2026-10-01"
        )
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()

    assert all_response.status_code == 200
    assert all_response.json()["total_count"] == 2
    assert review_response.json()["total_count"] == 1
    assert review_response.json()["invoices"][0]["id"] == "review-invoice"
    assert filtered_response.json()["total_count"] == 1
    assert filtered_response.json()["invoices"][0]["vendor"] == "Acme"
