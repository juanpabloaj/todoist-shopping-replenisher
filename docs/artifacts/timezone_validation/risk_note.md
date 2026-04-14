# Phase 3 — Risk Note: Validate TIMEZONE During Config Load

## Residual Issues

### 1. `ZoneInfoNotFoundError` fallbacks in `runner.py` and `cli.py` are now unreachable
**Classification: accepted risk**
`_resolve_today()` and `resolve_generated_at()` in `runner.py` still catch `ZoneInfoNotFoundError` and fall back to host-local time. Since `load_config()` now rejects invalid timezone names at startup, these fallbacks can never fire for a config-provided timezone.
**Phase 1 exclusion reference**: "No change to how timezone_name is used in runner.py or cli.py — the fallbacks are now redundant but harmless to leave."
**Why the exclusion still holds after implementation**: removing the fallbacks would require modifying `runner.py` and `cli.py` for defensive code that doesn't affect correctness. The risk of the existing fallbacks silently masking a bug is gone because invalid names are now rejected at load time.

### 2. Validation uses `ZoneInfo()` but does not store the `ZoneInfo` object
**Classification: accepted risk**
`load_config()` calls `ZoneInfo(value)` to validate but discards the object, storing only the string name. This means downstream code must call `ZoneInfo(config.timezone)` again. This is consistent with how `history.py`, `runner.py`, and `cli.py` all use the timezone name.
**Phase 1 exclusion reference**: no explicit exclusion was stated, but this matches the existing cross-module convention of passing the name string, not the object.
**Why this still holds**: storing the string is the existing contract across all modules. Changing it would be a broader refactor out of scope for this task.

## What Was Not Fully Verified
- No end-to-end run was captured as a formal validation record. The behavior change is limited to `load_config()` startup — an invalid timezone now terminates the process at config load with `ConfigError` instead of continuing silently. This is covered by unit tests. See validation record for the approach taken.
