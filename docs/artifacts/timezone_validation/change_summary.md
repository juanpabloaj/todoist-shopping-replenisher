# Phase 2 — Change Summary: Validate TIMEZONE During Config Load

## Files Changed
- `shopping_replenisher/config.py`
- `tests/test_config.py`

## Behavior Changed
- `load_config()` now reads `TIMEZONE` into a local variable before passing it to `AppConfig`
- If `TIMEZONE` is present, `ZoneInfo(value)` is called immediately; `ZoneInfoNotFoundError` is caught and re-raised as `ConfigError("Environment variable TIMEZONE must be a valid IANA timezone name.")`
- If `TIMEZONE` is absent, `config.timezone` is `None` — behavior unchanged
- `ZoneInfo` and `ZoneInfoNotFoundError` are now imported in `config.py`

## Tests Added
- `test_load_config_accepts_valid_timezone` — sets `TIMEZONE=America/Santiago`, asserts `config.timezone == "America/Santiago"`
- `test_load_config_rejects_invalid_timezone` — sets `TIMEZONE=Mars/Olympus_Mons`, asserts `ConfigError` with `"TIMEZONE"` in message
- `test_load_config_accepts_missing_timezone` — deletes `TIMEZONE` from env, asserts `config.timezone is None`

## Config / Docs Changes
- `docs/technical_debt.md` — item marked resolved

## Known Limitations
- The `ZoneInfoNotFoundError` fallbacks in `runner.py` and `cli.py` are now unreachable for config-provided timezones but were not removed (see risk note)
