# Phase 3 — Risk Note: Re-audit Design and README Against Final Implemented Behavior

## Residual Issues

### 1. DESIGN.md "Implementation Plan" table not updated
**Classification: accepted risk**
The "Implementation Plan" table (steps 1–12) is a historical record of planned stages, not a description of current behavior. It uses forward-looking language ("Step 1 | Extract and formalize domain rules") that was accurate when written. It has not been updated to reflect completion status.
**Phase 1 exclusion reference**: the contract brief explicitly excludes changes to the Implementation Plan table, noting it is a historical record.
**Why this still holds**: the table is correctly positioned in the document as a plan-at-inception. It does not mislead contributors about current behavior; the ROADMAP.md Progress Log and stage statuses serve that purpose.

### 2. DESIGN.md "Occurrence granularity" section uses conceptual field names
**Classification: accepted risk**
The section uses `occurrence_timestamps` and `pattern_dates` — these are conceptual names, not the actual `ItemHistory` dataclass field names (`occurrences` and `occurrence_days`). This was not flagged in the contract brief as requiring a fix.
**Phase 1 exclusion reference**: the contract brief does not list this section as stale — it targets specific concrete mismatches between the doc and the code. The occurrence granularity section is a conceptual description, not a code reference.
**Why this still holds**: the section appears under "Data Sources", not under "Key data interfaces". It explains the design concept, not the implementation. No contributor would use these names to write code.
