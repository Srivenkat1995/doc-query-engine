from pathlib import Path

import pytest

from app.deterministic_extraction import DeterministicExtractionProvider
from app.extraction import ExtractionProvider

FIXTURES = Path(__file__).parent / "fixtures"


def test_clean_fixture_produces_structured_extraction() -> None:
    provider = DeterministicExtractionProvider()

    result = provider.extract(
        (FIXTURES / "clean_invoice.txt").read_bytes(), "application/pdf"
    )

    assert isinstance(provider, ExtractionProvider)
    assert [(field.name, field.value) for field in result.fields] == [
        ("vendor", "Acme Corporation"),
        ("total", "250.00"),
        ("due_date", "2026-09-30"),
        ("payment_terms", "Net 30"),
    ]
    assert len(result.line_items) == 2
    assert result.line_items[1].amount == "150.00"
    assert result.fields[0].citation is not None


def test_messy_fixture_preserves_low_confidence_and_total() -> None:
    provider = DeterministicExtractionProvider()

    result = provider.extract(
        (FIXTURES / "messy_invoice.txt").read_bytes(), "image/jpeg"
    )

    vendor = next(field for field in result.fields if field.name == "vendor")
    total = next(field for field in result.fields if field.name == "total")
    assert vendor.confidence == 0.672
    assert vendor.confidence_signals is not None
    assert vendor.confidence_signals.model_score == 0.62
    assert vendor.confidence_signals.format_valid is True
    assert vendor.confidence_signals.consistency_score == 0.5
    assert total.value == "300.00"
    assert result.raw_text.startswith("VENDOR: Acme Corporation")


def test_deterministic_provider_returns_same_result_for_same_fixture() -> None:
    provider = DeterministicExtractionProvider()
    content = (FIXTURES / "clean_invoice.txt").read_bytes()

    assert provider.extract(content, "application/pdf") == provider.extract(
        content, "application/pdf"
    )


@pytest.mark.parametrize("content", [b"VENDOR: Acme", b"ITEM: Bad|format"])
def test_provider_rejects_incomplete_fixture(content: bytes) -> None:
    with pytest.raises(ValueError, match="missing required fields|ITEM"):
        DeterministicExtractionProvider().extract(content, "application/pdf")
