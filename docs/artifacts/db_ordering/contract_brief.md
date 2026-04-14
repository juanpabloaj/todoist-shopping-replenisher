# Phase 1 — Contract Brief: Decide Whether SQLite Read Queries Should Enforce Explicit Ordering

## Stage
Decide whether SQLite read queries should enforce explicit ordering (technical_debt.md, Low Priority)

## Proportionality
Test fix + inline documentation. No main execution path change. Phase 3 abbreviated. Phase 5 not required.

**Question**: what contract or assumption changes in this stage?

**Answer**: clarifies the ordering contract for all three DB read functions. Fixes a test that encodes accidental SQLite insertion order as an assertion.

## Phase 1.5 — Judgment Check Summary

Consulted Codex before finalizing this contract. Codex agreed with the split judgment:
- Completion queries do not need `ORDER BY` — `history.py` always re-sorts the data at the Python level
- `fetch_active_items` test depends on incidental SQLite insertion order, which should be fixed without adding `ORDER BY` to SQL
- Adding `ORDER BY` to all queries would elevate ordering into the DB-layer contract when the pipeline does not require it for completion data; this hides the more important truth that `history.py` owns canonical ordering

## Decision

**Do not add `ORDER BY` to any query.** Instead:
1. Add inline comments to the completion query functions in `db.py` stating that row order is not guaranteed and ordering is handled by the Python layer
2. Fix `test_fetch_active_items_returns_typed_rows` in `test_db.py` to compare without depending on insertion order

## Changes required

### `shopping_replenisher/db.py`

Add a short inline comment to `fetch_completion_event_rows` and `fetch_completed_task_rows` stating that the functions return rows in unspecified order, and that the caller (`history.py`) is responsible for sorting.

`fetch_active_items` needs no comment — it is used only as a membership lookup and has no ordering requirement.

### `tests/test_db.py`

Fix `test_fetch_active_items_returns_typed_rows`:
- Change the assertion from exact list equality to an order-independent comparison
- Use `assert set(rows) == {ActiveItemRow(...), ActiveItemRow(...)}` or sort both sides before comparing
- The test still verifies that exactly the right rows are returned for the right project; it just stops encoding a meaningless ordering guarantee

The two completion query tests (`test_fetch_completion_event_rows_returns_typed_rows`, `test_fetch_completed_task_rows_returns_typed_rows`) each return one row, so they are unaffected.

## Out of scope / exclusions

- No `ORDER BY` added to completion queries — `history.py` already sorts all completion data at lines 53, 68–71 before any downstream consumer uses it. Adding SQL ordering would be redundant and would falsely suggest downstream code depends on DB-layer ordering.
- No changes to `history.py`, `runner.py`, or any other module
- No new test cases — only a fix to an existing assertion

**Invariant**: `build_purchase_occurrences` (line 53) and `build_item_histories` (lines 68–71) both sort before returning. DB ordering cannot affect pipeline output.

## What the reviewer will check in Phase 4

- `db.py` completion functions have inline comments about unspecified row order
- `test_fetch_active_items_returns_typed_rows` no longer depends on insertion order
- Completion query tests are unchanged (single-row, not affected)
- No `ORDER BY` was added to any query
- All tests pass
