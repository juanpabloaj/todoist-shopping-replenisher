# Phase 3 — Risk Note: Reduce Duplicated Pipeline Logic

## Residual Issues

### 1. `cli.py` imported a private helper (`_resolve_generated_at`) from `runner.py`
**Classification: scope insufficiency** *(resolved before commit — renamed to `resolve_generated_at` per Phase 4 finding)*
The original implementation exported a private-named function across modules. This was caught in Phase 4 and fixed before committing: `_resolve_generated_at` was renamed to `resolve_generated_at` in `runner.py`, and the import and test in `cli.py`/`test_cli.py` were updated accordingly. No longer a residual risk.

### 2. Any future bug in `build_pipeline_candidates()` now affects both `predict` and `run`
**Classification: accepted risk**
Consolidating the pipeline into a single helper means a bug there propagates to both paths. This is an inherent consequence of the refactor's goal (single source of truth) and is preferable to silent drift between two separate implementations.
**Phase 1 exclusion reference**: "shared pipeline preparation should live behind one helper or service-level function" — the contract brief explicitly chose consolidation over isolation.
**Why this still holds after implementation**: the helper is well-tested (sqlite3.Error path, candidate selection) and the consolidated behavior was validated end-to-end via `predict --json` in Phase 5.

## What Was Not Fully Reworked
- Report writing remains split between `predict` and `run` because the behaviors are intentionally different — `predict` always writes reports; `run --apply` writes only when there are auto-add candidates.
