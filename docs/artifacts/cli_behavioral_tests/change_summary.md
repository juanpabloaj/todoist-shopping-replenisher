# Phase 2 — Change Summary: Strengthen CLI Behavioral Tests

## Files Changed

- `tests/test_cli.py`

## Behavior Changed

- No production behavior changed.
- Added two behavioral tests for `_handle_predict()` that patch only the DB layer and let the real pipeline execute.

## Tests Added

- `test_handle_predict_json_output_has_expected_structure`
  - patches only the DB layer to return no history
  - lets the real pipeline, report writing, and JSON serialization run
  - asserts return code `0`, valid JSON output, required top-level keys, and report artifact creation under `tmp_path`

- `test_handle_predict_with_history_produces_scored_candidates`
  - patches only the DB layer with real-shaped `CompletionRow` history for one item
  - lets deduplication, scoring, selection, report writing, and JSON serialization run
  - asserts that at least one candidate is produced with `canonical_name`, `candidate_class`, and boolean `auto_add`

## Contract Strengthened

- `_handle_predict()` is now protected against regressions in output structure, candidate scoring/selection visibility, and local report creation.
- The CLI tests no longer prove only mocked wiring; they now exercise meaningful behavior through the real pipeline.

## Known Limitations

- The tests still patch the SQLite access layer rather than executing against a real SQLite file.
- The tests reroute report writing into `tmp_path` through a wrapper so the real report generator runs without polluting `reports/`.
