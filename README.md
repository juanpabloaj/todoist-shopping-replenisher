# todoist-shopping-replenisher

Python tool for analyzing the purchase history of a Todoist shopping project, identifying items that likely need replenishment, and, when run in `--apply` mode, creating new Todoist tasks.

## What It Does

- Reads a local Todoist SQLite database
- Reconstructs purchase history from `completion_events` and `completed_tasks`
- Normalizes item names and deduplicates occurrences
- Computes frequency, gaps, and replenishment signals
- Classifies candidates as `now`, `soon`, or `optional`
- In apply mode, creates Todoist tasks and may send a Telegram summary

## Structure

- `shopping_replenisher/`: main application code
- `tests/`: `pytest` test suite
- `docs/`: domain rules and threshold notes
- `ROADMAP.md`: staged development plan
- `DESIGN.md`: functional design
- `DEVELOPMENT.md`: development conventions

## Requirements

- Python 3.11+
- `uv` for environment and dependency management
- A `.env` file with the required variables
- A local Todoist SQLite database, kept in sync by [todoist-local-sync](https://github.com/juanpabloaj/todoist-local-sync)

## Setup

1. Create the virtual environment:

```bash
uv venv
```

2. Install dependencies:

```bash
uv sync
```

3. Create `.env` from the example:

```bash
cp .env.example .env
```

Fill in at least:

- `TODOIST_DB_PATH`
- `TODOIST_API_TOKEN`
- `SHOPPING_PROJECT_ID`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Main Commands

Validate configuration:

```bash
uv run python -m shopping_replenisher.cli inspect
```

Generate a local prediction and report:

```bash
uv run python -m shopping_replenisher.cli predict
```

Generate a local prediction and print JSON:

```bash
uv run python -m shopping_replenisher.cli predict --json
```

Run the full pipeline in dry-run mode:

```bash
uv run python -m shopping_replenisher.cli run
```

Run the full pipeline with Todoist writes enabled:

```bash
uv run python -m shopping_replenisher.cli run --apply
```

## Testing

Run the full suite:

```bash
uv run pytest
```

Format and check style:

```bash
uv run ruff format .
uv run ruff check .
```

## Operational Notes

- `predict` always writes local reports to `reports/<timestamp>/`
- `run --apply` sends Telegram only if at least one item was successfully added
- No automatic API retries are implemented; the next cron run is the natural retry path
- Idempotency depends on the local Todoist SQLite being up to date before the next scheduled run
