# Phase 3 — Risk Note: Strengthen CLI Behavioral Tests

## Classified Findings

- **Accepted risk**: The tests still patch the DB layer instead of exercising a real SQLite file.
  - Justification: this is explicitly out of scope in Phase 1. The stage goal is to strengthen CLI behavioral coverage without turning it into an end-to-end SQLite integration test.

- **Accepted risk**: Report writing is redirected to `tmp_path` through a thin wrapper around the real reporter function.
  - Justification: this preserves real artifact generation while avoiding filesystem pollution in the repository. The stage does not need to validate the default `reports/` path itself.

- **Deferred debt**: `tests/test_cli.py` still contains one lighter-weight wiring test (`test_handle_predict_uses_shared_pipeline_builder`) alongside the new behavioral tests.
  - Backlog relevance: acceptable to keep because the new tests now cover real behavior, but the file still mixes test styles.

## What Was Not Changed

- No production code was modified.
- No `run` command behavior was touched.
- No real SQLite end-to-end validation was added.

## What Needs Reviewer Attention

- Confirm the new tests patch only the DB layer and not scoring/selection/report serialization.
- Confirm the new tests would fail if candidate output structure or report generation contract changed.
- Confirm the accepted risks are truly covered by the explicit exclusions in the Phase 1 brief.
