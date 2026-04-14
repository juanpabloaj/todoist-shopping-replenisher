# Phase 1 — Contract Brief: Strengthen CLI Tests

## Stage
Strengthen CLI tests so they validate behavior, not only mocked wiring (technical_debt.md, Medium Priority)

## Proportionality
No new config. Main execution path not modified. No new external callers. Phase 1 reduced.

**Question**: what contract or assumption changes in this stage?

**Answer**: adds at least one test for `predict` that patches only the SQLite DB layer and lets the real pipeline run — scoring, selection, report writing, and JSON serialization. This catches behavioral regressions that the current all-mocked test cannot.

## What the current test proves (and what it doesn't)
`test_handle_predict_uses_shared_pipeline_builder` patches `build_pipeline_candidates`, `resolve_generated_at`, `write_report_artifacts`, and `build_summary_payload`. It proves that `_handle_predict` calls the shared helper and returns 0. It does **not** protect against:
- Regressions in `build_pipeline_candidates` behavior (scoring, selection, deduplication)
- Wrong JSON output structure from `build_summary_payload`
- `write_report_artifacts` failing to write the expected files
- `--json` flag producing invalid or structurally incorrect output

## Tests to add

### Test 1 — `test_handle_predict_json_output_has_expected_structure`
- Patch only: `shopping_replenisher.runner.sqlite3.connect`, `fetch_active_items`, `fetch_completion_event_rows`, `fetch_completed_task_rows` (return empty lists — no history → 0 candidates)
- Let real code run: `build_pipeline_candidates`, `build_purchase_occurrences`, `build_item_histories`, `select_candidates`, `write_report_artifacts`, `build_summary_payload`
- Use `tmp_path` for reports root to avoid filesystem pollution
- Capture stdout with `capsys`
- Assert: return code 0, JSON output parses correctly, top-level keys `"candidates"` and `"candidate_count"` are present, `"candidates"` is a list

### Test 2 — `test_handle_predict_with_history_produces_scored_candidates`
- Provide minimal fixture completion history via mocked `fetch_completion_event_rows` or `fetch_completed_task_rows` returning real-shaped rows for one item with enough occurrences to produce a scored candidate
- Let the full pipeline run (scoring, selection)
- Assert: at least one candidate is produced with correct structure (`canonical_name`, `candidate_class`, `auto_add`)
- This test fails if scoring or selection logic changes in a way that drops candidates

## Out of scope / exclusions
- No changes to `cli.py` or `runner.py` — test-only
- No test for `run` command behavioral path (covered by `test_runner.py`)
- No end-to-end test with real SQLite (that is Phase 5 territory)
**Invariant**: `build_pipeline_candidates` and the full pipeline are already tested in isolation in `test_runner.py` and `test_history.py`. These CLI tests verify that `_handle_predict` wires them correctly and produces the right output contract.

## What the reviewer will check in Phase 4
- Each new test patches only the DB layer, not the pipeline logic
- JSON output structure is verified, not just return code
- Tests would fail if `build_summary_payload` or `select_candidates` changed their output contract
- `tmp_path` is used so tests don't write to `reports/`
