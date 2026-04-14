# Phase 2 — Change Summary: Reduce Duplicated Pipeline Logic

## Files Changed

- `shopping_replenisher/runner.py`
- `shopping_replenisher/cli.py`
- `tests/test_runner.py`
- `tests/test_cli.py`

## Behavior Changed

- Added `build_pipeline_candidates(config)` in `shopping_replenisher/runner.py` as the shared DB-to-candidates pipeline helper.
- `run_pipeline()` now delegates candidate construction to `build_pipeline_candidates()`.
- `predict` in `shopping_replenisher/cli.py` now uses the same shared helper as `run`.
- `_resolve_today()` and `_resolve_generated_at()` were removed from `shopping_replenisher/cli.py`; the helpers were consolidated in `runner.py`. Per Phase 4 review, `_resolve_generated_at` was renamed to `resolve_generated_at` (removing the private prefix) before committing, since it is imported externally by `cli.py`.
- The `predict` path now logs `db_path` before re-raising `sqlite3.Error`, aligning it with the `run` path because both go through the same helper.

## Tests Added or Updated

- Updated CLI test to assert that `predict` delegates to the shared pipeline helper.
- Added runner test covering the `sqlite3.Error` path in `build_pipeline_candidates()`, including log message verification.
- Existing runner tests continue to exercise `run_pipeline()` through the shared helper.

## Config and Docs Changes

- No configuration fields changed.
- No external API behavior changed.

## Known Limitations

- `build_pipeline_candidates()` remains in `runner.py` rather than a new shared module, by design from the contract brief.
- `predict` still owns report writing locally because that behavior is intentionally different from `run`.
