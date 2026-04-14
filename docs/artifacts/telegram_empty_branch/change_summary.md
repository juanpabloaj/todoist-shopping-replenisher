# Phase 2 — Change Summary: Decide Whether the Empty Telegram Summary Branch Should Exist

## Files Changed
- `tests/test_telegram.py` (commit 58db0bd)
- `shopping_replenisher/telegram.py` (commit 9c01bee — scope expanded after Phase 4 review)
- `tests/test_telegram.py` (commit 9c01bee — three tests updated to pass non-empty added_task_ids)

## Behavior Changed

### commit 58db0bd — remove test asserting on dead path
- Removed `test_build_run_summary_message_for_empty_input_is_minimal`
- Removed import of `_build_run_summary_message` from `test_telegram.py`
- No production code changed in this commit

### commit 9c01bee — scope expansion: enforce invariant in production
- Added guard to `send_run_summary()` in `telegram.py`: if `added_task_ids` is empty, return immediately
- Guard includes comment explaining that the runner already enforces this invariant
- Updated three existing tests that were calling `send_run_summary(..., added_task_ids=[])` — changed to `added_task_ids=["task-1"]` to respect the now-explicit contract
- This commit was triggered by the original risk note item being reclassified as **scope insufficiency**

## Why the Scope Expanded
The original contract said "test-only, no production changes." The risk note item ("The empty-input branch still exists in telegram.py") was treated as accepted risk, but it was scope insufficiency: removing the test without enforcing the invariant at the module boundary left the production code in a state that could silently allow the empty-input path. The guard in `send_run_summary()` was the correct completion of the task.

## Config / Docs Changes
- `docs/technical_debt.md` — item marked resolved
