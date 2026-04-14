# Phase 1 — Contract Brief: Re-audit Design and README Against Final Implemented Behavior

## Stage
Re-audit design and README against the final implemented behavior (technical_debt.md, Low Priority)

## Proportionality
Documentation-only task. No production logic changes. Phase 3 abbreviated. Phase 5 not required.

**Question**: what contract or assumption changes in this stage?

**Answer**: corrects four specific stale sections in DESIGN.md and ROADMAP.md. README.md and DEVELOPMENT.md are current and require no changes.

## Audit Findings

### DESIGN.md

**1. Architecture block — source files listing (lines 115–125)**
`reporter.py` is missing from the listing. The module exists and is a first-class part of the pipeline (builds summary payloads, writes JSON/Markdown/CSV artifacts). The architecture block should include it between `selection.py` and `todoist_api.py`.

**2. Architecture block — tests directory listing (lines 123–130)**
Only 4 test files are listed: `test_normalize.py, test_history.py, test_scoring.py, test_selection.py`. The actual test suite has 11 files. Missing: `test_db.py, test_config.py, test_runner.py, test_todoist_api.py, test_telegram.py, test_reporter.py, test_cli.py`.

**3. Key data interfaces — function signatures (lines 141–156)**
`build_purchase_occurrences` and `build_item_histories` are shown without the `timezone_name: str | None = None` parameter that both functions now accept. Update both signatures.

**4. Output section — Telegram message content (lines 210–214)**
Current text says the Telegram message includes:
- "Number of candidates found"
- "Items skipped (active duplicate)"
- "Items added (with reason)"
- "Items in optional bucket (report only)"

Actual implementation sends:
```
Replenisher

Overdue:
- <item>

Coming up:
- <item>

On the radar: <item1>, <item2>
```

Replace with a description that matches the real format.

### ROADMAP.md

**5. Current Status section (lines 14–16)**
Text says: "The repository currently contains design and development documentation only. No implementation files are present yet, so all delivery stages are initialized as `Not Started`."

This was accurate on project creation. All 12 stages are now `Done`. Replace with a brief statement of current status.

## Changes required

### `DESIGN.md`
- Add `reporter.py` to the source file listing in the Architecture block
- Update the tests listing to include all 11 current test files
- Update `build_purchase_occurrences` and `build_item_histories` signatures to include `timezone_name: str | None = None`
- Replace the Telegram output bullet list with a description matching the actual message format

### `ROADMAP.md`
- Replace the stale "Current Status" paragraph with a statement reflecting that all 12 stages are complete

## Out of scope / exclusions

- No changes to README.md — it accurately describes all commands, operational notes, and the tool's behavior
- No changes to DEVELOPMENT.md — it accurately describes conventions and is not tied to stage-specific behavior
- No changes to the DESIGN.md "Implementation Plan" table — it is a historical record of the planned stages, not a description of current behavior
- No changes to `docs/` subdirectory files (operations.md, threshold_notes.md, domain_rules.md) — these were updated incrementally and are current
- No production code changes

## What the reviewer will check in Phase 4

- `reporter.py` appears in the DESIGN.md architecture listing
- All 11 test files appear in the DESIGN.md tests listing
- Both `build_purchase_occurrences` and `build_item_histories` include `timezone_name` in their shown signatures
- The Telegram output section describes the actual "Overdue:", "Coming up:", "On the radar:" format
- The ROADMAP.md Current Status no longer says "No implementation files are present yet"
- No production code was modified
