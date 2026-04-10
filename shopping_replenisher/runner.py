"""End-to-end pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import logging
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from shopping_replenisher.config import AppConfig
from shopping_replenisher.db import (
    fetch_active_items,
    fetch_completed_task_rows,
    fetch_completion_event_rows,
)
from shopping_replenisher.history import build_item_histories, build_purchase_occurrences
from shopping_replenisher.reporter import ReportArtifacts, write_report_artifacts
from shopping_replenisher.selection import Candidate, select_candidates
from shopping_replenisher.telegram import TelegramAPIError, send_run_summary
from shopping_replenisher.todoist_api import TodoistAPIError, create_task


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunResult:
    """Outcome of a pipeline run."""

    candidates: list[Candidate]
    added_task_ids: list[str]
    report_artifacts: ReportArtifacts | None
    apply_mode: bool
    failed_items: list[str]


def run_pipeline(config: AppConfig, apply_mode: bool) -> RunResult:
    """Run the full local pipeline, with optional external side effects."""

    logger.info("run started apply_mode=%s", apply_mode)

    try:
        with sqlite3.connect(config.todoist_db_path) as conn:
            active_items = fetch_active_items(conn, config.shopping_project_id)
            completion_events = fetch_completion_event_rows(conn, config.shopping_project_id)
            completed_tasks = fetch_completed_task_rows(conn, config.shopping_project_id)
    except sqlite3.Error:
        logger.error("failed reading Todoist SQLite db_path=%s", config.todoist_db_path)
        raise

    occurrences = build_purchase_occurrences(completion_events, completed_tasks)
    histories = build_item_histories(occurrences)
    today = _resolve_today(config)
    candidates = select_candidates(
        histories=histories,
        active_items=active_items,
        config=config,
        today=today,
    )

    auto_add_candidates = [candidate for candidate in candidates if candidate.auto_add]
    optional_candidates = [
        candidate for candidate in candidates if candidate.candidate_class == "optional"
    ]

    logger.info(
        "candidates selected total=%s auto_add=%s optional=%s",
        len(candidates),
        len(auto_add_candidates),
        len(optional_candidates),
    )

    report_artifacts: ReportArtifacts | None = None
    if apply_mode and auto_add_candidates:
        generated_at = _resolve_generated_at(config)
        report_artifacts = write_report_artifacts(
            candidates,
            reports_root=Path("reports"),
            generated_at=generated_at,
        )
        logger.info("report written path=%s", report_artifacts.report_dir)

    added_task_ids: list[str] = []
    added_candidates: list[Candidate] = []
    failed_items: list[str] = []

    if apply_mode:
        for candidate in auto_add_candidates:
            item_name = candidate.scored_item.canonical_name
            try:
                task_id = create_task(config, candidate)
            except TodoistAPIError as exc:
                failed_items.append(item_name)
                logger.error("task creation failed item=%s error=%s", item_name, exc)
                continue

            added_task_ids.append(task_id)
            added_candidates.append(candidate)
            logger.info("task created item=%s task_id=%s", item_name, task_id)

        if added_task_ids:
            summary_candidates = added_candidates + optional_candidates
            try:
                send_run_summary(config, summary_candidates, added_task_ids)
                logger.info("telegram notification sent added_count=%s", len(added_task_ids))
            except TelegramAPIError as exc:
                logger.error("telegram notification failed error=%s", exc)
        elif failed_items:
            logger.error("all Todoist writes failed candidate_count=%s", len(auto_add_candidates))

    logger.info(
        "run summary candidates_found=%s added_count=%s optional_count=%s failed_count=%s",
        len(candidates),
        len(added_task_ids),
        len(optional_candidates),
        len(failed_items),
    )

    return RunResult(
        candidates=candidates,
        added_task_ids=added_task_ids,
        report_artifacts=report_artifacts,
        apply_mode=apply_mode,
        failed_items=failed_items,
    )


def _resolve_today(config: AppConfig) -> date:
    """Resolve the current date using the configured timezone when valid."""

    if config.timezone is None:
        return date.today()
    try:
        return datetime.now(ZoneInfo(config.timezone)).date()
    except ZoneInfoNotFoundError:
        return date.today()


def _resolve_generated_at(config: AppConfig) -> datetime:
    """Resolve the report timestamp using the configured timezone when valid."""

    if config.timezone is None:
        return datetime.now()
    try:
        return datetime.now(ZoneInfo(config.timezone))
    except ZoneInfoNotFoundError:
        return datetime.now()
