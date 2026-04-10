# Development Guidelines

## Language

All code, comments, docstrings, commit messages, and documentation must be written in **English**.

## Incremental Development

Development follows incremental stages defined in `ROADMAP.md`. Rules:

- Each stage must have tests before moving to the next
- Each stage must be manually validated on real data before proceeding
- Do not start a new stage until the current one is complete and tested
- Stages and their status are tracked in `ROADMAP.md`
- The roadmap is a reference, not a contract — it can be adapted if requirements or understanding evolves

## Sensitive Information

Never include in code, configuration files, or documentation:

- Absolute paths (`/Users/user/...`, `/home/user/...`)
- Machine or OS-specific information
- Developer names or personal information
- Real credentials (API tokens, bot tokens)
- Real IDs (Todoist project IDs, Telegram chat IDs)

Use placeholders in examples:

```env
TODOIST_DB_PATH=/path/to/todoist.db
SHOPPING_PROJECT_ID=YOUR_PROJECT_ID
TODOIST_API_TOKEN=your_token_here
```

## Environment Variables

- Never commit `.env` — it is git-ignored
- Always keep `.env.example` up to date with all required variables (empty values)
- Load configuration exclusively from environment variables via `.env`

## Dependencies

- Use `uv` for dependency management
- Use `.venv` for the virtual environment: `uv venv`
- Add dependencies with: `uv add <package>`
- Add dev dependencies with: `uv add --dev <package>`

## Code Formatting

- Format all code with `ruff` before committing:
  ```bash
  uv run ruff format .
  uv run ruff check .
  ```

## Testing

- Use `pytest` for all tests
- Run tests with: `uv run pytest`
- Tests live in `tests/`
- Each module must have a corresponding test file: `tests/test_<module>.py`
- Tests must pass before moving to the next development stage

## Python Version

Specify the required Python version in `pyproject.toml`. Minimum: Python 3.11.

## Type Hints

Use type hints in all function signatures and return types. Example:

```python
def build_item_histories(
    occurrences: list[PurchaseOccurrence],
) -> dict[str, ItemHistory]:
    ...
```

Not enforced automatically in v1, but required as a convention in all new code.

## Git

- Do not commit: `.env`, `data/`, `reports/`, `.venv/`, `__pycache__/`
- See `.gitignore` for the full list
