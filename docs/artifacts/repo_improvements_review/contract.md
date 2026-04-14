# WI-001 Contract

## Repository Analysis Summary

This repository is already in reasonable shape for a small cron-style tool, but three issues still materially reduce usefulness or operational safety:

1. Local-only commands are over-constrained by write-only credentials.
   `inspect`, `predict`, and dry-run `run` all call the same strict `load_config()` path, which requires Todoist and Telegram write credentials even when those commands only need the SQLite database and project id. This makes diagnostics harder to run safely and unnecessarily couples analysis to production secrets.

2. User-facing outputs reuse canonical matching keys as display names.
   Canonical normalization is intentionally lossy for matching (`Azúcar -> azucar`, `papeles -> papele`). The same canonical strings are currently used in Todoist task creation, Telegram summaries, and local reports. That is a real usability bug: the machine key leaks into operator-visible surfaces.

3. Report directory naming still allows second-level collisions.
   The repository previously accepted and documented this as operating-model risk, but the failure mode is silent artifact reuse. That weakens auditability and can happen through ordinary operator behavior such as two manual `predict` runs in quick succession.

## Scope

This item will implement the following:

- Split configuration validation into command-appropriate levels so local diagnostics can run without Todoist/Telegram write credentials, while `run --apply` still requires them.
- Add bounds validation for numeric behavior settings that can currently disable or distort the pipeline silently.
- Introduce a stable human-readable display name for candidates and use it for user-visible outputs (Todoist task content, Telegram text, report payload/Markdown/CSV).
- Make report directories unique beyond second-level precision and add direct regression coverage.
- Make `inspect` validate the configured SQLite source instead of only echoing configuration presence.
- Update docs and review artifacts to match the new behavior.

## Out of Scope

- Changing the matching or scoring model itself.
- Adding new external integrations, retries, or queueing.
- Solving deeper language-aware normalization. This item fixes display leakage of canonical keys rather than changing the normalization strategy.

## Required Validation

- Targeted unit tests for config loading, CLI behavior, Todoist output content, Telegram summaries, reporter output, and any affected runner behavior.
- Repository formatting and test validation with `uv run ruff format .`, `uv run ruff check .`, and `uv run pytest`.

## Bug-Class Search Requirement

The display-name issue must be fixed across all user-facing surfaces, not only in one module. At minimum this requires reviewing:

- `shopping_replenisher/todoist_api.py`
- `shopping_replenisher/telegram.py`
- `shopping_replenisher/reporter.py`
- any JSON payloads or tests that currently expose canonical names as operator-facing labels
