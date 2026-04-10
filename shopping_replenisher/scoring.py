"""Feature extraction and scoring for purchase histories."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import statistics

from shopping_replenisher.history import ItemHistory


Confidence = str


@dataclass(frozen=True)
class ScoredItem:
    """Computed scoring features for a canonical item history."""

    canonical_name: str
    original_names: set[str]
    occurrence_count: int
    unique_days: int
    gaps: list[int]
    typical_gap: float | None
    gap_stddev: float | None
    last_purchased: date
    days_since_last: int
    overdue_ratio: float | None
    is_active: bool
    confidence: Confidence


def score_item_history(
    history: ItemHistory,
    *,
    today: date,
    is_active: bool,
) -> ScoredItem:
    """Compute scoring features for a single item history."""

    occurrence_count = len(history.occurrences)
    unique_days = len(history.occurrence_days)
    gaps = _calculate_gaps(history.occurrence_days)
    typical_gap = float(statistics.median(gaps)) if gaps else None
    gap_stddev = float(statistics.pstdev(gaps)) if len(gaps) >= 2 else 0.0 if gaps else None
    last_purchased = max(history.occurrence_days)
    days_since_last = (today - last_purchased).days
    overdue_ratio = (
        days_since_last / typical_gap if typical_gap is not None and typical_gap > 0 else None
    )

    return ScoredItem(
        canonical_name=history.canonical_name,
        original_names=history.original_names,
        occurrence_count=occurrence_count,
        unique_days=unique_days,
        gaps=gaps,
        typical_gap=typical_gap,
        gap_stddev=gap_stddev,
        last_purchased=last_purchased,
        days_since_last=days_since_last,
        overdue_ratio=overdue_ratio,
        is_active=is_active,
        confidence=_classify_confidence(unique_days=unique_days, gap_stddev=gap_stddev),
    )


def _calculate_gaps(occurrence_days: list[date]) -> list[int]:
    """Calculate day gaps between consecutive purchase days."""

    sorted_days = sorted(occurrence_days)
    return [
        (current_day - previous_day).days
        for previous_day, current_day in zip(sorted_days, sorted_days[1:])
    ]


def _classify_confidence(unique_days: int, gap_stddev: float | None) -> Confidence:
    """Classify confidence from purchase volume and gap stability."""

    if gap_stddev is None:
        return "low"
    if unique_days >= 8 and gap_stddev <= 5.5:
        return "high"
    if unique_days >= 4 and gap_stddev <= 7:
        return "medium"
    return "low"
