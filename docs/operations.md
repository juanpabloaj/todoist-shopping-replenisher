# Operations Guide

## Scheduled Execution

Add the following entry to crontab (`crontab -e`):

```
12 8 * * * cd /home/user/code/todoist-shopping-replenisher && /home/user/code/todoist-shopping-replenisher/.venv/bin/python -m shopping_replenisher.cli run --apply 2>&1 | logger -t shopping_replenisher
```

This runs daily at 08:12, a few minutes after `todoist-local-sync` (which runs at 08:07 via its own cron entry) so the local SQLite database is always fresh before prediction runs.

## Setup

Create the virtual environment before the first run:

```bash
cd /home/user/code/todoist-shopping-replenisher
uv sync
```

Copy `.env.example` to `.env`.

- For `inspect`, `predict`, and dry-run `run`, only `TODOIST_DB_PATH` and `SHOPPING_PROJECT_ID` are required.
- For `run --apply`, Todoist and Telegram credentials are also required.

## Monitoring

Logs are written to the system journal via `logger`. To inspect:

```bash
# Recent runs
journalctl -t shopping_replenisher

# Follow live
journalctl -t shopping_replenisher -f

# Today only
journalctl -t shopping_replenisher --since today
```

Each run ends with a structured summary line:

```
INFO shopping_replenisher.runner Run complete: candidates_found=5 added_count=2 optional_count=1 failed_count=0
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Normal completion (includes empty runs with no candidates) |
| 1 | At least one Todoist task write failed |

Exit code 1 does not abort the run — remaining items are still attempted and Telegram is notified of what succeeded.

## Telegram Notifications

A Telegram message is sent only when `run --apply` successfully adds at least one item to Todoist. No message is sent for dry runs, empty runs, or runs where all Todoist writes failed.

## Local DB Freshness

The system reads a local SQLite snapshot of Todoist data maintained by [todoist-local-sync](https://github.com/juanpabloaj/todoist-local-sync). If that sync process is not running, predictions will be based on stale data.

- `todoist-local-sync` must be running and its cron entry must be active
- The replenisher cron entry is scheduled 5 minutes after the sync to guarantee a fresh snapshot
- If the sync is paused or broken, disable the replenisher cron entry too until sync is restored

## Dry Run

To preview candidates without writing to Todoist or sending Telegram:

```bash
cd /home/user/code/todoist-shopping-replenisher
.venv/bin/python -m shopping_replenisher.cli run
```

For detailed candidate output with scores:

```bash
.venv/bin/python -m shopping_replenisher.cli predict
```

Reports are written to a unique directory under `reports/` for inspection.
