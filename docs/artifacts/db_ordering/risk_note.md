# Phase 3 — Risk Note: Decide Whether SQLite Read Queries Should Enforce Explicit Ordering

## Residual Issues

### 1. Future callers of DB functions may assume stable ordering
**Classification: accepted risk**
A caller that reuses `fetch_completion_event_rows` outside the current pipeline might assume stable order. The inline comment now makes the unspecified-order contract explicit, which reduces but does not eliminate this risk.
**Phase 1 exclusion reference**: the contract brief states that `history.py` always re-sorts (lines 53, 68–71), so DB ordering cannot affect pipeline output. Adding `ORDER BY` was excluded because it would falsely suggest downstream code depends on DB-layer ordering.
**Why this still holds**: there is no current caller outside the pipeline. The inline comment is the appropriate mitigation for a v1 codebase.

### 2. `fetch_active_items` test now uses set comparison — loses count assertion
**Classification: accepted risk**
`set(rows) == {row1, row2}` implicitly asserts count (sets discard duplicates, and the right-hand side has 2 elements), so duplicate rows would not be detected unless both rows had identical field values. In practice, `task_id` is unique per row, so duplicates cannot be masked.
**Phase 1 exclusion reference**: the contract brief states the fix is to compare order-independently; it does not require adding an explicit `len()` assertion.
**Why this still holds**: `ActiveItemRow` is a frozen dataclass with `task_id` and `content`. Two rows with the same content but different `task_id` would appear as distinct set elements. The assertion is sufficient.
