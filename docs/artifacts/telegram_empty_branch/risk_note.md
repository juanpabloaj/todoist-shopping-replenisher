# Phase 3 — Risk Note: Decide Whether the Empty Telegram Summary Branch Should Exist

## Residual Issues

### 1. Empty-input branch still existed in `telegram.py` after test removal
**Classification: scope insufficiency** *(retrospective — this item caused scope expansion via commit 9c01bee)*
The original scope ("test-only, no production changes") was insufficient. Removing the test that asserted on the empty-input path without enforcing the invariant at the production boundary left `telegram.py` able to silently process an empty-additions call. When this item was reviewed independently after the initial closure, it was determined that `send_run_summary()` itself should guard against empty `added_task_ids`. The fix was added in commit 9c01bee.

**Lesson recorded**: an item that describes a production behavior inconsistency cannot be classified as "accepted risk" unless a Phase 1 exclusion explicitly covers it with a justifying invariant. "The runner already guards it" justifies not adding a *test*, but does not justify leaving the module boundary unprotected.

## What Was Fully Resolved
- `send_run_summary()` now returns immediately if `added_task_ids` is empty (commit 9c01bee)
- Three tests that incorrectly called `send_run_summary` with empty `added_task_ids` were corrected
- The empty-input path is now explicitly blocked at the Telegram client boundary, not only at the runner
