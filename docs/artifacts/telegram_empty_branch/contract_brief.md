# Phase 1 — Contract Brief: Decide Whether the Empty Telegram Summary Branch Should Exist

## Stage
Decide whether the empty Telegram summary branch should exist (technical_debt.md, Medium Priority)

## Proportionality
Test-only change. No new config. Main execution path not modified. Phase 1 reduced.

**Question**: what contract or assumption does this stage verify?

**Answer**: `runner.py:85` already guards `send_run_summary` behind `if added_task_ids:`.
The production flow never calls Telegram with empty additions.
`test_build_run_summary_message_for_empty_input_is_minimal` tests an unreachable state.

## Decision

Remove `test_build_run_summary_message_for_empty_input_is_minimal` from `tests/test_telegram.py`.

No production code changes. The runner guard at line 85 is the correct protection and stays.

**Rationale**: a test for a path that cannot occur in production provides no regression value.
Keeping it would imply the empty-input behavior is a supported contract — it is not.

## What is NOT changing

- `telegram.py` — no changes. The function behavior for empty input is unchanged; it simply
  has no test because the scenario cannot occur.
- `runner.py` — no changes. The `if added_task_ids:` guard remains and is sufficient.

## What the reviewer will check in Phase 4

- The removed test was the only test asserting on the empty-input path (no duplicate elsewhere).
- No other test is affected by the removal.
- Production code is unchanged.
- The runner guard (`if added_task_ids:`) is confirmed as the invariant that makes empty calls impossible.
