"""End-to-end pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from shopping_replenisher.config import AppConfig
from shopping_replenisher.db import (
    ActiveItemRow,
    fetch_active_items,
    fetch_completed_task_rows,
    fetch_completion_event_rows,
)
from shopping_replenisher.history import ItemHistory, build_item_histories, build_purchase_occurrences
from shopping_replenisher.normalize import normalize
from shopping_replenisher.reporter import ReportArtifacts, write_report_artifacts
from shopping_replenisher.scoring import score_item_history
from shopping_replenisher.selection import Candidate, select_candidates
from shopping_replenisher.telegram import send_run_summary
from shopping_replenisher.todoist_api import create_task


@dataclass(frozen=True)
class RunResult:
    """Outcome of a pipeline run."""

    candidates: list[Candidate]
    added_task_ids: list[str]
    report_artifacts: ReportArtifacts
    apply_mode: bool


def run_pipeline(config: AppConfig, apply_mode: bool) -> RunResult:
    """Run the full local pipeline, with optional external side effects."""

    with sqlite3.connect(config.todoist_db_path) as conn:
        active_items = fetch_active_items(conn, config.shopping_project_id)
        completion_events = fetch_completion_event_rows(conn, config.shopping_project_id)
        completed_tasks = fetch_completed_task_rows(conn, config.shopping_project_id)

    occurrences = build_purchase_occurrences(completion_events, completed_tasks)
    histories = build_item_histories(occurrences)
    today = _resolve_today(config)
    candidates = select_candidates(
        histories=histories,
        active_items=active_items,
        config=config,
        today=today,
    )

    generated_at = _resolve_generated_at(config)
    report_artifacts = write_report_artifacts(
        candidates,
        reports_root=Path("reports"),
        generated_at=generated_at,
    )

    added_task_ids: list[str] = []
    summary_candidates = candidates + _build_skipped_active_candidates(
        histories=histories,
        active_items=active_items,
        today=today,
    )

    if apply_mode:
        for candidate in candidates:
            if candidate.auto_add:
                added_task_ids.append(create_task(config, candidate))
        send_run_summary(config, summary_candidates, added_task_ids)
    elif candidates or config.dry_run_notify_empty:
        send_run_summary(config, summary_candidates, added_task_ids)

    return RunResult(
        candidates=candidates,
        added_task_ids=added_task_ids,
        report_artifacts=report_artifacts,
        apply_mode=apply_mode,
    )


def _build_skipped_active_candidates(
    *,
    histories: dict[str, ItemHistory],
    active_items: list[ActiveItemRow],
    today: date,
) -> list[Candidate]:
    """Build summary-only candidates for items skipped because they are already active."""

    active_by_canonical_name = {normalize(item.content): item for item in active_items}
    skipped_candidates: list[Candidate] = []
    for canonical_name in sorted(active_by_canonical_name):
        history = histories.get(canonical_name)
        if history is None:
            continue
        scored_item = score_item_history(history, today=today, is_active=True)
        skipped_candidates.append(
            Candidate(
                scored_item=scored_item,
                candidate_class="optional",
                auto_add=False,
            )
        )
    return skipped_candidates


def _resolve_today(config: AppConfig) -> date:
    """Resolve the current date using the configured timezone when valid."""

    if config.timezone == "your_timezone":
        return date.today()

    try:
        return datetime.now(ZoneInfo(config.timezone)).date()
    except ZoneInfoNotFoundError:
        return date.today()


def _resolve_generated_at(config: AppConfig) -> datetime:
    """Resolve the report timestamp using the configured timezone when valid."""

    if config.timezone == "your_timezone":
        return datetime.now()

    try:
        return datetime.now(ZoneInfo(config.timezone))
    except ZoneInfoNotFoundError:
        return datetime.now()
