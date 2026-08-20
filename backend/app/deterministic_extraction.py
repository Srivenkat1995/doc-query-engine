from __future__ import annotations

from decimal import Decimal
from typing import Dict, List

from app.extraction import Citation, ExtractedField, InvoiceExtraction, LineItem


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

        fields = [
            ExtractedField(
                name=field_name,
                value=values[key],
                confidence=confidence.get(key, 0.99),
                citation=Citation(page=1, source_text=f"{key.upper()}: {values[key]}"),
            )
            for key, field_name in required_fields.items()
        ]
        Decimal(values["total"])  # Fail early on malformed money in a fixture.
        return InvoiceExtraction(
            fields=fields,
            line_items=line_items,
            raw_text=raw_text,
        )
