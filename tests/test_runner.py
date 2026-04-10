"""Tests for the end-to-end pipeline runner."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from shopping_replenisher.config import AppConfig
from shopping_replenisher.reporter import ReportArtifacts
from shopping_replenisher.runner import RunResult, run_pipeline
from shopping_replenisher.scoring import ScoredItem
from shopping_replenisher.selection import Candidate


def test_run_pipeline_dry_run_writes_reports_and_can_notify_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dry runs should skip Todoist writes and still notify when configured for empty runs."""

    config = _build_config(dry_run_notify_empty=True)
    report_artifacts = _build_report_artifacts()
    calls: dict[str, object] = {
        "todoist_calls": [],
        "telegram_calls": [],
    }

    monkeypatch.setattr("shopping_replenisher.runner.sqlite3.connect", _fake_connect)
    monkeypatch.setattr("shopping_replenisher.runner.fetch_active_items", lambda conn, project_id: [])
    monkeypatch.setattr(
        "shopping_replenisher.runner.fetch_completion_event_rows",
        lambda conn, project_id: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.fetch_completed_task_rows",
        lambda conn, project_id: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.build_purchase_occurrences",
        lambda completion_events, completed_tasks: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.build_item_histories",
        lambda occurrences: {},
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.select_candidates",
        lambda histories, active_items, config, today: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.write_report_artifacts",
        lambda candidates, reports_root, generated_at: report_artifacts,
    )

    def fake_create_task(config: AppConfig, candidate: Candidate) -> str:
        calls["todoist_calls"].append(candidate.scored_item.canonical_name)
        return "unexpected"

    def fake_send_run_summary(
        config: AppConfig,
        candidates: list[Candidate],
        added_task_ids: list[str],
    ) -> None:
        calls["telegram_calls"].append(
            {
                "candidate_names": [candidate.scored_item.canonical_name for candidate in candidates],
                "added_task_ids": added_task_ids,
            }
        )

    monkeypatch.setattr("shopping_replenisher.runner.create_task", fake_create_task)
    monkeypatch.setattr("shopping_replenisher.runner.send_run_summary", fake_send_run_summary)

    result = run_pipeline(config, apply_mode=False)

    assert result == RunResult(
        candidates=[],
        added_task_ids=[],
        report_artifacts=report_artifacts,
        apply_mode=False,
    )
    assert calls["todoist_calls"] == []
    assert calls["telegram_calls"] == [
        {
            "candidate_names": [],
            "added_task_ids": [],
        }
    ]


def test_run_pipeline_apply_mode_creates_tasks_and_sends_summary(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Apply mode should create Todoist tasks for auto-add candidates and notify Telegram."""

    config = _build_config(dry_run_notify_empty=False)
    report_artifacts = _build_report_artifacts()
    candidates = [
        _build_candidate("milk", "now", True, is_active=False),
        _build_candidate("bread", "optional", False, is_active=False),
    ]
    skipped_active_candidate = _build_candidate("eggs", "optional", False, is_active=True)
    calls: dict[str, object] = {
        "todoist_calls": [],
        "telegram_calls": [],
    }

    monkeypatch.setattr("shopping_replenisher.runner.sqlite3.connect", _fake_connect)
    monkeypatch.setattr("shopping_replenisher.runner.fetch_active_items", lambda conn, project_id: [])
    monkeypatch.setattr(
        "shopping_replenisher.runner.fetch_completion_event_rows",
        lambda conn, project_id: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.fetch_completed_task_rows",
        lambda conn, project_id: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.build_purchase_occurrences",
        lambda completion_events, completed_tasks: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.build_item_histories",
        lambda occurrences: {},
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.select_candidates",
        lambda histories, active_items, config, today: candidates,
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.write_report_artifacts",
        lambda candidates, reports_root, generated_at: report_artifacts,
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner._build_skipped_active_candidates",
        lambda histories, active_items, today: [skipped_active_candidate],
    )

    def fake_create_task(config: AppConfig, candidate: Candidate) -> str:
        calls["todoist_calls"].append(candidate.scored_item.canonical_name)
        return f"task-{candidate.scored_item.canonical_name}"

    def fake_send_run_summary(
        config: AppConfig,
        summary_candidates: list[Candidate],
        added_task_ids: list[str],
    ) -> None:
        calls["telegram_calls"].append(
            {
                "candidate_names": [
                    candidate.scored_item.canonical_name for candidate in summary_candidates
                ],
                "added_task_ids": added_task_ids,
            }
        )

    monkeypatch.setattr("shopping_replenisher.runner.create_task", fake_create_task)
    monkeypatch.setattr("shopping_replenisher.runner.send_run_summary", fake_send_run_summary)

    result = run_pipeline(config, apply_mode=True)

    assert result == RunResult(
        candidates=candidates,
        added_task_ids=["task-milk"],
        report_artifacts=report_artifacts,
        apply_mode=True,
    )
    assert calls["todoist_calls"] == ["milk"]
    assert calls["telegram_calls"] == [
        {
            "candidate_names": ["milk", "bread", "eggs"],
            "added_task_ids": ["task-milk"],
        }
    ]


def _build_config(*, dry_run_notify_empty: bool) -> AppConfig:
    """Build a config object for runner tests."""

    return AppConfig(
        todoist_db_path=Path("/tmp/todoist.db"),
        todoist_api_token="todoist-token",
        shopping_project_id="project-id",
        telegram_bot_token="bot-token",
        telegram_chat_id="chat-id",
        auto_apply=False,
        max_items_per_run=5,
        prediction_window_days=7,
        min_pattern_occurrences=4,
        min_confidence="medium",
        buy_soon_days=7,
        ignored_items=frozenset(),
        enable_completion_events_backfill=True,
        todoist_task_prefix="",
        log_level="INFO",
        timezone="your_timezone",
        overrule_active_duplicates=False,
        forgotten_ratio_threshold=1.75,
        dry_run_notify_empty=dry_run_notify_empty,
    )


def _build_report_artifacts() -> ReportArtifacts:
    """Build report-artifact paths for runner tests."""

    return ReportArtifacts(
        report_dir=Path("reports/20260409T120000"),
        summary_json_path=Path("reports/20260409T120000/summary.json"),
        summary_md_path=Path("reports/20260409T120000/summary.md"),
        candidates_csv_path=Path("reports/20260409T120000/candidates.csv"),
    )


def _build_candidate(
    canonical_name: str,
    candidate_class: str,
    auto_add: bool,
    *,
    is_active: bool,
) -> Candidate:
    """Build a representative candidate for runner tests."""

    return Candidate(
        scored_item=ScoredItem(
            canonical_name=canonical_name,
            original_names={canonical_name.title()},
            occurrence_count=4,
            unique_days=4,
            gaps=[7, 7, 7],
            typical_gap=7.0,
            gap_stddev=0.0,
            last_purchased=date(2026, 4, 2),
            days_since_last=7,
            overdue_ratio=1.0,
            is_active=is_active,
            confidence="medium",
        ),
        candidate_class=candidate_class,
        auto_add=auto_add,
    )


class _FakeConnection:
    """Minimal context-manager connection for runner tests."""

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
