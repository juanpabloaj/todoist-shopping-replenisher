# todoist-shopping-replenisher — Design Document

> This document is a reference and flexible guide. It can be adapted as understanding of the problem evolves or requirements change.

## Overview

A batch system that reads the local Todoist SQLite database, analyzes the purchase history of a specific shopping project, predicts which items should be bought soon based on historical patterns, automatically adds them to the Todoist shopping list via API, and sends a Telegram notification with the results.

## Goals

- Predict grocery replenishment using historical purchase patterns, without LLMs
- Avoid adding items already active in the list (soft duplicate detection)
- Run automatically on a cron schedule
- Be conservative: less recall, less noise

---

## Data Sources

The system reads from a local SQLite database configured via `TODOIST_DB_PATH`.

### Key tables

| Table | Content |
|---|---|
| `tasks` | Currently active (uncompleted) tasks |
| `completed_tasks` | Non-recurring completed tasks only |
| `completion_events` | All completion events, including recurring tasks |
| `task_history` | View mixing active and completed — not used as model input |

### Important distinction

`completed_tasks` only records **non-recurring** tasks. Recurring tasks (likely the most frequent grocery items: milk, eggs, bread, etc.) are only captured in `completion_events`. Therefore:

- **Primary source:** `completion_events`
- **Complementary source:** `completed_tasks`
- **Current active items:** `tasks` (for deduplication)

Deduplication between both sources is done in Python, not SQL, for readability and testability.

### Deduplication strategy

Match a `completed_tasks` row against a `completion_events` row using a hierarchical key:

1. **Strong match:** same `task_id` AND `abs(delta_seconds) <= 5`
2. **Medium match:** same normalized content AND same day AND `abs(delta_seconds) <= 10`
3. No match → keep as independent occurrence

This prevents merging two genuinely different purchases of the same item made on the same day.

### Occurrence granularity

- `occurrence_timestamps`: full precision (for detecting same-day duplicates)
- `pattern_dates`: `set(occurrence_day)` — used for gap/frequency calculation to avoid inflating frequency from technical double-closes

---

## Normalization & Equivalence

Canonical normalization applied to all item names before grouping or deduplication:

1. Lowercase
2. Remove accents (NFKD + strip combining chars)
3. Trim and collapse whitespace
4. Remove trivial punctuation
5. Light singular/plural heuristic for Spanish and English (rule-based, not linguistic)
6. Normalize obvious variants (e.g. `coca cola` / `coca-cola`)

**v1 does not use aggressive fuzzy matching.** Deterministic normalization + a few singular/plural rules. This keeps results traceable and avoids false merges.

---

## Prediction Model

No LLMs. The prediction approach is open — rule-based, statistical, or ML models are all valid.

### Features per item

| Feature | Description |
|---|---|
| `occurrence_count` | Total historical purchases |
| `unique_days` | Number of distinct days purchased |
| `gaps` | List of day gaps between consecutive purchases |
| `typical_gap` | Median gap in days |
| `gap_stddev` | Gap standard deviation |
| `last_purchased` | Date of last purchase |
| `days_since_last` | Days elapsed since last purchase |
| `overdue_ratio` | `days_since_last / typical_gap` |
| `is_active` | Whether an equivalent item is currently active |
| `confidence` | Based on volume and gap stability |

### Candidate criteria (v1)

- At least `MIN_PATTERN_OCCURRENCES` (default: 4) unique purchase days
- Calculable typical gap
- Item not currently active in the list
- Overdue or approaching due date
- Confidence: `medium` or `high`

### Classification

| Class | Condition | Auto-add |
|---|---|---|
| `now` | Overdue or clearly forgotten | Yes |
| `soon` | Due within next `BUY_SOON_DAYS` days | Yes |
| `optional` | Not urgent | No (report only) |

---

## Architecture

```
todoist_shopping_replenisher/
├── shopping_replenisher/
│   ├── config.py        # Load .env, parse thresholds and flags
│   ├── db.py            # SQLite queries by project_id
│   ├── normalize.py     # Text normalization and soft equivalence
│   ├── history.py       # Build purchase history from both sources
│   ├── scoring.py       # Features and replenishment score
│   ├── selection.py     # Final filters: dedup, per-run limit, ranking
│   ├── todoist_api.py   # Create tasks via Todoist API
│   ├── telegram.py      # Summary and error notifications
│   ├── runner.py        # End-to-end orchestration
│   └── cli.py           # CLI entry points
└── tests/
    ├── test_normalize.py
    ├── test_history.py
    ├── test_scoring.py
    └── test_selection.py
```

