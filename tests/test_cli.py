"""Tests for CLI helper behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from shopping_replenisher.cli import _handle_predict
from shopping_replenisher.config import AppConfig
from shopping_replenisher.scoring import ScoredItem
from shopping_replenisher.selection import Candidate


def test_handle_predict_uses_shared_pipeline_builder(monkeypatch: pytest.MonkeyPatch) -> None:
    """Predict should delegate candidate building to the shared runner helper."""

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
        lambda candidates, reports_root, generated_at: calls.setdefault(
            "artifacts",
            type(
                "Artifacts",
                (),
                {"report_dir": Path("reports/20260409T120000")},
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
