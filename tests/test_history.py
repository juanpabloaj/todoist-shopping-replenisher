"""Tests for purchase-occurrence building and item-history grouping."""

from __future__ import annotations

from datetime import date, datetime, timezone

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


def test_build_purchase_occurrences_deduplicates_medium_match_using_configured_timezone() -> None:
    """Configured timezone must control same-day matching for UTC-aware rows."""

    completion_events = [
        CompletionRow(
            task_id="E-211",
            content="Yogurt",
            completed_at=datetime(2026, 4, 10, 23, 59, 55, tzinfo=timezone.utc),
        )
    ]
    completed_tasks = [
        CompletionRow(
            task_id="C-778",
            content="yogurts",
            completed_at=datetime(2026, 4, 11, 0, 0, 3, tzinfo=timezone.utc),
        )
    ]

    occurrences = build_purchase_occurrences(
        completion_events,
        completed_tasks,
        timezone_name="America/Santiago",
    )

    assert occurrences == [
        PurchaseOccurrence(
            task_id="E-211",
            content="Yogurt",
            canonical_name="yogurt",
            completed_at=datetime(2026, 4, 10, 23, 59, 55, tzinfo=timezone.utc),
        )
    ]


def test_to_local_date_uses_astimezone_for_aware_datetimes() -> None:
    """UTC-aware datetimes must be converted through astimezone before extracting the date.

    The bug this guards: calling .date() directly on a UTC-aware datetime gives the UTC
    calendar date, which differs from the local calendar date for any timezone behind UTC.
    _to_local_date must call .astimezone() first.

    We verify the contract indirectly: a UTC datetime at a fixed offset yields the correct
    local date for that offset, which differs from the raw UTC date when the offset crosses
    a calendar boundary.
    """
    from datetime import timedelta
    from shopping_replenisher.history import _to_local_date

    utc_minus_4 = timezone(timedelta(hours=-4))
    # 2026-04-10 01:30:00 UTC → 2026-04-09 21:30:00 in UTC-4 → local date is April 9
    dt_utc_aware = datetime(2026, 4, 10, 1, 30, 0, tzinfo=timezone.utc)
    dt_local_aware = dt_utc_aware.astimezone(utc_minus_4)

    # The UTC date is April 10; the UTC-4 local date is April 9
    assert dt_utc_aware.date() == date(2026, 4, 10)
    assert dt_local_aware.date() == date(2026, 4, 9)

    # _to_local_date on a naive datetime must return the naive date unchanged
    dt_naive = datetime(2026, 4, 10, 1, 30, 0)
    assert _to_local_date(dt_naive) == date(2026, 4, 10)

    # _to_local_date on a UTC-4 aware datetime must return the UTC-4 calendar date
    assert _to_local_date(dt_local_aware) == date(2026, 4, 9)


def test_to_local_date_uses_configured_timezone_when_provided() -> None:
    """Configured timezone must override the host-local timezone for aware datetimes."""

    from shopping_replenisher.history import _to_local_date

    dt_utc_aware = datetime(2026, 4, 11, 2, 30, 0, tzinfo=timezone.utc)

    assert _to_local_date(dt_utc_aware, "America/Santiago") == date(2026, 4, 10)
    assert _to_local_date(dt_utc_aware, "UTC") == date(2026, 4, 11)


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
        display_name="coca-cola",
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
        display_name="Milk",
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
