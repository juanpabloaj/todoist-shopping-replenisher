"""Tests for canonical item normalization."""

from __future__ import annotations

import pytest

from shopping_replenisher.normalize import normalize


@pytest.mark.parametrize(
    ("raw_text", "expected"),
    [
        ("Milk", "milk"),
        ("QUESO", "queso"),
        ("Coca Cola", "coca cola"),
        ("Café", "cafe"),
        ("Azúcar", "azucar"),
        ("Jamón", "jamon"),
        ("  milk", "milk"),
        ("milk  ", "milk"),
        ("coca   cola", "coca cola"),
        ("  queso   crema  ", "queso crema"),
        ("coca-cola", "coca cola"),
        ("coca, cola", "coca cola"),
        ("milk.", "milk"),
        ("queso!", "queso"),
        ("quesos", "queso"),
        ("egg", "egg"),
        ("eggs", "egg"),
    ],
)
def test_normalize_matches_documented_examples(raw_text: str, expected: str) -> None:
    """The normalizer should match the concrete domain-rule examples."""

    assert normalize(raw_text) == expected


def test_normalize_is_conservative_for_unmatched_words() -> None:
    """The normalizer should not do fuzzy matching beyond the documented rules."""

    assert normalize("bread") == "bread"

