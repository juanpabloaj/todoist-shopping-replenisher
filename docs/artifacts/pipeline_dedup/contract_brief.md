# Phase 1 — Contract Brief: Reduce Duplicated Pipeline Logic

## Stage
Reduce duplicated pipeline logic between `predict` and `run` (technical_debt.md, High Priority)

## Affected modules
- `shopping_replenisher/cli.py`
- `shopping_replenisher/runner.py`

## What is duplicated today

### 1. `_resolve_today(config)` — byte-for-byte identical in both files
### 2. `_resolve_generated_at(config)` — byte-for-byte identical in both files
### 3. Pipeline build sequence — same 4-step call chain in both files:
```
fetch_active_items / fetch_completion_event_rows / fetch_completed_task_rows
→ build_purchase_occurrences
→ build_item_histories
→ select_candidates
```
Difference: `runner.py` wraps the SQLite block in `try/except sqlite3.Error` (logs + re-raises); `cli.py._build_prediction_candidates` does not.

## Proposed change

1. **Remove `_resolve_today` and `_resolve_generated_at` from `cli.py`**; keep them in `runner.py` as module-level helpers; import them in `cli.py` from `runner`.

2. **Extract a `build_pipeline_candidates(config)` function in `runner.py`** that encapsulates the full DB + pipeline sequence including `sqlite3.Error` handling. Both `run_pipeline` and `cli._build_prediction_candidates` call this function.

   Signature:
   ```python
   def build_pipeline_candidates(config: AppConfig) -> list[Candidate]:
       ...
   ```

3. **`cli._build_prediction_candidates` is replaced** by a direct call to `build_pipeline_candidates`. It may be inlined into `_handle_predict` or kept as a thin wrapper.

## Inputs / outputs / failure behavior

- Inputs: `AppConfig` (unchanged)
- Outputs: `list[Candidate]` (unchanged type and semantics)
- Failure behavior change: `predict` path will now also re-raise `sqlite3.Error` after logging (currently it propagates uncaught without a log). This is the correct behavior and aligns both paths.

## New configuration values
None.

## New invariants introduced
- `predict` and `run` paths use identical DB-to-candidates logic.
- `sqlite3.Error` on the predict path now logs `db_path` before re-raising, matching the run path.

## Open assumptions
- `build_pipeline_candidates` belongs in `runner.py` (not a new module), since `cli.py` already imports from `runner`. No new file needed.
- The `_resolve_today` / `_resolve_generated_at` helpers may either stay in `runner.py` (exported) or be moved to a shared location. Staying in `runner.py` is preferred — no new modules for two small helpers.

## What the reviewer will check in Phase 4
- No dead code remains in `cli.py` after removing the duplicates
- `cli.py` no longer defines `_resolve_today` or `_resolve_generated_at`
- `build_pipeline_candidates` in `runner.py` has at least one test that covers the sqlite3.Error path
- `_handle_predict` in `cli.py` correctly delegates to the shared helper
- Cross-module invariants (timezone, error types) remain consistent
