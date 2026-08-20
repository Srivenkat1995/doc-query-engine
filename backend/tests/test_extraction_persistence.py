from collections.abc import Generator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.deterministic_extraction import DeterministicExtractionProvider
from app.extraction_persistence import persist_extraction
from app.main import create_app
from app.models import CitationRecord, Invoice, InvoiceStatus, JobStatus, ProcessingJob

FIXTURE = Path(__file__).parent / "fixtures" / "clean_invoice.txt"


def test_fixture_extraction_is_persisted_and_retrievable() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    Base.metadata.create_all(engine)
    invoice_id = "invoice-extraction-1"
    job_id = "job-extraction-1"
    with Session(engine) as session:
        session.add(
            Invoice(
                id=invoice_id,
                original_filename="clean_invoice.txt",
                mime_type="application/pdf",
                size_bytes=FIXTURE.stat().st_size,
                storage_key="invoices/invoice-extraction-1",
            )
        )
        session.add(
            ProcessingJob(
                id=job_id,
                invoice_id=invoice_id,
                idempotency_key="extraction-1",
            )
        )
        session.commit()
        extraction = DeterministicExtractionProvider().extract(
            FIXTURE.read_bytes(), "application/pdf"
        )
        persist_extraction(session, invoice_id, job_id, extraction)
        session.commit()
        invoice = session.get(Invoice, invoice_id)
        job = session.get(ProcessingJob, job_id)
        assert invoice is not None
        assert job is not None
        assert invoice.status == InvoiceStatus.READY.value
        assert job.status == JobStatus.COMPLETED.value
        citations = session.query(CitationRecord).filter_by(invoice_id=invoice_id).all()
        assert len(citations) == 6
        assert {citation.entity_type for citation in citations} == {
            "field",
            "line_item",
        }

    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    try:
        response = TestClient(app).get(f"/invoices/{invoice_id}/extraction")
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()

    assert response.status_code == 200
    body = response.json()
    assert body["invoice_id"] == invoice_id
    assert body["raw_text"].startswith("VENDOR: Acme Corporation")
    assert body["fields"][0]["citation"]["page"] == 1
    assert len(body["line_items"]) == 2
    assert body["issues"] == []
