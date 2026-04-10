# Roadmap

> This roadmap is the staged development reference for the project. It is a guide, not a contract, and may be updated as requirements or understanding evolve.

## Usage Rules

- Do not start a new stage until the current stage is marked `Done`
- Each stage must have tests before the next stage begins
- Each stage must be manually validated on real data before the next stage begins
- Status values must stay within: `Not Started`, `In Progress`, `Blocked`, `Done`
- When scope changes, update this file rather than bypassing it

## Current Status

The repository currently contains design and development documentation only. No implementation files are present yet, so all delivery stages are initialized as `Not Started`.

## Validation Standard

Every stage must satisfy all of the following before being marked `Done`:

- Relevant automated tests exist in `tests/`
- `uv run pytest` passes for the implemented scope
- Manual validation has been performed against real Todoist data where applicable
- Documentation and examples remain aligned with the implemented behavior

## Stage Tracker

| Stage | Name | Status | Automated Validation Required | Manual Validation Required | Exit Criteria |
|---|---|---|---|---|---|
| 1 | Domain Rules and Examples | Done | Tests for normalization and equivalence examples added or drafted where applicable | Review real item names and purchase-history examples to confirm intended rules | Domain rules for normalization, equivalence, and scoring are documented with concrete examples and accepted as the working baseline |
| 2 | Repo Skeleton and Config Validation | Done | Tests for config loading and CLI/config validation behavior | Run `inspect`-style validation against a real `.env` and local DB path | Project skeleton exists with package layout, CLI stub, environment loading, and validation for DB path and project ID |
| 3 | SQLite Read Layer | Done | Tests for DB query functions using fixtures or sample SQLite data | Validate queries against a real Todoist SQLite database and target shopping project | Read functions exist for active tasks, completion events, and completed tasks, returning stable typed data structures |
| 4 | Normalization and Soft Deduplication | Done | Tests cover accents, whitespace, punctuation, singular/plural cases, and source deduplication | Validate grouping and deduplication behavior on real grocery history samples | Deterministic normalization and occurrence deduplication are implemented and produce traceable, conservative results |
| 5 | Scoring and Selection | Done | Tests for feature extraction, confidence, ranking, thresholds, and per-run limits | Review candidate outputs on real history and tune thresholds for false positives | Items can be scored, classified (`now`, `soon`, `optional`), filtered against active duplicates, and ranked for output |
| 6 | Local Prediction Output | Not Started | Tests for prediction pipeline output and report generation | Run local prediction on real data and inspect JSON/Markdown/CSV outputs for correctness | `predict` works end to end without external writes and produces local artifacts |
| 7 | Real-Data Validation and Threshold Tuning | Not Started | Regression tests added for cases discovered during manual review | Review false positives and missed items on real data and tune thresholds conservatively | Thresholds and heuristics are updated based on real usage, with documented rationale for the chosen defaults |
| 8 | Todoist Write Client | Not Started | Tests for API request construction, error handling, and dry-run safeguards | Validate task creation in a real Todoist test/project environment | Selected candidates can be created as Todoist tasks with correct naming, project targeting, and safe dry-run behavior |
| 9 | Telegram Notifications | Not Started | Tests for message formatting and notification error handling | Validate delivery and message content in a real Telegram chat | Run summaries and errors can be sent to Telegram with clear item outcomes |
| 10 | Full Apply Pipeline | Not Started | End-to-end tests for orchestration and apply/dry-run branching where practical | Run the full pipeline on real data in dry-run, then with apply enabled | `run` and `run --apply` orchestrate prediction, Todoist writes, reporting, and notifications safely |
| 11 | Hardening and Operational Quality | Not Started | Tests for logging paths, empty runs, timeout/error handling, and edge cases | Validate operational behavior on realistic empty/noisy/error scenarios | The system behaves predictably under failures, empty inputs, and operational edge cases |
| 12 | Cron and Operations Documentation | Not Started | Documentation review and any smoke tests for scheduled invocation scripts | Validate scheduled execution in the target environment | Cron setup and operating instructions are documented, and scheduled execution has been tested in practice |

## Stage Details

### Stage 1: Domain Rules and Examples

- Source: [DESIGN.md](./DESIGN.md)
- Focus:
  - Confirm normalization rules
  - Confirm item equivalence boundaries
  - Confirm scoring intent and conservative prediction philosophy
- Deliverables:
  - Accepted examples for item-name normalization
  - Accepted examples for cross-table deduplication
  - Clear definitions for candidate classes and confidence levels
