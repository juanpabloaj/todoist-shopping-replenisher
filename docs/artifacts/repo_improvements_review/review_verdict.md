# WI-001 Review Verdict

**Reviewer:** Claude  
**Date:** 2026-04-14  
**Verdict: PASS with debt**

---

## What Was Verified

All changed files were read against the implementation record's claims. Tests were run (`72 passed`). Lint was clean. The previous blocked verdict is superseded by this one.

---

## Finding: Config credential split — PASS

`load_config(require_write_credentials=bool)` is implemented cleanly. `cli.py` sets `require_write_credentials = args.command == "run" and args.apply`, so `inspect`, `predict`, and dry-run `run` do not require Todoist or Telegram credentials.

The `AppConfig` dataclass is unchanged — write-credential fields default to `""` when `require_write_credentials=False`. The `_describe_secret` helper in `_handle_inspect` handles empty strings correctly ("not configured").

Behavioral tests:
- `test_main_predict_allows_missing_write_credentials` ✓ — predict succeeds without write credentials
- `test_main_run_apply_requires_write_credentials` ✓ — apply fails fast without them

**Debt (minor):** The implementation record claims `inspect` and `run` (dry-run) also work without write credentials. Both are correct by code inspection, but there are no explicit tests for those two paths. The claim is stated, not demonstrated.

---

## Finding: Numeric config bounds — PASS

`_get_positive_int` enforces `>= 1` for `MAX_ITEMS_PER_RUN` and `MIN_PATTERN_OCCURRENCES`. `_get_non_negative_int` enforces `>= 0` for `BUY_SOON_DAYS`. Parametrized test covers all three rejection cases. Clean.

---

## Finding: `inspect` SQLite validation — PASS

`_validate_sqlite_source` queries `sqlite_master` for the three required tables and returns a diagnostic string or `None`. `_handle_inspect` checks the return value and exits with code 2 on failure. Test `test_handle_inspect_rejects_missing_required_tables` verifies the exact log message and exit code. Clean.

One observation: `sqlite3.connect` without a `uri=True` read-only flag will create the DB file if it does not exist. For `inspect` specifically this means running against a nonexistent path will create an empty file and then report missing tables (correct behavior), but leaves an empty SQLite file as a side effect. This is the same behavior as `build_pipeline_candidates` and is acceptable for this tool.

---

## Finding: Display name — PASS

The implementation is correct and complete.

- `history.py`: `display_name = sorted_occurrences[-1].content.strip()` — most recent raw name, deterministic.
- Threaded through `ScoredItem.display_name` into all three output surfaces:
  - `todoist_api.py:_build_task_content` now uses `display_name` ✓
  - `telegram.py:_build_run_summary_message` now uses `display_name` for all three sections ✓
  - `reporter.py`: JSON payload, Markdown table, and CSV all expose `display_name`; `canonical_name` is preserved for traceability ✓

Tests verify the fix end-to-end:
- `test_create_task_posts_expected_payload` asserts `"content": "Milk"` (not `"milk"`) ✓
- `test_create_task_applies_optional_prefix` asserts `"[buy] Milk"` ✓
- `test_build_summary_payload_has_expected_json_structure` asserts `display_name: "Milk"` in serialized payload ✓
- `test_write_report_artifacts_writes_json_markdown_and_csv` asserts `"| Milk | now |..."` in Markdown and `"Milk,milk,now,..."` in CSV ✓
- `test_handle_predict_with_history_produces_scored_candidates` asserts `display_name == "Milk"` in end-to-end output ✓

The "most recent occurrence" strategy is documented in the implementation record. It is deterministic and an improvement over the status quo. The limitation (not frequency-weighted, not language-aware) is correctly noted as deferred.

---

## Finding: Report directory uniqueness — PASS

`_allocate_report_dir` uses microsecond precision (`%f` in strftime) plus a numeric suffix fallback, with `mkdir(exist_ok=False)`. Two writes at the same timestamp produce `20260409T083000000000` and `20260409T083000000000-1`. Test `test_write_report_artifacts_avoids_reusing_existing_directory` verifies this directly. The 1000-iteration cap with a `RuntimeError` fallback is appropriate for a single-user cron tool.

**Contract item 3 note:** This was flagged in my prior review as scope inflation given the existing documentation accepting the tradeoff. The implementation is sound and the test proves it. No objection to including it.

---

## Finding: Predict double-computation — PASS

`_handle_predict` now builds the payload once and passes it to `write_report_artifacts(payload=payload)`. The `payload` parameter is optional, so the runner's `run --apply` path (which doesn't need the payload externally) continues to compute it internally. Correct.

---

## Finding: Partial Todoist failure test — PASS

`test_run_pipeline_continues_after_partial_todoist_failure` covers the path where one item fails and another succeeds: `failed_items == ["milk"]`, `added_task_ids == ["task-bread"]`, and Telegram receives only the successful item. This was a real gap; it is now closed.

---

## Residual Debt (acknowledged in implementation record)

1. **`ZoneInfoNotFoundError` fallbacks in `runner.py` and `history.py`** — unreachable because `load_config` validates the timezone at startup. These are cleanup debt, not correctness issues. Correctly deferred.

2. **`inspect` and `run` (dry-run) credential behavior** — code is correct, but the behavioral claim in the implementation record lacks dedicated test coverage for these two paths.

3. **Selection and scoring boundary coverage** — still sparse. The confidence thresholds (`unique_days >= 8`, `gap_stddev <= 5.5`, etc.) do not have explicit boundary tests. Correctly deferred.

---

## Verdict

**PASS with debt.**

All five contract items are implemented, tested, and verified against the current filesystem. The three debt items above are accurately characterized in the implementation record and are not correctness issues. No regressions. 72 tests passing, lint clean.
