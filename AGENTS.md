# Repository Guidelines

## Project Structure & Module Organization

Core code lives in `shopping_replenisher/`. Key modules are:

- `cli.py` for entry points
- `runner.py` for end-to-end orchestration
- `db.py`, `history.py`, `normalize.py`, `scoring.py`, and `selection.py` for the prediction pipeline
- `todoist_api.py`, `telegram.py`, and `reporter.py` for integrations and local artifacts

Tests live in `tests/` and mirror module names, for example `tests/test_scoring.py`. Project docs and design references are in `DEVELOPMENT.md`, `DESIGN.md`, `ROADMAP.md`, and `docs/`.

## Build, Test, and Development Commands

- `uv run pytest` runs the full test suite.
- `uv run pytest tests/test_runner.py` runs a focused test file.
- `uv run python -m shopping_replenisher.cli predict --json` runs the local diagnostic pipeline and writes `reports/<timestamp>/`.
- `uv run python -m shopping_replenisher.cli run` executes the dry-run pipeline with no external writes.
- `uv run python -m shopping_replenisher.cli run --apply` creates Todoist tasks and may send Telegram if items were added.

## Coding Style & Naming Conventions

Use Python 3.11+ with full type hints on all function signatures. Keep code, comments, docstrings, commits, and docs in English. Follow the existing module naming pattern: lowercase filenames, `snake_case` functions, `PascalCase` dataclasses. Format and lint before review:

- `uv run ruff format .`
- `uv run ruff check .`

## Testing Guidelines

Use `pytest`. Add or update tests for every behavior change, especially around Todoist/Telegram side effects, config parsing, and SQLite schema assumptions. Test files should follow `tests/test_<module>.py`. Prefer fixtures and mocked HTTP calls over real network access.

## Review Standards

Do not treat "tests pass" as sufficient closure. Each completed change should include:

- a happy-path test
- a failure-path or invalid-input test
- a direct regression test for any real bug found during validation

When a real bug is discovered, search for the same class of issue across the repo before closing the fix. Examples: timezone consistency, env-var validation, duplicated pipeline logic, and external HTTP client behavior. Any new external integration must ship with explicit timeouts, useful error wrapping, and logs that are actionable in cron or unattended runs.

## Commit & Pull Request Guidelines

Recent history uses short imperative commit messages such as `implement stage 11: logging, hardening, and operational quality`. Follow that style: lead with the action, then scope if useful. Pull requests should include:

- a brief summary of behavior changes
- any config or schema assumptions
- test evidence, for example `uv run pytest`

## Security & Configuration Tips

Never commit `.env`, real API tokens, chat IDs, project IDs, or machine-specific paths. Keep `.env.example` updated whenever config changes. External APIs intentionally do not retry automatically; cron is the retry mechanism.
