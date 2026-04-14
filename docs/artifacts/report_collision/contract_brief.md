# Phase 1 — Contract Brief: Review Report Directory Collision Risk

## Stage
Review report directory collision risk (technical_debt.md, Low Priority)

## Proportionality
Documentation-only task. No production logic changes. Phase 3 abbreviated. Phase 5 not required.

**Question**: what contract or assumption changes in this stage?

**Answer**: makes the collision risk and the safety invariant explicit in `reporter.py`. No behavior change.

## Phase 1.5 — Judgment Check Summary

Consulted Codex before finalizing this contract. Codex agreed accepting and documenting is appropriate for this tool as currently positioned:
- Single-user, scheduled, not intended for concurrent execution
- Reports are diagnostic artifacts, not authoritative state

Codex noted the real hidden risk is near-simultaneous legitimate runs (scheduled + manual predict, quick retry after failure), not true concurrent execution. The failure mode is silent overwrite of artifacts — loss of audit clarity, not catastrophic data loss.

Codex also noted the fix would be cheap (adding microseconds to the directory name), but confirmed "acceptable to defer, but not because it would be hard to fix."

## Decision

**Accept and document the risk.** Add a comment to `write_report_artifacts` in `reporter.py` making explicit:
- That directory names are second-level precision
- That two runs in the same second would silently reuse the directory
- That the tool is designed for non-concurrent single-user operation, so this is outside the intended operating model
- The failure mode if the invariant is violated: overwritten artifacts without error or warning

## Changes required

### `shopping_replenisher/reporter.py`

Add a comment near the `report_dir = ...` line in `write_report_artifacts` documenting the collision behavior and the invariant.

## Out of scope / exclusions

- No change to directory naming precision (no microseconds added) — the tool is designed for non-concurrent single-user scheduled runs; overlapping executions are outside the intended operating model. If concurrent runs become a requirement, the fix is to use `generated_at.strftime("%Y%m%dT%H%M%S%f")` or add a UUID suffix.
- No test changes needed — collision behavior is not tested and does not need to be
- No changes to `runner.py`, `cli.py`, or any other module

**Invariant**: the tool is expected to run at most once at a time. Concurrent or near-simultaneous executions are not part of the supported operating model.

## What the reviewer will check in Phase 4

- `reporter.py` has a comment near the directory naming line that names the collision risk and the invariant
- No directory naming logic was changed
- No tests were modified
- All tests pass unchanged
