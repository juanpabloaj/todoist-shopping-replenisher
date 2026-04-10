"""Tests for CLI helper behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from shopping_replenisher.cli import _build_prediction_candidates
from shopping_replenisher.config import AppConfig
from shopping_replenisher.scoring import ScoredItem
from shopping_replenisher.selection import Candidate


def test_build_prediction_candidates_runs_local_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    """The predict helper should compose the local pipeline stages and return candidates."""

    config = _build_config()
    expected_candidates = [
        Candidate(
            scored_item=ScoredItem(
                canonical_name="milk",
                original_names={"Milk"},
                occurrence_count=4,
                unique_days=4,
                gaps=[7, 7, 7],
                typical_gap=7.0,
                gap_stddev=0.0,
                last_purchased=__import__("datetime").date(2026, 4, 2),
                days_since_last=7,
                overdue_ratio=1.0,
                is_active=False,
                confidence="medium",
            ),
            candidate_class="now",
            auto_add=True,
        )
    ]

    monkeypatch.setattr("shopping_replenisher.cli.sqlite3.connect", _fake_connect)
    monkeypatch.setattr(
        "shopping_replenisher.cli.fetch_active_items",
        lambda conn, project_id: ["active-items"],
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.fetch_completion_event_rows",
        lambda conn, project_id: ["completion-events"],
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.fetch_completed_task_rows",
        lambda conn, project_id: ["completed-tasks"],
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.build_purchase_occurrences",
        lambda completion_events, completed_tasks: ["occurrences"],
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.build_item_histories",
        lambda occurrences: {"milk": "history"},
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli._resolve_today",
        lambda config: __import__("datetime").date(2026, 4, 9),
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.select_candidates",
        lambda histories, active_items, config, today: expected_candidates,
    )

    candidates = _build_prediction_candidates(config)

    assert candidates == expected_candidates


def _build_config() -> AppConfig:
    """Build a config object for CLI tests."""

    return AppConfig(
        todoist_db_path=Path("/tmp/todoist.db"),
        todoist_api_token="todoist-token",
        shopping_project_id="project-id",
        telegram_bot_token="bot-token",
        telegram_chat_id="chat-id",
        auto_apply=False,
        max_items_per_run=5,
        min_pattern_occurrences=4,
        min_confidence="medium",
        buy_soon_days=7,
        ignored_items=frozenset(),
        todoist_task_prefix="",
        log_level="INFO",
        timezone=None,
    )


class _FakeConnection:
    """Minimal context-manager connection for CLI tests."""

    def __enter__(self) -> "_FakeConnection":
        """Enter the connection context manager."""

        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """Exit the connection context manager."""

        return None


def _fake_connect(path: Path) -> _FakeConnection:
    """Return a fake SQLite connection."""

    _ = path
    return _FakeConnection()
