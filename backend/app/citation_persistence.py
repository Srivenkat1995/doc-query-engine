from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.extraction import InvoiceExtraction
from app.models import CitationRecord


def replace_citations(
    db: Session,
    invoice_id: str,
    extraction: InvoiceExtraction,
    field_ids: list[str],
    line_item_ids: list[str],
) -> None:
    """Replace durable source references for one extraction."""

    db.execute(delete(CitationRecord).where(CitationRecord.invoice_id == invoice_id))
    for field, record_id in zip(extraction.fields, field_ids):
        if field.citation is not None:
            db.add(
                CitationRecord(
                    invoice_id=invoice_id,
                    entity_type="field",
                    entity_id=record_id,
                    page=field.citation.page,
                    source_text=field.citation.source_text,
                    bounding_box=(
                        list(field.citation.bounding_box)
                        if field.citation.bounding_box
                        else None
                    ),
                )
            )
    for item, record_id in zip(extraction.line_items, line_item_ids):
        if item.citation is not None:
            db.add(
                CitationRecord(
                    invoice_id=invoice_id,
                    entity_type="line_item",
                    entity_id=record_id,
                    page=item.citation.page,
                    source_text=item.citation.source_text,
                    bounding_box=(
                        list(item.citation.bounding_box)
                        if item.citation.bounding_box
                        else None
                    ),
                )
            )
