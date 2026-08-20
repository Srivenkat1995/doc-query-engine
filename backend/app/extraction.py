from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, Sequence, Tuple, runtime_checkable

from app.confidence import ConfidenceSignals


@dataclass(frozen=True)
class Citation:
    """Source location supporting an extracted value."""

    page: int
    source_text: str
    bounding_box: Optional[Tuple[float, float, float, float]] = None


@dataclass(frozen=True)
class ExtractedField:
    """A field value with its confidence and source reference."""

    name: str
    value: Optional[str]
    confidence: float
    citation: Optional[Citation] = None
    confidence_signals: Optional[ConfidenceSignals] = None
    needs_review: bool = False
    review_reason: Optional[str] = None


@dataclass(frozen=True)
class LineItem:
    description: str
    quantity: str
    unit_price: str
    amount: str
    citation: Optional[Citation] = None


@dataclass(frozen=True)
class ExtractionIssue:
    code: str
    message: str
    details: dict[str, str]


@dataclass(frozen=True)
class InvoiceExtraction:
    """Provider-neutral structured extraction result."""

    fields: Sequence[ExtractedField]
    line_items: Sequence[LineItem]
    raw_text: str
    issues: Sequence[ExtractionIssue] = field(default_factory=tuple)


@runtime_checkable
class ExtractionProvider(Protocol):
    """Provider boundary for OCR/layout and invoice extraction."""

    def extract(self, content: bytes, mime_type: str) -> InvoiceExtraction:
        """Extract invoice fields, line items, source text, and citations."""
