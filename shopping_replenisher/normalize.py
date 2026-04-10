"""Canonical item-name normalization."""

from __future__ import annotations

import re
import unicodedata


_TRIVIAL_PUNCTUATION_PATTERN = re.compile(r"[\.,!?:;'\"]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Normalize an item name into a canonical form."""

    normalized = text.lower()
    normalized = _remove_accents(normalized)
    normalized = _replace_trivial_punctuation(normalized)
    normalized = _collapse_whitespace(normalized)
    normalized = _apply_light_plural_heuristic(normalized)
    normalized = _collapse_whitespace(normalized)
    return normalized


def _remove_accents(text: str) -> str:
    """Strip combining marks after NFKD normalization."""

    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def _replace_trivial_punctuation(text: str) -> str:
    """Remove punctuation considered trivial by the design rules."""

    text = text.replace("-", " ")
    return _TRIVIAL_PUNCTUATION_PATTERN.sub("", text)


def _collapse_whitespace(text: str) -> str:
    """Trim outer whitespace and collapse internal runs."""

    return _WHITESPACE_PATTERN.sub(" ", text).strip()


def _apply_light_plural_heuristic(text: str) -> str:
    """Apply a conservative singular/plural heuristic for Spanish and English."""

    words = text.split()
    return " ".join(_singularize_word(word) for word in words)


def _singularize_word(word: str) -> str:
    """Singularize a single token conservatively."""

    if len(word) <= 3:
        return word

    if word.endswith("es") and len(word) > 4:
        return word[:-2]

    if word.endswith("s") and len(word) > 3:
        return word[:-1]

    return word
