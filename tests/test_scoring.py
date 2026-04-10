"""Tests for item scoring."""

from __future__ import annotations

from datetime import date, datetime

from shopping_replenisher.history import ItemHistory, PurchaseOccurrence
from shopping_replenisher.scoring import ScoredItem, score_item_history


def test_score_item_history_computes_documented_features() -> None:
    """Scoring should compute the Stage 5 feature set from an item history."""

    history = ItemHistory(
        canonical_name="milk",
        original_names={"Milk"},
        occurrences=[
            PurchaseOccurrence(
                task_id="1",
                content="Milk",
                canonical_name="milk",
                completed_at=datetime.fromisoformat("2026-03-01T08:00:00"),
            ),
            PurchaseOccurrence(
                task_id="2",
                content="Milk",
                canonical_name="milk",
                completed_at=datetime.fromisoformat("2026-03-08T08:00:00"),
            ),
            PurchaseOccurrence(
                task_id="3",
                content="Milk",
                canonical_name="milk",
                completed_at=datetime.fromisoformat("2026-03-15T08:00:00"),
            ),
            PurchaseOccurrence(
                task_id="4",
                content="Milk",
                canonical_name="milk",
                completed_at=datetime.fromisoformat("2026-03-22T08:00:00"),
            ),
        ],
        occurrence_days=[
            date(2026, 3, 1),
            date(2026, 3, 8),
            date(2026, 3, 15),
            date(2026, 3, 22),
        ],
    )

    scored_item = score_item_history(history, today=date(2026, 3, 29), is_active=False)

    assert scored_item == ScoredItem(
        canonical_name="milk",
        original_names={"Milk"},
        occurrence_count=4,
        unique_days=4,
        gaps=[7, 7, 7],
        typical_gap=7.0,
        gap_stddev=0.0,
        last_purchased=date(2026, 3, 22),
        days_since_last=7,
        overdue_ratio=1.0,
        is_active=False,
        confidence="medium",
    )


def test_score_item_history_returns_low_confidence_without_stable_pattern() -> None:
    """Items with too few or unstable gaps should be low confidence."""

    history = ItemHistory(
        canonical_name="bread",
        original_names={"Bread"},
        occurrences=[
            PurchaseOccurrence(
                task_id="1",
                content="Bread",
                canonical_name="bread",
                completed_at=datetime.fromisoformat("2026-03-01T08:00:00"),
            ),
            PurchaseOccurrence(
                task_id="2",
                content="Bread",
                canonical_name="bread",
                completed_at=datetime.fromisoformat("2026-03-10T08:00:00"),
            ),
            PurchaseOccurrence(
                task_id="3",
                content="Bread",
                canonical_name="bread",
                completed_at=datetime.fromisoformat("2026-03-30T08:00:00"),
            ),
        ],
        occurrence_days=[date(2026, 3, 1), date(2026, 3, 10), date(2026, 3, 30)],
    )

    scored_item = score_item_history(history, today=date(2026, 4, 5), is_active=True)

    assert scored_item.gaps == [9, 20]
    assert scored_item.typical_gap == 14.5
    assert scored_item.gap_stddev == 5.5
    assert scored_item.confidence == "low"
    assert scored_item.is_active is True

