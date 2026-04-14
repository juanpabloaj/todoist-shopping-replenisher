# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Commands

```bash
uv run pytest                          # run all tests
uv run pytest tests/test_normalize.py  # run a single test file
uv run pytest -k "test_name"           # run a single test by name
uv run ruff format .                   # format code
uv run ruff check .                    # lint
uv run python -m shopping_replenisher.cli inspect   # validate config and DB
uv run python -m shopping_replenisher.cli predict   # local prediction, no writes
uv run python -m shopping_replenisher.cli predict --json  # prediction with JSON stdout
uv run python -m shopping_replenisher.cli run       # dry-run (no Todoist/Telegram)
uv run python -m shopping_replenisher.cli run --apply    # full pipeline with writes
```

All code, comments, docstrings, and commit messages must be in **English**.

## Architecture

The pipeline is a linear read → score → select → write flow, split across these modules:

- **`db.py`** — read-only SQLite queries. Three functions: `fetch_active_items`, `fetch_completion_event_rows`, `fetch_completed_task_rows`. All scoped by `project_id`. Active items filter `checked=0 AND is_deleted=0`. `completion_events` uses `parent_project_id` (not `project_id`) and `event_date` (not `completed_at`).

- **`normalize.py`** — deterministic text normalization pipeline: lowercase → NFKD accent removal → punctuation → whitespace collapse → known variants → light singular/plural heuristic. Conservative by design — no fuzzy matching.

- **`history.py`** — builds `PurchaseOccurrence` and `ItemHistory` from both DB sources. Deduplicates using a two-level hierarchical match (strong: same `task_id` + delta ≤ 5s; medium: same normalized content + same day + delta ≤ 10s). Converts UTC timestamps to local date using `ZoneInfo(TIMEZONE)` when configured, otherwise falls back to system local timezone via `.astimezone().date()`.

- **`scoring.py`** — computes `ScoredItem` features per item: gaps, `typical_gap` (median), `gap_stddev`, `overdue_ratio`, confidence (`low`/`medium`/`high`). Confidence thresholds: high = `unique_days >= 8 AND gap_stddev <= 5.5`, medium = `unique_days >= 4 AND gap_stddev <= 7`.

- **`selection.py`** — filters by `MIN_PATTERN_OCCURRENCES`, confidence, active status, `IGNORED_ITEMS`, classifies as `now`/`soon`/`optional`, ranks by `overdue_ratio`, caps auto-add at `MAX_ITEMS_PER_RUN`.

- **`runner.py`** — orchestrates the full pipeline. In apply mode: writes report artifacts only if there are auto-add candidates, creates Todoist tasks per item (catching `TodoistAPIError` individually and continuing), sends Telegram only if at least one task was added. SQLite errors are logged with context and re-raised (fatal). Exit code 1 if any Todoist write failed.

- **`reporter.py`** — writes `reports/<timestamp>/summary.json`, `summary.md`, `candidates.csv`. Always called by `predict`; called by `run --apply` only when there are auto-add candidates.

- **`telegram.py`** — sends `Overdue` / `Coming up` / `On the radar` sections. No notification for dry-run or empty apply runs.

- **`todoist_api.py`** — single function `create_task()` using REST API v2, no dependencies beyond stdlib.

- **`cli.py`** — entry point. Configures logging with timestamps from `LOG_LEVEL`. `predict` always writes reports and never calls Todoist/Telegram.

## Configuration

All configuration via `.env` (never committed). Copy `.env.example` to start. Required vars: `TODOIST_DB_PATH`, `TODOIST_API_TOKEN`, `SHOPPING_PROJECT_ID`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. `IGNORED_ITEMS` is a comma-separated list of normalized item names to exclude from scoring (e.g. `compra`). `TIMEZONE` is an optional IANA timezone name (e.g. `America/Santiago`); invalid values raise `ConfigError` at load time.

## Development Stages

Tracked in `ROADMAP.md`. The rule from `DEVELOPMENT.md`: each stage requires passing tests and manual validation on real data before advancing. Do not connect to the Todoist API until scoring is validated locally (`predict` only first).

Threshold calibration rationale is documented in `docs/threshold_notes.md`. Domain normalization and deduplication examples are in `docs/domain_rules.md`.
