"""CLI entry points for the shopping replenisher."""

from __future__ import annotations

import argparse
from datetime import date, datetime
import json
from pathlib import Path
import sqlite3
from typing import Sequence
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from shopping_replenisher.config import AppConfig, ConfigError, load_config
from shopping_replenisher.db import (
    fetch_active_items,
    fetch_completed_task_rows,
    fetch_completion_event_rows,
)
from shopping_replenisher.history import build_item_histories, build_purchase_occurrences
from shopping_replenisher.reporter import build_summary_payload, write_report_artifacts
from shopping_replenisher.selection import select_candidates


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(prog="shopping-replenisher")
    parser.add_argument(
        "--dotenv-path",
        type=Path,
        default=None,
        help="Optional path to a .env file.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("inspect", help="Validate configuration and print a summary.")

    predict_parser = subparsers.add_parser("predict", help="Stub for local prediction flow.")
    predict_parser.add_argument(
        "--json",
        action="store_true",
        help="Reserved flag for JSON output.",
    )

    run_parser = subparsers.add_parser("run", help="Stub for the end-to-end pipeline.")
    run_parser.add_argument(
        "--apply",
        action="store_true",
        help="Reserved flag for apply mode.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the shopping replenisher CLI."""

    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.dotenv_path)
    except ConfigError as exc:
        parser.exit(status=2, message=f"Configuration error: {exc}\n")

    if args.command == "inspect":
        return _handle_inspect(config)
    if args.command == "predict":
        return _handle_predict(config, output_json=args.json)
    if args.command == "run":
        return _handle_run(config, apply_mode=args.apply)

    parser.exit(status=2, message=f"Unknown command: {args.command}\n")
    return 2


def _handle_inspect(config: AppConfig) -> int:
    """Handle the inspect subcommand."""

    print("Configuration is valid.")
    print(f"TODOIST_DB_PATH={config.todoist_db_path}")
    print(f"SHOPPING_PROJECT_ID={config.shopping_project_id}")
    print(f"AUTO_APPLY={config.auto_apply}")
    print(f"LOG_LEVEL={config.log_level}")
    return 0


def _handle_predict(config: AppConfig, output_json: bool) -> int:
    """Handle the local prediction flow."""

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
    artifacts = write_report_artifacts(
        candidates,
        reports_root=Path("reports"),
        generated_at=generated_at,
    )
    payload = build_summary_payload(candidates, generated_at=generated_at)

    print(f"Report written to {artifacts.report_dir}")
    if output_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _handle_run(config: AppConfig, apply_mode: bool) -> int:
    """Handle the run subcommand stub."""

    _ = config
    _ = apply_mode
    print("The 'run' command is not implemented yet.")
    return 0


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


if __name__ == "__main__":
    raise SystemExit(main())
