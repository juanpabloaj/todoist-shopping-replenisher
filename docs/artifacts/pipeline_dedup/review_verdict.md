# Phase 4 — Review Verdict: Reduce Duplicated Pipeline Logic

## Decision: Pass with one required fix before commit

---

## Findings

### Finding 1 — `_resolve_generated_at` is private but exported (required fix)

`runner.py` defines `_resolve_generated_at` with a leading underscore (private by convention), but `cli.py` imports it directly from `runner`. Importing a private name across modules is a code smell and creates an implicit coupling to internals.

Fix: rename to `resolve_generated_at` (remove the underscore) in `runner.py` and update the import in `cli.py`. `_resolve_today` can stay private — it is only used inside `runner.py`.

---

## Checklist results

- **No dead code in `cli.py`**: confirmed. `_resolve_today`, `_resolve_generated_at`, and `_build_prediction_candidates` are gone. No leftover imports (datetime, sqlite3, ZoneInfo, ZoneInfoNotFoundError were all removed). ✅
- **`build_pipeline_candidates` has callers**: called by `run_pipeline` and `_handle_predict`. ✅
- **sqlite3.Error path now covers predict**: `build_pipeline_candidates` has the try/except with `logger.error`. ✅
- **Test would fail if core change reverted**: `test_build_pipeline_candidates_logs_and_reraises_sqlite_errors` checks for the log message — removing the try/except or the logger.error causes it to fail. ✅
- **`test_handle_predict_uses_shared_pipeline_builder`**: if `_handle_predict` stopped calling `build_pipeline_candidates`, `calls["candidates"]` raises KeyError. Protective. ✅
- **Cross-module invariants**: timezone handling is consistent — both paths go through the same `build_pipeline_candidates`. ✅
- **No duplicated logic remaining**: confirmed.

---

## Items escalated to debt

None. The `_resolve_generated_at` naming issue is a required fix before commit, not deferred debt.

---

## What Phase 5 must verify

A real `predict --json` run should produce identical output structure to before the refactor. The validator confirms behavioral correctness of the deduplicated path with real data.
