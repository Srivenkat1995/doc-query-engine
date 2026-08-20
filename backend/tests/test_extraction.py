from app.extraction import (
    Citation,
    ExtractedField,
    ExtractionProvider,
    InvoiceExtraction,
    LineItem,
)


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
