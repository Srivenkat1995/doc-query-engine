from __future__ import annotations

from typing import List, Optional, Tuple

from pydantic import BaseModel


class CitationResponse(BaseModel):
    page: int
    source_text: str
    bounding_box: Optional[Tuple[float, float, float, float]]


class ExtractedFieldResponse(BaseModel):
    name: str
    value: Optional[str]
    confidence: float
    confidence_signals: Optional[dict]
    needs_review: bool
    review_reason: Optional[str]
    citation: Optional[CitationResponse]


class LineItemResponse(BaseModel):
    description: str
    quantity: str
    unit_price: str
    amount: str
    citation: Optional[CitationResponse]


class ExtractionResponse(BaseModel):
    invoice_id: str
    fields: List[ExtractedFieldResponse]
    line_items: List[LineItemResponse]
    raw_text: str
