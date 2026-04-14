# Phase 2/3 — Change Summary: Decide Whether SQLite Read Queries Should Enforce Explicit Ordering

## Changes made

### `shopping_replenisher/db.py`
Added a 2-line comment to `fetch_completion_event_rows` and `fetch_completed_task_rows` stating that row order is intentionally unspecified and `history.py` owns canonical ordering.

### `tests/test_db.py`
Changed `test_fetch_active_items_returns_typed_rows` from exact list equality to set comparison — `assert set(rows) == {...}`. The test still verifies correct project scoping and row count; it no longer encodes accidental SQLite insertion order.

## Changes NOT made (per contract)
- No `ORDER BY` added to any query
- Completion query tests unchanged (single-row, not affected by ordering)
- No changes to `history.py`, `runner.py`, or any other module
