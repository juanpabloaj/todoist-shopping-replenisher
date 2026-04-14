# Technical Debt

Use this file as the current backlog of engineering issues that should be reviewed or corrected. Mark items as complete by changing `- [ ]` to `- [x]` and updating the notes if needed.

## High Priority

- [x] Validate `TIMEZONE` during config load
  - Problem: `TIMEZONE` is currently optional, but an invalid value does not fail fast. The code falls back silently to host-local time.
  - Why it matters: this can hide misconfiguration and produce inconsistent date handling across environments.
  - Relevant files:
    - `shopping_replenisher/config.py`
    - `shopping_replenisher/history.py`
    - `shopping_replenisher/runner.py`
    - `shopping_replenisher/cli.py`
  - Expected outcome: invalid timezone names should raise `ConfigError` during `load_config()`, with direct tests covering valid and invalid cases.
  - Resolved: `load_config()` now calls `ZoneInfo(value)` at load time and raises `ConfigError` for invalid IANA names. Three tests added: valid timezone, invalid timezone, absent timezone.

- [x] Reduce duplicated pipeline logic between `predict` and `run`
  - Problem: `shopping_replenisher/cli.py` and `shopping_replenisher/runner.py` still contain overlapping data-loading and pipeline-building logic.
  - Why it matters: this creates drift risk when business rules or signatures change.
  - Relevant files:
    - `shopping_replenisher/cli.py`
    - `shopping_replenisher/runner.py`
  - Expected outcome: shared pipeline preparation should live behind one helper or service-level function, with CLI and runner using the same contract.
  - Resolved: `build_pipeline_candidates(config)` added to `runner.py`; `run_pipeline` and `predict` both delegate to it. `_resolve_today` / `resolve_generated_at` consolidated in `runner.py`. Phase artifacts in `docs/artifacts/pipeline_dedup/`.

## Medium Priority

- [x] Add stronger HTTP client failure-path coverage
  - Problem: the clients now test payloads and timeout usage, but not all important bad-response cases.
  - Missing coverage:
    - Telegram `ok=false` response
    - Todoist invalid JSON response
    - Todoist response without `id`
  - Relevant files:
    - `tests/test_telegram.py`
    - `tests/test_todoist_api.py`
  - Expected outcome: each failure mode has a direct regression test and raises the correct wrapped error.
  - Resolved: 4 tests added (ok=false, invalid JSON x2, missing id). Each asserts on error message string. Phase artifacts in `docs/artifacts/http_failure_coverage/`.

- [x] Decide whether the empty Telegram summary branch should exist
  - Problem: `_build_run_summary_message([], []) == "Replenisher"` is still supported, but current production flow should not call Telegram with empty additions.
  - Why it matters: this is either dead behavior or an undocumented fallback path.
  - Relevant files:
    - `shopping_replenisher/telegram.py`
    - `shopping_replenisher/runner.py`
    - `tests/test_telegram.py`
  - Expected outcome: either remove the branch and its test, or document why it is intentionally kept.
  - Resolved: removed `test_build_run_summary_message_for_empty_input_is_minimal`. The `runner.py` guard `if added_task_ids:` is the real invariant. Phase artifacts in `docs/artifacts/telegram_empty_branch/`.

- [x] Strengthen CLI tests so they validate behavior, not only mocked wiring
  - Problem: `tests/test_cli.py` currently monkeypatches most of the pipeline and mainly proves composition.
  - Why it matters: this gives weak protection against behavioral regressions in `predict`.
  - Relevant files:
    - `tests/test_cli.py`
    - `shopping_replenisher/cli.py`
  - Expected outcome: at least one test should validate more realistic behavior of `predict` or its helper using less synthetic setup.
  - Resolved: two behavioral tests added that patch only the DB layer and let the real pipeline run. One verifies JSON output structure; one provides real CompletionRow history and verifies a scored candidate is produced. Phase artifacts in `docs/artifacts/cli_behavioral_tests/`.

- [x] Revisit normalization quality for conservative plural handling
  - Problem: current normalization avoids aggressive merges, but still produces awkward canonical names such as `luces -> luce` and `papeles -> papele`.
  - Why it matters: awkward canonical names can affect history grouping, readability, and created Todoist task names.
  - Relevant files:
    - `shopping_replenisher/normalize.py`
    - `tests/test_normalize.py`
    - `docs/domain_rules.md`
  - Expected outcome: either improve the heuristic safely or document the current tradeoff more explicitly.
  - Resolved: documented the tradeoff in `normalize.py` (comment in `_singularize_word`) and `docs/domain_rules.md` (new "Known Imperfect Outputs" subsection). Improving the heuristic is unsafe without language detection — stripping `-es` would break English words like `noodles`. Phase artifacts in `docs/artifacts/normalization_plural/`.

## Low Priority

- [x] Decide whether SQLite read queries should enforce explicit ordering
  - Problem: current read queries rely on implicit SQLite row order.
  - Why it matters: deterministic ordering can make reports and debugging more predictable.
  - Relevant files:
    - `shopping_replenisher/db.py`
    - `tests/test_db.py`
  - Expected outcome: either add `ORDER BY` where needed or document why ordering is intentionally deferred to later stages.
  - Resolved: no `ORDER BY` added. Inline comments added to completion query functions documenting that `history.py` owns ordering. `test_fetch_active_items_returns_typed_rows` fixed to use set comparison instead of exact list equality. Phase artifacts in `docs/artifacts/db_ordering/`.

- [x] Review report directory collision risk
  - Problem: report directories are timestamped to the second.
  - Why it matters: two runs in the same second could collide.
  - Relevant files:
    - `shopping_replenisher/reporter.py`
    - `tests/test_reporter.py`
  - Expected outcome: either accept and document the risk, or make report paths unique beyond second-level precision.
  - Resolved: accepted and documented. Comment added to `write_report_artifacts` naming the silent-overwrite failure mode and the non-concurrent operating model invariant. The fix (adding microseconds) is deferred as this tool is designed for single-user scheduled runs. Phase artifacts in `docs/artifacts/report_collision/`.

- [ ] Re-audit design and README against the final implemented behavior
  - Problem: docs have been updated incrementally across many stages and may still contain stale assumptions.
  - Why it matters: contributors may follow outdated behavior instead of the code.
  - Relevant files:
    - `README.md`
    - `DESIGN.md`
    - `DEVELOPMENT.md`
    - `ROADMAP.md`
    - `docs/`
  - Expected outcome: documentation reflects current production behavior, especially Stage 10-11 operational decisions.

## Update Rules

- Keep items concrete and actionable.
- When a task is completed, mark it done and briefly note the commit or file change that resolved it.
- If a new bug reveals a wider class of issue, add a new task here instead of burying it in commit history.
