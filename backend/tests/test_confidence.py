import pytest

from app.confidence import compose_confidence


@pytest.mark.parametrize(
    ("model_score", "format_valid", "consistency_score", "expected"),
    [
        (1.0, True, 1.0, 1.0),
        (0.5, True, 1.0, 0.7),
        (0.5, False, 1.0, 0.5),
        (0.5, True, 0.0, 0.5),
    ],
)
def test_confidence_composition_exposes_signal_effects(
    model_score: float,
    format_valid: bool,
    consistency_score: float,
    expected: float,
) -> None:
    signals = compose_confidence(
        model_score,
        format_valid=format_valid,
        consistency_score=consistency_score,
    )

    assert signals.final_score == expected
    assert signals.model_score == model_score
    assert signals.format_valid is format_valid
    assert signals.consistency_score == consistency_score


def test_confidence_inputs_are_bounded() -> None:
    signals = compose_confidence(
        2.0,
        format_valid=True,
        consistency_score=-1.0,
    )

    assert signals.model_score == 1.0
    assert signals.consistency_score == 0.0
    assert signals.final_score == 0.8
