from app.extraction import (
    Citation,
    ExtractedField,
    ExtractionProvider,
    InvoiceExtraction,
    LineItem,
)
from app.repair import extract_with_one_repair


class FakeExtractionProvider:
    def extract(self, content: bytes, mime_type: str) -> InvoiceExtraction:
        return InvoiceExtraction(
            fields=[
                ExtractedField(
                    name="vendor",
                    value="Acme",
                    confidence=0.98,
                    citation=Citation(page=1, source_text="Acme Corporation"),
                )
            ],
            line_items=[
                LineItem(
                    description="Consulting",
                    quantity="1",
                    unit_price="100.00",
                    amount="100.00",
                )
            ],
            raw_text=content.decode(),
        )


def test_fake_provider_satisfies_extraction_contract() -> None:
    provider = FakeExtractionProvider()

    assert isinstance(provider, ExtractionProvider)
    result = provider.extract(b"Acme Corporation", "application/pdf")

    assert result.fields[0].value == "Acme"
    assert result.fields[0].citation is not None
    assert result.line_items[0].amount == "100.00"
    assert result.raw_text == "Acme Corporation"


class RepairingProvider(FakeExtractionProvider):
    def __init__(self) -> None:
        self.repair_calls = 0

    def extract(self, content: bytes, mime_type: str) -> InvoiceExtraction:
        raise ValueError("invalid schema")

    def repair(
        self,
        content: bytes,
        mime_type: str,
        validation_error: str,
    ) -> InvoiceExtraction:
        self.repair_calls += 1
        return super().extract(content, mime_type)


def test_repair_provider_gets_exactly_one_repair_attempt() -> None:
    provider = RepairingProvider()

    result = extract_with_one_repair(provider, b"Acme Corporation", "application/pdf")

    assert provider.repair_calls == 1
    assert result.fields[0].value == "Acme"


def test_failed_repair_preserves_raw_text_and_creates_review_issue() -> None:
    class BrokenProvider:
        def extract(self, content: bytes, mime_type: str) -> InvoiceExtraction:
            raise ValueError("invalid schema")

    result = extract_with_one_repair(BrokenProvider(), b"raw invoice text", "")

    assert result.fields == []
    assert result.raw_text == "raw invoice text"
    assert result.issues[0].code == "schema_repair_failed"
