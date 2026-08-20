from __future__ import annotations

from typing import Optional, Protocol, runtime_checkable

from app.extraction import ExtractionIssue, ExtractionProvider, InvoiceExtraction


@runtime_checkable
class RepairableExtractionProvider(Protocol):
    def repair(
        self,
        content: bytes,
        mime_type: str,
        validation_error: str,
    ) -> InvoiceExtraction:
        """Repair one invalid extraction using validation context."""


def extract_with_one_repair(
    provider: ExtractionProvider,
    content: bytes,
    mime_type: str,
    *,
    raw_text: Optional[str] = None,
) -> InvoiceExtraction:
    """Run extraction once, then allow exactly one optional repair attempt."""

    try:
        return provider.extract(content, mime_type)
    except Exception as first_error:
        repair = getattr(provider, "repair", None)
        if callable(repair):
            try:
                return repair(content, mime_type, str(first_error))
            except Exception:
                pass
        fallback_text = raw_text if raw_text is not None else content.decode(
            "utf-8", errors="replace"
        )
        return InvoiceExtraction(
            fields=[],
            line_items=[],
            raw_text=fallback_text,
            issues=[
                ExtractionIssue(
                    code="schema_repair_failed",
                    message="Extraction could not be repaired after one attempt",
                    details={"validation_error": str(first_error)},
                )
            ],
        )
