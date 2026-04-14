# WI-001 Validation Record

## Commands Run

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
```

## Results

- `uv run ruff format .` completed with no additional changes required.
- `uv run ruff check .` passed.
- `uv run pytest` passed with `72 passed`.

## Validation Notes

- The initial validation pass surfaced two issues in the new tests:
  - `tests/test_cli.py` was unintentionally loading the repository `.env` during a missing-credentials test.
  - `tests/test_config.py` inherited `IGNORED_ITEMS` from the surrounding environment.
- Both issues were fixed before the final validation run.

## Coverage Added By This Item

- Local-command config loading without write credentials
- Apply-mode failure when write credentials are missing
- Numeric config bounds validation
- `inspect` failure on missing SQLite tables
- User-facing display-name propagation in Todoist, Telegram, and reports
- Unique report directory allocation on collision
- Partial Todoist failure handling in `run_pipeline()`
