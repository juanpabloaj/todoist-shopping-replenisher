# Phase 2 — Change Summary: Remove Empty Telegram Summary Test

## Files Changed

- `tests/test_telegram.py`

## Behavior Changed

- No production behavior changed.
- Removed `test_build_run_summary_message_for_empty_input_is_minimal` because it asserted on an unreachable production state.

## Rationale

- `runner.py` already guards Telegram delivery behind `if added_task_ids:`.
- The production flow should never call `send_run_summary()` for an empty-additions case.
- Keeping the test would incorrectly imply that the empty-input branch is part of the supported contract.

## Tests Added or Removed

- Removed:
  - `test_build_run_summary_message_for_empty_input_is_minimal`

## Known Limitations

- `telegram.py` still contains behavior for empty input, but it is no longer treated as a supported contract in tests.
- This stage does not remove the production branch itself; it only stops asserting on the unreachable state.
