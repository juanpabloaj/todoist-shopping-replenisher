# WI-001 Implementation Record

## Files Changed

- `shopping_replenisher/config.py`
- `shopping_replenisher/cli.py`
- `shopping_replenisher/history.py`
- `shopping_replenisher/scoring.py`
- `shopping_replenisher/reporter.py`
- `shopping_replenisher/todoist_api.py`
- `shopping_replenisher/telegram.py`
- `tests/test_cli.py`
- `tests/test_config.py`
- `tests/test_history.py`
- `tests/test_reporter.py`
- `tests/test_runner.py`
- `tests/test_scoring.py`
- `tests/test_selection.py`
- `tests/test_telegram.py`
- `tests/test_todoist_api.py`
- `README.md`
- `DESIGN.md`
- `docs/operations.md`
- `docs/artifacts/repo_improvements_review/contract.md`

## Behavior Changed

### 1. Local diagnostics no longer require write credentials

- `load_config()` now supports command-appropriate validation through `require_write_credentials`.
- `inspect`, `predict`, and dry-run `run` only require `TODOIST_DB_PATH` and `SHOPPING_PROJECT_ID`.
- `run --apply` still fails fast unless Todoist and Telegram credentials are configured.

### 2. Numeric config values now fail fast when out of supported bounds

- `MAX_ITEMS_PER_RUN` must be `>= 1`.
- `MIN_PATTERN_OCCURRENCES` must be `>= 1`.
- `BUY_SOON_DAYS` must be `>= 0`.

This closes a class of silent misconfiguration where the pipeline could be effectively disabled or skewed without any startup error.

### 3. `inspect` now validates the SQLite source

- `inspect` now opens the configured SQLite database and checks for the required pipeline tables: `tasks`, `completion_events`, and `completed_tasks`.
- It returns exit code `2` and logs a direct error if the database is unreadable or structurally incomplete.

### 4. User-facing outputs now use readable display names

- `ItemHistory` and `ScoredItem` now carry `display_name`, derived from the most recent observed raw item text for that canonical item.
- Todoist task content now uses `display_name`.
- Telegram summaries now use `display_name`.
- Report payloads now expose both `display_name` and `canonical_name`.
- Markdown and CSV report surfaces now show `display_name` to the operator while preserving `canonical_name` for traceability.

Bug-class search result:

- Fixed in `todoist_api.py`
- Fixed in `telegram.py`
- Fixed in `reporter.py`
- JSON payload contract expanded to include `display_name`

### 5. Report directories no longer silently reuse old artifacts

- Report paths now allocate a unique directory name using microsecond precision and a numeric suffix fallback when needed.
- Repeated writes with the same timestamp no longer overwrite or merge artifacts silently.

### 6. Small operability hardening during implementation

- `predict` no longer rebuilds the summary payload twice; the prebuilt payload is passed into `write_report_artifacts()`.
- Added explicit test coverage for partial Todoist write failure in `run_pipeline()`.

## Validation Run

See `validation_record.md`.

## Residual Findings

### Deferred Debt

- `runner.py` and `history.py` still contain `ZoneInfoNotFoundError` fallbacks that are redundant after config-time timezone validation. This is cleanup debt, not an active correctness bug.
- Scoring and selection boundary coverage is still lighter than ideal even after this item. Core behavior is covered, but threshold-edge tests could still be expanded further.

### Accepted for This Item

- `display_name` is currently chosen as the most recent raw name variant. This is deterministic and user-friendly, but it is not the same as “most common” or language-aware formatting. A more advanced presentation rule would need frequency tracking or explicit naming policy.

### Resolved During This Item

- Config credential over-coupling for local-only commands
- Silent numeric misconfiguration for key integer settings
- `inspect` reporting success on structurally invalid SQLite sources
- Canonical-name leakage into Todoist, Telegram, and report outputs
- Silent report directory reuse
- Missing partial-Todoist-failure regression coverage
