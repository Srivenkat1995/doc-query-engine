from __future__ import annotations

from decimal import Decimal
from typing import Dict, List

from app.confidence import compose_confidence, confidence_review_reason
from app.extraction import (
    Citation,
    ExtractedField,
    ExtractionIssue,
    InvoiceExtraction,
    LineItem,
)


class DeterministicExtractionProvider:
    """Parse the small, line-oriented fixture format used for local demos."""

    def extract(self, content: bytes, mime_type: str) -> InvoiceExtraction:
        del mime_type
        raw_text = content.decode("utf-8")
        values: Dict[str, str] = {}
        confidence: Dict[str, float] = {}
        line_items: List[LineItem] = []

        for line_number, line in enumerate(raw_text.splitlines(), start=1):
            if not line.strip():
                continue
            key, separator, value = line.partition(":")
            if not separator:
                continue
            key = key.strip()
            value = value.strip()
            if key.startswith("CONFIDENCE_"):
                confidence[key.removeprefix("CONFIDENCE_").lower()] = float(value)
            elif key == "ITEM":
                parts = [part.strip() for part in value.split("|")]
                if len(parts) != 4:
                    raise ValueError(
                        "ITEM must contain description, quantity, unit price, "
                        "and amount"
                    )
                line_items.append(
                    LineItem(
                        description=parts[0],
                        quantity=parts[1],
                        unit_price=parts[2],
                        amount=parts[3],
                        citation=Citation(page=1, source_text=line),
                    )
                )
            else:
                values[key.lower()] = value

        required_fields = {
            "vendor": "vendor",
            "total": "total",
            "due_date": "due_date",
            "payment_terms": "payment_terms",
        }
        missing = [label for key, label in required_fields.items() if key not in values]
        if missing or not line_items:
            raise ValueError(
                f"Fixture is missing required fields: {', '.join(missing or ['items'])}"
            )

        consistency_score = self._consistency_score(values["total"], line_items)
        issues = self._reconciliation_issues(values["total"], line_items)
        fields = []
        for key, field_name in required_fields.items():
            signals = compose_confidence(
                confidence.get(key, 0.99),
                format_valid=self._format_valid(key, values[key]),
                consistency_score=consistency_score,
            )
            review_reason = confidence_review_reason(signals)
            fields.append(
                ExtractedField(
                    name=field_name,
                    value=values[key],
                    confidence=signals.final_score,
                    citation=Citation(
                        page=1,
                        source_text=f"{key.upper()}: {values[key]}",
                    ),
                    confidence_signals=signals,
                    needs_review=review_reason is not None,
                    review_reason=review_reason,
                )
            )
        Decimal(values["total"])  # Fail early on malformed money in a fixture.
        return InvoiceExtraction(
            fields=fields,
            line_items=line_items,
            raw_text=raw_text,
            issues=issues,
        )

    @staticmethod
    def _format_valid(key: str, value: str) -> bool:
        if not value:
            return False
        if key == "total":
            try:
                Decimal(value)
            except Exception:
                return False
        return True

    @staticmethod
    def _consistency_score(total: str, line_items: List[LineItem]) -> float:
        try:
            item_total = sum(Decimal(item.amount) for item in line_items)
            return 1.0 if Decimal(total) == item_total else 0.5
        except Exception:
            return 0.0

    @staticmethod
    def _reconciliation_issues(
        printed_total: str,
        line_items: List[LineItem],
    ) -> List[ExtractionIssue]:
        calculated_total = sum(Decimal(item.amount) for item in line_items)
        printed = Decimal(printed_total)
        if printed == calculated_total:
            return []
        difference = printed - calculated_total
        return [
            ExtractionIssue(
                code="total_mismatch",
                message="Printed total does not match the line-item total",
                details={
                    "printed_total": str(printed),
                    "calculated_total": str(calculated_total),
                    "difference": str(difference),
                },
            )
        ]
