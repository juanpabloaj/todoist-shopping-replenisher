# Review Checklist

Use this checklist before marking a stage or feature as done.

## Config

- Every new environment variable is reflected in `shopping_replenisher/config.py`, `.env.example`, and relevant docs.
- Invalid values fail during config load with `ConfigError`, not later in runtime.
- Config changes have at least one valid-case test and one invalid-case test.

## Time And Dates

- Date logic uses one timezone model across history building, scoring, runner, and reports.
- If `TIMEZONE` is configured, aware datetimes are interpreted with that timezone consistently.
- Tests include timezone-aware datetimes, not only naive datetimes.

## Pipeline Contracts

- If a helper signature changes, all call sites and mocks are updated.
- Shared pipeline logic is not duplicated without reason.
- CLI and runner behavior stay aligned where they share business rules.

## External Integrations

- Every HTTP request has an explicit timeout.
- HTTP clients wrap network and response failures with actionable context.
- Tests cover payload shape, timeout usage, and at least one failure path.

## Logging And Operations

- Logs are useful for unattended runs and include enough context to diagnose failures.
- Logs do not expose secrets, real tokens, chat IDs, project IDs, or local machine paths unnecessarily.
- Important flows emit a structured summary line at the end.

## Tests

- Each real bug gets a direct regression test.
- Do not count a heavily mocked wiring test as full behavioral coverage.
- Verify that reverting the bug fix would actually fail at least one test.

## Bug-Fix Rule

When a bug is found in production validation or real-data runs:

- fix the immediate bug
- search the repo for the same class of bug
- add the missing regression test
- record any remaining operational risk if the fix is partial

## Final Verification

- Run `uv run pytest`
- Run `uv run ruff format .`
- Run `uv run ruff check .`
