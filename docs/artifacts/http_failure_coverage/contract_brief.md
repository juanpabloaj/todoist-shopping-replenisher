# Phase 1 — Contract Brief: Add Stronger HTTP Client Failure-Path Coverage

## Stage
Add stronger HTTP client failure-path coverage (technical_debt.md, Medium Priority)

## Proportionality
No production code changes. No new config. No new external callers. Main execution path not modified.
Phase 1 reduced to one question: what contract or assumption does this stage verify?

**Answer**: the production error-handling paths in `telegram.py` and `todoist_api.py` already exist
but are not covered by tests. This stage adds regression tests that fail if those paths are removed.

## Affected modules (tests only)
- `tests/test_telegram.py`
- `tests/test_todoist_api.py`

## What is missing today

### telegram.py — untested paths
- `ok=false` response: `_send_message` reads `response_payload.get("ok", False)` and raises
  `TelegramAPIError("Telegram API returned ok=false.")` when false. No test exists.
- Invalid JSON response: `json.loads` raises `JSONDecodeError` → `TelegramAPIError("Telegram API
  returned invalid JSON.")`. No test exists.

### todoist_api.py — untested paths
- Invalid JSON response: `json.loads` raises `JSONDecodeError` → `TodoistAPIError("Todoist API
  returned invalid JSON.")`. No test exists.
- Response without `id`: `response_payload.get("id")` returns None/empty →
  `TodoistAPIError("Todoist API response did not include a task id.")`. No test exists.

## Tests to add

| Test name | File | Trigger | Expected error |
|---|---|---|---|
| `test_send_run_summary_raises_on_ok_false` | test_telegram.py | `{"ok": false}` response | `TelegramAPIError` with "ok" in message |
| `test_send_run_summary_raises_on_invalid_json` | test_telegram.py | non-JSON response body | `TelegramAPIError` with "JSON" in message |
| `test_create_task_raises_on_invalid_json` | test_todoist_api.py | non-JSON response body | `TodoistAPIError` with "JSON" in message |
| `test_create_task_raises_on_missing_id` | test_todoist_api.py | `{}` response (no id field) | `TodoistAPIError` with "id" in message |

## Mutation requirement
Each new test must fail if its target branch in production code is removed or the error message
changes. Verify by confirming the assertion checks a string from the actual error message.

## What the reviewer will check in Phase 4
- Each new test asserts on the specific error message, not just the exception type
- Each test would fail if its corresponding production branch were deleted
- No production code was modified
