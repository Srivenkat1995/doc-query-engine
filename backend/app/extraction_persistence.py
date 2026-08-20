from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.extraction import InvoiceExtraction
from app.models import (
    ExtractedFieldRecord,
    ExtractionRecord,
    Invoice,
    InvoiceIssue,
    InvoiceStatus,
    JobStatus,
    LineItemRecord,
    ProcessingJob,
)


def _citation_values(citation):
    if citation is None:
        return None, None, None
    bounding_box = list(citation.bounding_box) if citation.bounding_box else None
    return citation.page, citation.source_text, bounding_box


def persist_extraction(
    db: Session,
    invoice_id: str,
    job_id: str,
    extraction: InvoiceExtraction,
) -> None:
    """Replace one extraction and complete its invoice/job atomically."""

    invoice = db.get(Invoice, invoice_id)
    job = db.get(ProcessingJob, job_id)
    if invoice is None or job is None or job.invoice_id != invoice_id:
        raise ValueError("Invoice and processing job must exist and match")

    db.execute(
        delete(ExtractedFieldRecord).where(
            ExtractedFieldRecord.invoice_id == invoice_id
        )
    )
    db.execute(
        delete(LineItemRecord).where(LineItemRecord.invoice_id == invoice_id)
    )
    db.execute(
        delete(ExtractionRecord).where(ExtractionRecord.invoice_id == invoice_id)
    )
    db.execute(delete(InvoiceIssue).where(InvoiceIssue.invoice_id == invoice_id))

    for field in extraction.fields:
        page, source_text, bounding_box = _citation_values(field.citation)
        db.add(
            ExtractedFieldRecord(
                invoice_id=invoice_id,
                name=field.name,
                value=field.value,
                confidence=field.confidence,
                confidence_signals=(
                    field.confidence_signals.to_dict()
                    if field.confidence_signals
                    else None
                ),
                needs_review=field.needs_review,
                review_reason=field.review_reason,
                citation_page=page,
                citation_text=source_text,
                bounding_box=bounding_box,
            )
        )
    for position, item in enumerate(extraction.line_items):
        page, source_text, bounding_box = _citation_values(item.citation)
        db.add(
            LineItemRecord(
                invoice_id=invoice_id,
                position=position,
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=item.amount,
                citation_page=page,
                citation_text=source_text,
                bounding_box=bounding_box,
            )
        )
    db.add(ExtractionRecord(invoice_id=invoice_id, raw_text=extraction.raw_text))
    for issue in extraction.issues:
        db.add(
            InvoiceIssue(
                invoice_id=invoice_id,
                code=issue.code,
                message=issue.message,
                details=issue.details,
            )
        )
    invoice.status = InvoiceStatus.READY.value
    job.status = JobStatus.COMPLETED.value
    job.failure_reason = None
