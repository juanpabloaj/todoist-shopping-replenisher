"""Tests for purchase-occurrence building and item-history grouping."""

from __future__ import annotations

from datetime import date, datetime

from shopping_replenisher.db import CompletionRow
from shopping_replenisher.history import (
    ItemHistory,
    PurchaseOccurrence,
    build_item_histories,
    build_purchase_occurrences,
)


def test_build_purchase_occurrences_deduplicates_strong_match() -> None:
    """Rows with the same task id within five seconds should collapse to one occurrence."""

    completion_events = [
        CompletionRow(
            task_id="T-100",
            content="Milk",
            completed_at=datetime.fromisoformat("2026-04-01T09:15:00"),
        )
    ]
    completed_tasks = [
        CompletionRow(
            task_id="T-100",
            content="Milk",
            completed_at=datetime.fromisoformat("2026-04-01T09:15:03"),
        )
    ]

    occurrences = build_purchase_occurrences(completion_events, completed_tasks)

    assert occurrences == [
        PurchaseOccurrence(
            task_id="T-100",
            content="Milk",
            canonical_name="milk",
            completed_at=datetime.fromisoformat("2026-04-01T09:15:00"),
        )
    ]


def test_build_purchase_occurrences_deduplicates_medium_match() -> None:
    """Rows with matching canonical content on the same day within ten seconds should collapse."""

    completion_events = [
        CompletionRow(
            task_id="E-210",
            content="Coca Cola",
            completed_at=datetime.fromisoformat("2026-04-02T18:30:00"),
        )
    ]
    completed_tasks = [
        CompletionRow(
            task_id="C-777",
            content="coca-cola",
            completed_at=datetime.fromisoformat("2026-04-02T18:30:08"),
        )
    ]

    occurrences = build_purchase_occurrences(completion_events, completed_tasks)

    assert occurrences == [
        PurchaseOccurrence(
            task_id="E-210",
            content="Coca Cola",
            canonical_name="coca cola",
            completed_at=datetime.fromisoformat("2026-04-02T18:30:00"),
        )
    ]


def test_build_purchase_occurrences_keeps_same_day_rows_when_delta_is_too_large() -> None:
    """Rows beyond the medium-match time window should stay separate."""

    completion_events = [
        CompletionRow(
            task_id="E-300",
            content="eggs",
            completed_at=datetime.fromisoformat("2026-04-03T10:00:00"),
        )
    ]
    completed_tasks = [
        CompletionRow(
            task_id="C-300",
            content="Egg",
            completed_at=datetime.fromisoformat("2026-04-03T10:00:15"),
        )
    ]

    occurrences = build_purchase_occurrences(completion_events, completed_tasks)

    assert occurrences == [
        PurchaseOccurrence(
            task_id="E-300",
            content="eggs",
            canonical_name="egg",
            completed_at=datetime.fromisoformat("2026-04-03T10:00:00"),
        ),
        PurchaseOccurrence(
            task_id="C-300",
            content="Egg",
            canonical_name="egg",
            completed_at=datetime.fromisoformat("2026-04-03T10:00:15"),
        ),
    ]


def test_build_purchase_occurrences_keeps_rows_from_different_days() -> None:
    """Rows with the same canonical content on different days should stay separate."""

    completion_events = [
        CompletionRow(
            task_id="E-410",
            content="quesos",
            completed_at=datetime.fromisoformat("2026-04-04T22:00:00"),
        )
    ]
    completed_tasks = [
        CompletionRow(
            task_id="C-410",
            content="queso",
            completed_at=datetime.fromisoformat("2026-04-05T08:00:00"),
        )
    ]

    occurrences = build_purchase_occurrences(completion_events, completed_tasks)

    assert occurrences == [
        PurchaseOccurrence(
            task_id="E-410",
            content="quesos",
            canonical_name="queso",
            completed_at=datetime.fromisoformat("2026-04-04T22:00:00"),
        ),
        PurchaseOccurrence(
            task_id="C-410",
            content="queso",
            canonical_name="queso",
            completed_at=datetime.fromisoformat("2026-04-05T08:00:00"),
        ),
    ]


def test_build_purchase_occurrences_keeps_rows_for_different_items() -> None:
    """Rows with different canonical content should stay separate."""

    completion_events = [
        CompletionRow(
            task_id="E-500",
            content="milk",
            completed_at=datetime.fromisoformat("2026-04-06T12:00:00"),
        )
    ]
    completed_tasks = [
        CompletionRow(
            task_id="C-500",
            content="bread",
            completed_at=datetime.fromisoformat("2026-04-06T12:00:04"),
        )
    ]

    occurrences = build_purchase_occurrences(completion_events, completed_tasks)

    assert occurrences == [
        PurchaseOccurrence(
            task_id="E-500",
            content="milk",
            canonical_name="milk",
            completed_at=datetime.fromisoformat("2026-04-06T12:00:00"),
        ),
        PurchaseOccurrence(
            task_id="C-500",
            content="bread",
            canonical_name="bread",
            completed_at=datetime.fromisoformat("2026-04-06T12:00:04"),
        ),
    ]


def test_build_item_histories_groups_by_canonical_name() -> None:
    """Occurrences should group into item histories by canonical name."""

    occurrences = [
        PurchaseOccurrence(
            task_id="1",
            content="Coca Cola",
            canonical_name="coca cola",
            completed_at=datetime.fromisoformat("2026-04-01T10:00:00"),
        ),
        PurchaseOccurrence(
            task_id="2",
            content="coca-cola",
            canonical_name="coca cola",
            completed_at=datetime.fromisoformat("2026-04-03T10:00:00"),
        ),
        PurchaseOccurrence(
            task_id="3",
            content="Milk",
            canonical_name="milk",
            completed_at=datetime.fromisoformat("2026-04-02T10:00:00"),
        ),
    ]

    histories = build_item_histories(occurrences)

    assert histories["coca cola"] == ItemHistory(
        canonical_name="coca cola",
        original_names={"Coca Cola", "coca-cola"},
        occurrences=[
            PurchaseOccurrence(
                task_id="1",
                content="Coca Cola",
                canonical_name="coca cola",
                completed_at=datetime.fromisoformat("2026-04-01T10:00:00"),
            ),
            PurchaseOccurrence(
                task_id="2",
                content="coca-cola",
                canonical_name="coca cola",
                completed_at=datetime.fromisoformat("2026-04-03T10:00:00"),
            ),
        ],
        occurrence_days=[date(2026, 4, 1), date(2026, 4, 3)],
    )
    assert histories["milk"] == ItemHistory(
        canonical_name="milk",
        original_names={"Milk"},
        occurrences=[
            PurchaseOccurrence(
                task_id="3",
                content="Milk",
                canonical_name="milk",
                completed_at=datetime.fromisoformat("2026-04-02T10:00:00"),
            )
        ],
        occurrence_days=[date(2026, 4, 2)],
    )
