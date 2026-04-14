# Phase 3 — Risk Note: Reduce Duplicated Pipeline Logic

## Residual Risks

- `cli.py` still imports a private helper (`_resolve_generated_at`) from `runner.py`. This is acceptable for now because the goal was deduplication without creating a new module, but it still creates a soft coupling between CLI and runner internals.
- The shared helper centralizes the pipeline build path, which is good for consistency, but any future bug in `build_pipeline_candidates()` now affects both `predict` and `run`.

## What Was Not Fully Reworked

- Report writing remains split between `predict` and `run` because the behaviors are intentionally different.
- Time resolution helpers were only partially deduplicated per the agreed contract. `_resolve_today()` is no longer duplicated in `cli.py`, but only `_resolve_generated_at()` is imported there because `predict` does not need `_resolve_today()` directly after the refactor.

## What Needs Reviewer Attention

- Confirm no dead code remains in `cli.py` after removing the duplicated helpers and `_build_prediction_candidates()`.
- Confirm the `predict` path now has the same `sqlite3.Error` logging behavior as `run`.
- Confirm the new runner helper did not introduce misleading ownership by living in `runner.py` instead of a neutral shared module.

## Real-Data Validation Consideration

- This change should be low risk in behavior, but a real `predict --json` run remains the best validation that the deduplicated path still behaves the same outside tests.
