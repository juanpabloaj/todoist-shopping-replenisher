# Phase 4 — Review Verdict: Strengthen CLI Behavioral Tests

## Decision: Pass

## Checklist results

- **Tests patch only the DB layer**: confirmed. Both new tests mock `sqlite3.connect` and the three `fetch_*` functions. `build_purchase_occurrences`, `build_item_histories`, `select_candidates`, `build_summary_payload`, and `write_report_artifacts` (via real wrapper) all run for real. ✅
- **Report writing is real**: test 1 verifies `(tmp_path / "20260413T120000" / "summary.json").exists()` — the real reporter writes to disk. ✅
- **Mutation protection — test 1**: if `build_summary_payload` removed `"candidates"` or `"candidate_count"` keys, the assertions fail. If `write_report_artifacts` failed to write files, the `exists()` check fails. ✅
- **Mutation protection — test 2**: if `select_candidates` returned empty, `candidate_count >= 1` fails. If `canonical_name` were removed from the JSON payload, KeyError. If `candidate_class` changed set, assertion fails. ✅
- **Fixture history is valid**: 5 weekly completions for "Milk" → normalizes to "milk", satisfies `min_pattern_occurrences=4` and `min_confidence=medium`. ✅
- **Accepted risks verified against Phase 1 exclusions**: DB-layer patching and `tmp_path` redirect both covered by explicit exclusions in contract brief. ✅
- **No production code modified**. ✅

## Phase 5
Not required. No change to the main execution path.

## Items escalated to debt
Mixed test styles in `test_cli.py` (wiring test + behavioral tests) noted as deferred debt in risk note. No action required now.
