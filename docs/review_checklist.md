# Review Checklist

Use this checklist together with `docs/agent_workflow_process.md`. That document defines the general workflow; this file records repository-specific review checks for this project.

## Config

- Every new environment variable is reflected in `shopping_replenisher/config.py`, `.env.example`, and relevant docs.
- Invalid values fail during config load with `ConfigError`, not later in runtime.
- Config changes have at least one valid-case test and one invalid-case test.
- `TIMEZONE` handling stays aligned across `shopping_replenisher/config.py`, `shopping_replenisher/history.py`, `shopping_replenisher/runner.py`, and `shopping_replenisher/cli.py`.

## Time And Dates

- Date logic uses one timezone model across history building, scoring, runner, and reports.
- If `TIMEZONE` is configured, aware datetimes are interpreted with that timezone consistently.
- Tests include timezone-aware datetimes, not only naive datetimes.

## Pipeline Contracts

- If a helper signature changes, all call sites and mocks are updated.
- Shared pipeline logic is not duplicated without reason.
- CLI and runner behavior stay aligned where they share business rules.
- SQLite schema assumptions remain explicit in `shopping_replenisher/db.py` and mirrored in `tests/test_db.py`.
- `predict` and `run` continue to respect the documented split between local diagnostics and apply-mode external writes.

## Logging And Operations

- Logs are useful for unattended runs and include enough context to diagnose failures.
- Logs do not expose secrets, real tokens, chat IDs, project IDs, or local machine paths unnecessarily.
- Important flows emit a structured summary line at the end.

## Final Verification

- Run `uv run pytest`
- Run `uv run ruff format .`
- Run `uv run ruff check .`
