# Phase 2 — Change Summary: Add Stronger HTTP Client Failure-Path Coverage

## Files Changed

- `tests/test_telegram.py`
- `tests/test_todoist_api.py`

## Behavior Changed

- No production behavior changed.
- Added regression coverage for existing error-handling branches in `shopping_replenisher/telegram.py` and `shopping_replenisher/todoist_api.py`.

## Tests Added

### Telegram

- `test_send_run_summary_raises_on_ok_false`
  - covers HTTP 200 with `{"ok": false}`
  - asserts `TelegramAPIError` message contains `ok`

- `test_send_run_summary_raises_on_invalid_json`
  - covers HTTP 200 with invalid JSON body
  - asserts `TelegramAPIError` message contains `JSON`

### Todoist

- `test_create_task_raises_on_invalid_json`
  - covers HTTP 200 with invalid JSON body
  - asserts `TodoistAPIError` message contains `JSON`

- `test_create_task_raises_on_missing_id`
  - covers HTTP 200 with `{}` response body
  - asserts `TodoistAPIError` message contains `id`

## Mutation Requirement

- Each new test asserts on the error message string, not only the exception type.
- If the corresponding production branch or error message is removed, the test should fail.

## Known Limitations

- This stage does not add coverage for transport-level timeout behavior because that is already covered separately through timeout argument assertions.
- This stage does not change production code; it only improves regression protection around already-implemented failure paths.