- Validation notes:
  - Use real grocery examples before implementing heuristics

### Stage 2: Repo Skeleton and Config Validation

- Focus:
  - Create package structure under `shopping_replenisher/`
  - Add CLI entry points
  - Add configuration loading from `.env`
- Deliverables:
  - `pyproject.toml`
  - `.env.example`
  - Base package files
  - CLI `inspect` command or equivalent validation path
- Validation notes:
  - Confirm required environment variables are enforced

### Stage 3: SQLite Read Layer

- Focus:
  - Add the read-only Todoist SQLite access layer
  - Separate active-task reads from historical completion reads
- Deliverables:
  - `db.py`
  - Typed row models or dataclasses
  - Test fixtures for representative DB rows
- Validation notes:
  - Confirm table assumptions against a real Todoist DB snapshot

### Stage 4: Normalization and Soft Deduplication

- Focus:
  - Canonicalize item names deterministically
  - Deduplicate occurrences across `completion_events` and `completed_tasks`
- Deliverables:
  - `normalize.py`
  - `history.py`
  - Tests covering Spanish and English item variants
- Validation notes:
  - Confirm recurring-task behavior is handled through `completion_events`

### Stage 5: Scoring and Selection

- Focus:
  - Build item histories and scoring features
  - Apply selection thresholds and ranking
- Deliverables:
  - `scoring.py`
  - `selection.py`
  - Threshold-based classification logic
- Validation notes:
  - Prioritize precision over recall

### Stage 6: Local Prediction Output

- Focus:
  - Produce a safe local-only prediction flow
  - Emit human-readable and machine-readable reports
- Deliverables:
  - `predict` CLI path
  - `summary.json`
  - `summary.md`
  - `candidates.csv`
- Validation notes:
  - No external writes allowed at this stage

### Stage 7: Real-Data Validation and Threshold Tuning

- Focus:
  - Review prediction quality on actual history
  - Tune defaults conservatively
- Deliverables:
  - Updated thresholds if needed
  - Regression examples for observed edge cases
- Validation notes:
  - This stage is mandatory before any Todoist API integration is enabled

### Stage 8: Todoist Write Client

- Focus:
  - Add safe task-creation support
  - Preserve dry-run as the default safe workflow
- Deliverables:
  - `todoist_api.py`
  - Apply-mode wiring for task creation
- Validation notes:
  - Use a controlled project or test environment first

### Stage 9: Telegram Notifications

- Focus:
  - Send operational summaries and failures to Telegram
- Deliverables:
  - `telegram.py`
  - Message templates for success, empty runs, and errors
- Validation notes:
  - Confirm formatting is readable on mobile

### Stage 10: Full Apply Pipeline

- Focus:
  - Orchestrate prediction, writes, reporting, and notifications
- Deliverables:
  - `runner.py`
  - `run` and `run --apply` CLI behaviors
- Validation notes:
  - Verify dry-run and apply paths separately

### Stage 11: Hardening and Operational Quality

- Focus:
  - Stabilize error handling and operational behavior
- Deliverables:
  - Improved logging
  - Empty-run behavior
  - Safer failure handling and timeouts
- Validation notes:
  - Confirm behavior for missing data, API errors, and no-candidate runs

### Stage 12: Cron and Operations Documentation

- Focus:
  - Document how the system is run and monitored
- Deliverables:
  - Cron examples
  - Operating notes
  - Maintenance guidance for local DB freshness assumptions
- Validation notes:
  - Confirm the scheduled command works in the target environment

## Progress Log

Use this section to record stage transitions and the evidence for each status change.

| Date | Stage | Status Change | Notes |
|---|---|---|---|
| 2026-04-09 | All | Initialized to `Not Started` | Repository contains documentation only; roadmap created from `DESIGN.md` and `DEVELOPMENT.md` |
| 2026-04-09 | Stage 1 | `Not Started` → `Done` | `docs/domain_rules.md` created and manually validated |
| 2026-04-09 | Stage 2 | `Not Started` → `Done` | Package skeleton, config loader, CLI stubs, `.env.example`, tests passing |
| 2026-04-09 | Stage 3 | `Not Started` → `Done` | SQLite read layer with typed dataclasses, project_id filtering, 5 tests passing |
| 2026-04-09 | Stage 4 | `Not Started` → `Done` | Normalization and deduplication implemented, 29 tests passing |
| 2026-04-09 | Stage 5 | `Not Started` → `Done` | Scoring and selection implemented, IGNORED_ITEMS added, 34 tests passing, validated on real data |
