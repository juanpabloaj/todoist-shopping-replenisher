# Phase 2/3 — Change Summary: Re-audit Design and README Against Final Implemented Behavior

## Changes made

### `DESIGN.md`
1. Added `reporter.py` to the Architecture source file listing (between `selection.py` and `todoist_api.py`)
2. Updated the tests directory listing from 4 files to all 11 current test files
3. Added `timezone_name: str | None = None` to `build_purchase_occurrences` and `build_item_histories` signatures
4. Replaced stale Telegram output bullet list with a description matching the actual message format ("Overdue:", "Coming up:", "On the radar:")
5. Fixed tree formatting bug in tests listing (malformed `└──` in mid-list, corrected to `├──`)

### `ROADMAP.md`
6. Replaced stale "Current Status" paragraph ("No implementation files are present yet") with: "All 12 planned stages are complete. The repository now contains the full implementation, tests, operational documentation, and stage artifacts documenting later hardening and technical-debt work."

## Files NOT changed (per contract)
- README.md — current
- DEVELOPMENT.md — current
- `docs/` subdirectory files — current
- No production code modified
