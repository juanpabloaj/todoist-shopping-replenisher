# Phase 1 — Contract Brief: Validate TIMEZONE During Config Load

## Stage
Validate `TIMEZONE` during config load (technical_debt.md, High Priority)

## Inputs / outputs / failure behavior
- Input: `TIMEZONE` environment variable (optional string)
- Output: `AppConfig.timezone` — either a valid IANA name string or `None`
- Failure behavior: if `TIMEZONE` is present but not a valid IANA name, `load_config()` must raise `ConfigError` immediately, before returning the config object

## Cross-module dependencies
- `shopping_replenisher/config.py` — validation added here at load time
- `shopping_replenisher/history.py` — already uses `ZoneInfo(timezone_name)` at call time; this stage makes config load consistent with that usage
- `shopping_replenisher/runner.py` and `shopping_replenisher/cli.py` — consume `config.timezone`; behavior unchanged

## New configuration behavior
- `TIMEZONE` was already optional; this stage adds validation at load time
- Valid: any IANA timezone name accepted by `ZoneInfo()` (e.g. `America/Santiago`)
- Invalid: any name that raises `ZoneInfoNotFoundError` → `ConfigError`
- Absent: `None` — valid, means host-local time is used

## Out of scope / exclusions
- No change to how `timezone_name` is used in `history.py`, `runner.py`, or `cli.py` — those modules already use `ZoneInfo()` correctly at call time. The runner and cli both have a `ZoneInfoNotFoundError` fallback that is now redundant for config-provided values but harmless to leave. **Invariant that makes this safe**: `load_config()` now rejects invalid names before the pipeline runs; the fallbacks in runner/cli will never fire for a config-provided timezone.

## What the reviewer will check in Phase 4
- `ZoneInfo(value)` is called at load time, not deferred to first use
- `ConfigError` is raised with a message containing "TIMEZONE"
- Three tests exist: valid timezone, invalid timezone, absent timezone
- Each test would fail if its corresponding branch were removed