### Key data interfaces

```python
# db.py
def fetch_active_items(conn, project_id) -> list[ActiveItemRow]
def fetch_completion_event_rows(conn, project_id) -> list[CompletionRow]
def fetch_completed_task_rows(conn, project_id) -> list[CompletionRow]

# history.py
def build_purchase_occurrences(
    completion_events: list[CompletionRow],
    completed_tasks: list[CompletionRow],
) -> list[PurchaseOccurrence]

def build_item_histories(
    occurrences: list[PurchaseOccurrence],
) -> dict[str, ItemHistory]

@dataclass
class ItemHistory:
    canonical_name: str
    original_names: set[str]
    occurrences: list[PurchaseOccurrence]
    occurrence_days: list[date]
```

---

## CLI

```bash
python -m shopping_replenisher.cli inspect         # Validate config, DB, project_id, data coverage
python -m shopping_replenisher.cli predict         # Compute candidates, local report only
python -m shopping_replenisher.cli predict --json  # JSON output
python -m shopping_replenisher.cli run             # Full pipeline, dry-run (no writes to Todoist or Telegram)
python -m shopping_replenisher.cli run --apply     # Full pipeline + write to Todoist + notify Telegram
```

---

## Environment Variables

```env
# Required
TODOIST_DB_PATH=/home/user/data/todoist.db
TODOIST_API_TOKEN=...
SHOPPING_PROJECT_ID=YOUR_PROJECT_ID
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Behavior
AUTO_APPLY=false
MAX_ITEMS_PER_RUN=5
PREDICTION_WINDOW_DAYS=7
MIN_PATTERN_OCCURRENCES=4
MIN_CONFIDENCE=medium
BUY_SOON_DAYS=7

# Optional
ENABLE_COMPLETION_EVENTS_BACKFILL=true
TODOIST_TASK_PREFIX=
LOG_LEVEL=INFO
TIMEZONE=your_timezone
OVERRULE_ACTIVE_DUPLICATES=false
FORGOTTEN_RATIO_THRESHOLD=1.75
DRY_RUN_NOTIFY_EMPTY=true
```

---

## Output

Each run produces artifacts in `reports/<timestamp>/`:

```
reports/
└── <timestamp>/
    ├── summary.json
    ├── summary.md
    └── candidates.csv
```

Telegram message includes:
- Number of candidates found
- Items skipped (active duplicate)
- Items added (with reason)
- Items in `optional` bucket (report only)

---

## Cron Setup

The system is designed to run as a cron job. The SQLite database must be up to date before each run — how it is kept in sync is outside the scope of this project.

Example cron entry:

```cron
5 8 * * * cd /path/to/todoist_shopping_replenisher && uv run python -m shopping_replenisher.cli run --apply
```

Start in dry-run (`AUTO_APPLY=false`) until scoring is validated on real data.

---

## Implementation Plan

| Step | Task |
|---|---|
| 1 | Extract and formalize domain rules: normalization, equivalence, scoring criteria with real examples |
| 2 | Repo skeleton: CLI stub, `.env` loading, DB and project_id validation |
| 3 | SQLite read layer: queries for active items, completion events, completed tasks |
| 4 | Normalization and soft deduplication: tests with real cases (queso/Quesos, accents, plurals) |
| 5 | Scoring and selection: forecast, forgotten items, confidence, ranking, per-run limits |
| 6 | Implement `predict`: local JSON/Markdown output, no external writes |
| 7 | **Validate on real data**: tune thresholds, review false positives |
| 8 | Todoist write client: create tasks for selected candidates |
| 9 | Telegram notification: run summary and errors |
| 10 | Implement `run --apply`: full pipeline |
| 11 | Tests and operational hardening: error handling, logs, timeouts, empty runs |
| 12 | Cron setup and operational documentation |

> Step 7 is critical: do not connect to Todoist API until scoring is validated locally.

---

## Known Risks

- Singular/plural normalization in Spanish is imperfect with simple rules — v1 must be conservative
- Low-frequency or seasonal items may be excluded by design
- Items genuinely bought under different names won't be merged in v1 (no aggressive fuzzy matching)
- `completion_events` coverage depends on sync frequency — gaps in sync = gaps in history
