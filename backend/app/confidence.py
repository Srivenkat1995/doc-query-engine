from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

CONFIDENCE_REVIEW_THRESHOLD = 0.75
LOW_CONFIDENCE_REVIEW_REASON = "low_confidence"

@dataclass(frozen=True)
class ConfidenceSignals:
    model_score: float
    format_valid: bool
    consistency_score: float
    final_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compose_confidence(
    model_score: float,
    *,
    format_valid: bool,
    consistency_score: float,
) -> ConfidenceSignals:
    """Combine explainable signals into one bounded confidence score."""

    normalized_model_score = min(max(model_score, 0.0), 1.0)
    normalized_consistency = min(max(consistency_score, 0.0), 1.0)
    format_score = 1.0 if format_valid else 0.0
    final_score = round(
        (normalized_model_score * 0.6)
        + (format_score * 0.2)
        + (normalized_consistency * 0.2),
        4,
    )
    return ConfidenceSignals(
        model_score=normalized_model_score,
        format_valid=format_valid,
        consistency_score=normalized_consistency,
        final_score=final_score,
    )


def confidence_review_reason(signals: ConfidenceSignals) -> str | None:
    """Return a review reason when final confidence is below the threshold."""

    if signals.final_score < CONFIDENCE_REVIEW_THRESHOLD:
        return LOW_CONFIDENCE_REVIEW_REASON
    return None
