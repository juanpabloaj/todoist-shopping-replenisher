"""Tests for CLI helper behavior."""

from __future__ import annotations

from datetime import date, datetime, timedelta
import json
from pathlib import Path

import pytest

from shopping_replenisher.cli import _handle_inspect, _handle_predict, main
from shopping_replenisher.config import AppConfig
from shopping_replenisher.db import CompletionRow
from shopping_replenisher.reporter import write_report_artifacts as real_write_report_artifacts
from shopping_replenisher.scoring import ScoredItem
from shopping_replenisher.selection import Candidate


def test_handle_predict_uses_shared_pipeline_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    """Predict should delegate candidate building to the shared runner helper."""

    config = _build_config()
    expected_candidates = [
        Candidate(
            scored_item=ScoredItem(
                canonical_name="milk",
                display_name="Milk",
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
    calls: dict[str, object] = {}

    monkeypatch.setattr(
        "shopping_replenisher.cli.build_pipeline_candidates",
        lambda config: calls.setdefault("candidates", expected_candidates),
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.resolve_generated_at",
        lambda config: __import__("datetime").datetime(2026, 4, 9, 12, 0, 0),
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.write_report_artifacts",
        lambda candidates, reports_root, generated_at, payload=None: calls.setdefault(
            "artifacts",
            type(
                "Artifacts",
                (),
                {"report_dir": Path("reports/20260409T120000000000")},
            )(),
        ),
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.build_summary_payload",
        lambda candidates, generated_at: {"candidates": len(candidates)},
    )

    result = _handle_predict(config, output_json=False)

    assert result == 0
    assert calls["candidates"] == expected_candidates


def test_handle_predict_json_output_has_expected_structure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Predict should emit valid JSON and write reports when the real pipeline returns no candidates."""

    config = _build_config(todoist_db_path=tmp_path / "todoist.db")

    monkeypatch.setattr("shopping_replenisher.runner.sqlite3.connect", _fake_connect)
    monkeypatch.setattr(
        "shopping_replenisher.runner.fetch_active_items",
        lambda conn, project_id: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.fetch_completion_event_rows",
        lambda conn, project_id: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.fetch_completed_task_rows",
        lambda conn, project_id: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.resolve_generated_at",
        lambda config: datetime(2026, 4, 13, 12, 0, 0),
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.write_report_artifacts",
        lambda candidates, reports_root, generated_at, payload=None: real_write_report_artifacts(
            candidates,
            reports_root=tmp_path,
            generated_at=generated_at,
            payload=payload,
        ),
    )

    result = _handle_predict(config, output_json=True)

    stdout = capsys.readouterr().out
    payload = json.loads(stdout)

    assert result == 0
    assert "candidates" in payload
    assert "candidate_count" in payload
    assert isinstance(payload["candidates"], list)
    assert (tmp_path / "20260413T120000000000" / "summary.json").exists()


def test_handle_predict_with_history_produces_scored_candidates(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Predict should produce scored candidates when the DB layer returns real history rows."""

    config = _build_config(todoist_db_path=tmp_path / "todoist.db")
    today = date.today()
    completion_events = [
        CompletionRow(
            task_id=f"T-{index}",
            content="Milk",
            completed_at=datetime.combine(
                today - timedelta(days=days_ago),
                datetime.min.time(),
            ),
        )
        for index, days_ago in enumerate((35, 28, 21, 14, 7), start=1)
    ]

    monkeypatch.setattr("shopping_replenisher.runner.sqlite3.connect", _fake_connect)
    monkeypatch.setattr(
        "shopping_replenisher.runner.fetch_active_items",
        lambda conn, project_id: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.fetch_completion_event_rows",
        lambda conn, project_id: completion_events,
    )
    monkeypatch.setattr(
        "shopping_replenisher.runner.fetch_completed_task_rows",
        lambda conn, project_id: [],
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.resolve_generated_at",
        lambda config: datetime(2026, 4, 13, 12, 0, 0),
    )
    monkeypatch.setattr(
        "shopping_replenisher.cli.write_report_artifacts",
        lambda candidates, reports_root, generated_at, payload=None: real_write_report_artifacts(
            candidates,
            reports_root=tmp_path,
            generated_at=generated_at,
            payload=payload,
        ),
    )

    result = _handle_predict(config, output_json=True)

    stdout = capsys.readouterr().out
    payload = json.loads(stdout)

    assert result == 0
    assert payload["candidate_count"] >= 1
    first_candidate = payload["candidates"][0]
    assert first_candidate["canonical_name"] == "milk"
    assert first_candidate["display_name"] == "Milk"
    assert first_candidate["candidate_class"] in {"now", "soon", "optional"}
    assert isinstance(first_candidate["auto_add"], bool)


def test_main_predict_allows_missing_write_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Predict should load local config without Todoist or Telegram write credentials."""

    monkeypatch.setenv("TODOIST_DB_PATH", "/tmp/todoist.db")
    monkeypatch.setenv("SHOPPING_PROJECT_ID", "project-id")
    monkeypatch.delenv("TODOIST_API_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    monkeypatch.setattr("shopping_replenisher.cli._handle_predict", lambda config, output_json: 0)

    result = main(["predict"])

    assert result == 0


def test_main_run_apply_requires_write_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Apply mode should still fail fast when write credentials are missing."""

    monkeypatch.setenv("TODOIST_DB_PATH", "/tmp/todoist.db")
    monkeypatch.setenv("SHOPPING_PROJECT_ID", "project-id")
    monkeypatch.delenv("TODOIST_API_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    with pytest.raises(SystemExit) as exc_info:
        main(["--dotenv-path", "tests/does-not-exist.env", "run", "--apply"])

    assert exc_info.value.code == 2


def test_handle_inspect_rejects_missing_required_tables(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Inspect should fail when the configured SQLite source is missing pipeline tables."""

    config = _build_config(todoist_db_path=tmp_path / "missing-tables.db")

    with caplog.at_level("ERROR"):
        result = _handle_inspect(config)

    assert result == 2
    assert "missing_tables=completed_tasks, completion_events, tasks" in caplog.text


def _build_config(*, todoist_db_path: Path | None = None) -> AppConfig:
    """Build a config object for CLI tests."""

    return AppConfig(
        todoist_db_path=todoist_db_path or Path("/tmp/todoist.db"),
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
