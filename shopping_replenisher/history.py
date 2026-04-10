"""Purchase-occurrence building and item-history grouping."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from shopping_replenisher.db import CompletionRow
from shopping_replenisher.normalize import normalize


@dataclass(frozen=True)
class PurchaseOccurrence:
    """A deduplicated purchase occurrence."""

    task_id: str
    content: str
    canonical_name: str
    completed_at: datetime


@dataclass(frozen=True)
class ItemHistory:
    """Grouped history for a canonical item name."""

    canonical_name: str
    original_names: set[str]
    occurrences: list[PurchaseOccurrence]
    occurrence_days: list[date]


def build_purchase_occurrences(
    completion_events: list[CompletionRow],
    completed_tasks: list[CompletionRow],
    timezone_name: str | None = None,
) -> list[PurchaseOccurrence]:
    """Build deduplicated purchase occurrences from both history sources."""

    occurrences: list[PurchaseOccurrence] = [
        _to_purchase_occurrence(row) for row in completion_events
    ]

    for completed_task in completed_tasks:
        if _matches_existing_occurrence(
            completed_task,
            occurrences,
            timezone_name=timezone_name,
        ):
            continue
        occurrences.append(_to_purchase_occurrence(completed_task))

    return sorted(occurrences, key=lambda occurrence: occurrence.completed_at)


def build_item_histories(
    occurrences: list[PurchaseOccurrence],
    timezone_name: str | None = None,
) -> dict[str, ItemHistory]:
    """Group purchase occurrences by canonical item name."""

    grouped: dict[str, list[PurchaseOccurrence]] = {}
    for occurrence in occurrences:
        grouped.setdefault(occurrence.canonical_name, []).append(occurrence)

    histories: dict[str, ItemHistory] = {}
    for canonical_name, grouped_occurrences in grouped.items():
        sorted_occurrences = sorted(
            grouped_occurrences,
            key=lambda occurrence: occurrence.completed_at,
        )
        occurrence_days = sorted(
            {
                _to_local_date(occurrence.completed_at, timezone_name)
                for occurrence in sorted_occurrences
            }
        )
        original_names = {occurrence.content for occurrence in sorted_occurrences}
        histories[canonical_name] = ItemHistory(
            canonical_name=canonical_name,
            original_names=original_names,
            occurrences=sorted_occurrences,
            occurrence_days=occurrence_days,
        )

    return histories


def _to_purchase_occurrence(row: CompletionRow) -> PurchaseOccurrence:
    """Convert a completion row into a purchase occurrence."""

    return PurchaseOccurrence(
        task_id=row.task_id,
        content=row.content,
        canonical_name=normalize(row.content),
        completed_at=row.completed_at,
    )


def _matches_existing_occurrence(
    candidate: CompletionRow,
    existing_occurrences: list[PurchaseOccurrence],
    *,
    timezone_name: str | None = None,
) -> bool:
    """Determine whether a candidate row duplicates an existing occurrence."""

    candidate_canonical_name = normalize(candidate.content)
    for occurrence in existing_occurrences:
        if _is_strong_match(candidate, occurrence):
            return True
        if _is_medium_match(
            candidate,
            candidate_canonical_name,
            occurrence,
            timezone_name=timezone_name,
        ):
            return True
    return False


def _is_strong_match(candidate: CompletionRow, occurrence: PurchaseOccurrence) -> bool:
    """Match by task id within 5 seconds."""

    if candidate.task_id != occurrence.task_id:
        return False
    return _absolute_delta_seconds(candidate.completed_at, occurrence.completed_at) <= 5


def _is_medium_match(
    candidate: CompletionRow,
    candidate_canonical_name: str,
    occurrence: PurchaseOccurrence,
    *,
    timezone_name: str | None = None,
) -> bool:
    """Match by canonical content, same day, and within 10 seconds."""

    if candidate_canonical_name != occurrence.canonical_name:
        return False
    if _to_local_date(
        candidate.completed_at,
        timezone_name,
    ) != _to_local_date(occurrence.completed_at, timezone_name):
        return False
    return _absolute_delta_seconds(candidate.completed_at, occurrence.completed_at) <= 10


def _absolute_delta_seconds(left: datetime, right: datetime) -> float:
    """Return the absolute difference between two timestamps in seconds."""

    return abs((left - right).total_seconds())


def _to_local_date(dt: datetime, timezone_name: str | None = None) -> date:
    """Convert a datetime to a local calendar date.

    Timezone-aware datetimes are converted using the configured timezone when
    present; otherwise they fall back to the local system timezone.
    """
    if dt.tzinfo is not None:
        if timezone_name is not None:
            try:
                return dt.astimezone(ZoneInfo(timezone_name)).date()
            except ZoneInfoNotFoundError:
                return dt.astimezone().date()
        return dt.astimezone().date()
    return dt.date()
