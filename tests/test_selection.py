"""Tests for candidate selection."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from shopping_replenisher.config import AppConfig
from shopping_replenisher.db import ActiveItemRow
from shopping_replenisher.history import ItemHistory, PurchaseOccurrence
from shopping_replenisher.selection import select_candidates


def test_select_candidates_filters_and_ranks_results() -> None:
    """Selection should apply ignored-items, active-item, confidence, and ranking rules."""

    histories = {
        "milk": _build_history(
            "milk",
            ["Milk", "Milk", "Milk", "Milk"],
            [
                "2026-03-01T08:00:00",
                "2026-03-08T08:00:00",
                "2026-03-15T08:00:00",
                "2026-03-22T08:00:00",
            ],
        ),
        "egg": _build_history(
            "egg",
            ["Eggs", "Eggs", "Eggs", "Eggs"],
            [
                "2026-03-10T08:00:00",
                "2026-03-20T08:00:00",
                "2026-03-30T08:00:00",
                "2026-04-09T08:00:00",
            ],
        ),
        "bread": _build_history(
            "bread",
            ["Bread", "Bread", "Bread", "Bread"],
            [
                "2026-03-01T08:00:00",
                "2026-03-15T08:00:00",
                "2026-03-16T08:00:00",
                "2026-04-01T08:00:00",
            ],
        ),
        "compra": _build_history(
            "compra",
            ["Compra", "Compra", "Compra", "Compra"],
            [
                "2026-03-01T08:00:00",
                "2026-03-08T08:00:00",
                "2026-03-15T08:00:00",
                "2026-03-22T08:00:00",
            ],
        ),
        "coffee": _build_history(
            "coffee",
            ["Coffee", "Coffee", "Coffee"],
            ["2026-03-01T08:00:00", "2026-03-08T08:00:00", "2026-03-15T08:00:00"],
        ),
    }
    active_items = [ActiveItemRow(task_id="active-1", content="Eggs")]
    config = _build_config(
        min_pattern_occurrences=4,
        min_confidence="medium",
        buy_soon_days=7,
        max_items_per_run=2,
        ignored_items=frozenset({"compra"}),
    )

    candidates = select_candidates(
        histories=histories,
        active_items=active_items,
        config=config,
        today=date(2026, 4, 9),
    )

    assert [candidate.scored_item.canonical_name for candidate in candidates] == ["milk", "bread"]
    assert [candidate.candidate_class for candidate in candidates] == ["now", "soon"]
    assert [candidate.auto_add for candidate in candidates] == [True, True]


def test_select_candidates_limits_auto_add_classes_but_keeps_optional() -> None:
    """The per-run limit should apply to auto-add candidates only."""

    histories = {
        "milk": _build_history(
            "milk",
            ["Milk", "Milk", "Milk", "Milk"],
            [
                "2026-03-01T08:00:00",
                "2026-03-08T08:00:00",
                "2026-03-15T08:00:00",
                "2026-03-22T08:00:00",
            ],
        ),
        "rice": _build_history(
            "rice",
            ["Rice", "Rice", "Rice", "Rice"],
            [
                "2026-03-05T08:00:00",
                "2026-03-12T08:00:00",
                "2026-03-19T08:00:00",
                "2026-03-26T08:00:00",
            ],
        ),
        "coca cola": _build_history(
            "coca cola",
            ["Coca Cola", "Coca Cola", "Coca Cola", "Coca Cola"],
            [
                "2026-03-01T08:00:00",
                "2026-03-15T08:00:00",
                "2026-03-29T08:00:00",
                "2026-04-05T08:00:00",
            ],
        ),
    }
    config = _build_config(
        min_pattern_occurrences=4,
        min_confidence="medium",
        buy_soon_days=7,
        max_items_per_run=1,
        ignored_items=frozenset(),
    )

    candidates = select_candidates(
        histories=histories,
        active_items=[],
        config=config,
        today=date(2026, 4, 9),
    )

    assert [candidate.scored_item.canonical_name for candidate in candidates] == [
        "milk",
        "coca cola",
    ]
    assert [candidate.candidate_class for candidate in candidates] == ["now", "optional"]
    assert [candidate.auto_add for candidate in candidates] == [True, False]


def _build_history(
    canonical_name: str,
    contents: list[str],
    timestamps: list[str],
) -> ItemHistory:
    """Build a test item history from timestamp strings."""

    occurrences = [
        PurchaseOccurrence(
            task_id=str(index),
            content=content,
            canonical_name=canonical_name,
            completed_at=datetime.fromisoformat(timestamp),
        )
        for index, (content, timestamp) in enumerate(zip(contents, timestamps), start=1)
    ]
    occurrence_days = [occurrence.completed_at.date() for occurrence in occurrences]
    return ItemHistory(
        canonical_name=canonical_name,
        display_name=contents[-1],
        original_names=set(contents),
        occurrences=occurrences,
        occurrence_days=occurrence_days,
    )


def _build_config(
    *,
    min_pattern_occurrences: int,
    min_confidence: str,
    buy_soon_days: int,
    max_items_per_run: int,
    ignored_items: frozenset[str],
) -> AppConfig:
    """Build a config object for selection tests."""

    return AppConfig(
        todoist_db_path=Path("/tmp/todoist.db"),
        todoist_api_token="token",
        shopping_project_id="project",
        telegram_bot_token="bot-token",
        telegram_chat_id="chat-id",
        auto_apply=False,
        max_items_per_run=max_items_per_run,
        min_pattern_occurrences=min_pattern_occurrences,
        min_confidence=min_confidence,
        buy_soon_days=buy_soon_days,
        ignored_items=ignored_items,
        todoist_task_prefix="",
        log_level="INFO",
        timezone=None,
    )
