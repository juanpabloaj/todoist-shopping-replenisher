# Domain Rules and Examples

> This document captures concrete examples for Stage 1 of the roadmap. It is derived strictly from `DESIGN.md` and is intended to clarify the domain rules before implementation.

## Scope

This document covers:

1. Item name normalization examples
2. Cross-table deduplication examples between `completion_events` and `completed_tasks`
3. Candidate classification examples for `now`, `soon`, and `optional`

No implementation details are defined here beyond what is already specified in `DESIGN.md`.

## 1. Item Name Normalization

Canonical normalization is applied to all item names before grouping or deduplication.

The documented normalization steps are:

1. Lowercase
2. Remove accents
3. Trim and collapse whitespace
4. Remove trivial punctuation
5. Apply a light singular/plural heuristic for Spanish and English
6. Normalize obvious variants such as `coca cola` and `coca-cola`

`DESIGN.md` explicitly states that v1 does not use aggressive fuzzy matching.

### Lowercase

| Input | Canonical form |
|---|---|
| `Milk` | `milk` |
| `QUESO` | `queso` |
| `Coca Cola` | `coca cola` |

### Remove Accents

| Input | Canonical form |
|---|---|
| `Café` | `cafe` |
| `Azúcar` | `azucar` |
| `Jamón` | `jamon` |

### Trim and Collapse Whitespace

| Input | Canonical form |
|---|---|
| `  milk` | `milk` |
| `milk  ` | `milk` |
| `coca   cola` | `coca cola` |
| `  queso   crema  ` | `queso crema` |

### Remove Trivial Punctuation

| Input | Canonical form |
|---|---|
| `coca-cola` | `coca cola` |
| `coca, cola` | `coca cola` |
| `milk.` | `milk` |
| `queso!` | `queso` |

### Light Singular/Plural Heuristic

The design allows a light singular/plural heuristic for Spanish and English. The examples below are limited to the kind of forms explicitly referenced by the design.

| Input | Canonical form |
|---|---|
| `queso` | `queso` |
| `quesos` | `queso` |
| `egg` | `egg` |
| `eggs` | `egg` |

This is intended to be conservative and traceable. `DESIGN.md` also notes that singular/plural normalization in Spanish is imperfect in v1.

### Known Variants

`DESIGN.md` explicitly gives `coca cola` and `coca-cola` as an example of obvious variants that should normalize together.

| Input | Canonical form |
|---|---|
| `coca cola` | `coca cola` |
| `coca-cola` | `coca cola` |
| `Coca Cola` | `coca cola` |

### Non-Goal

The design does not authorize aggressive fuzzy matching in v1. That means this document does not define broader equivalence rules beyond deterministic normalization and a few obvious singular/plural or punctuation variants.

## 2. Cross-Table Deduplication

The design states:

- `completion_events` is the primary history source
- `completed_tasks` is a complementary source
- Deduplication is performed in Python, not SQL

The hierarchical deduplication key is:

1. Strong match: same `task_id` and `abs(delta_seconds) <= 5`
2. Medium match: same normalized content and same day and `abs(delta_seconds) <= 10`
3. No match: keep as independent occurrences

These rules are intended to avoid merging two genuinely different purchases of the same item made on the same day.

### Row Shape Used in Examples

The design does not define an exact row schema, so the examples below use only the fields required by the matching rules:

- `task_id`
- `content`
- `completed_at`

### Strong Match Example

Two rows should be treated as the same occurrence when they share the same `task_id` and their completion timestamps differ by at most 5 seconds.

| Source | task_id | content | completed_at |
|---|---|---|---|
| `completion_events` | `T-100` | `Milk` | `2026-04-01 09:15:00` |
| `completed_tasks` | `T-100` | `Milk` | `2026-04-01 09:15:03` |

Result:

- Same `task_id`
- Time delta is 3 seconds
- This is a strong match
- Keep one occurrence

### Medium Match Example

Two rows should be treated as the same occurrence when the normalized content matches, the calendar day is the same, and the timestamps differ by at most 10 seconds.

| Source | task_id | content | Normalized content | completed_at |
|---|---|---|---|---|
| `completion_events` | `E-210` | `Coca Cola` | `coca cola` | `2026-04-02 18:30:00` |
| `completed_tasks` | `C-777` | `coca-cola` | `coca cola` | `2026-04-02 18:30:08` |

Result:

- Different `task_id`
- Same normalized content
- Same day
- Time delta is 8 seconds
- This is a medium match
- Keep one occurrence

### No-Match Example: Same Day, But Too Far Apart

Two rows should remain separate when they have the same normalized content on the same day but the time delta exceeds the medium-match threshold.

| Source | task_id | content | Normalized content | completed_at |
|---|---|---|---|---|
| `completion_events` | `E-300` | `eggs` | `egg` | `2026-04-03 10:00:00` |
| `completed_tasks` | `C-300` | `Egg` | `egg` | `2026-04-03 10:00:15` |

Result:

- Different `task_id`
- Same normalized content
- Same day
- Time delta is 15 seconds
- This is not a medium match
- Keep as two independent occurrences

### No-Match Example: Different Day

Two rows should remain separate when they do not occur on the same day, even if normalized content matches.

| Source | task_id | content | Normalized content | completed_at |
|---|---|---|---|---|
| `completion_events` | `E-410` | `quesos` | `queso` | `2026-04-04 22:00:00` |
| `completed_tasks` | `C-410` | `queso` | `queso` | `2026-04-05 08:00:00` |

Result:

- Same normalized content
- Different day
- This is not a medium match
- Keep as two independent occurrences

### No-Match Example: Different Item

Two rows should remain separate when normalized content differs.

| Source | task_id | content | Normalized content | completed_at |
|---|---|---|---|---|
| `completion_events` | `E-500` | `milk` | `milk` | `2026-04-06 12:00:00` |
| `completed_tasks` | `C-500` | `bread` | `bread` | `2026-04-06 12:00:04` |

Result:

- Different normalized content
- This is not a match
- Keep as two independent occurrences

## 3. Candidate Classification Examples

The design defines the following v1 candidate criteria:

- At least `MIN_PATTERN_OCCURRENCES` unique purchase days
- Calculable typical gap
- Item not currently active in the list
- Overdue or approaching due date
- Confidence is `medium` or `high`

The design also defines the classes:

| Class | Condition | Auto-add |
|---|---|---|
| `now` | Overdue or clearly forgotten | Yes |
| `soon` | Due within next `BUY_SOON_DAYS` days | Yes |
| `optional` | Not urgent | No |

The feature examples below use only fields named in `DESIGN.md`:

- `occurrence_count`
- `unique_days`
- `typical_gap`
- `last_purchased`
- `days_since_last`
- `overdue_ratio`
- `is_active`
- `confidence`

These examples are illustrative applications of the documented rules, not additional scoring rules.

### `now`

Example item: `milk`

| Feature | Sample value |
|---|---|
| `occurrence_count` | `8` |
| `unique_days` | `8` |
| `typical_gap` | `7 days` |
| `last_purchased` | `2026-03-25` |
| `days_since_last` | `15` |
| `overdue_ratio` | `15 / 7 = 2.14` |
| `is_active` | `false` |
| `confidence` | `high` |

Classification:

- Meets the minimum pattern requirement
- Has a calculable typical gap
- Is not currently active
- Is overdue relative to its typical gap
- Should be classified as `now`
- Should be auto-added

### `soon`

Example item: `eggs`

| Feature | Sample value |
|---|---|
| `occurrence_count` | `6` |
| `unique_days` | `6` |
| `typical_gap` | `10 days` |
| `last_purchased` | `2026-04-02` |
| `days_since_last` | `7` |
| `overdue_ratio` | `7 / 10 = 0.70` |
| `is_active` | `false` |
| `confidence` | `medium` |

Classification:

- Meets the minimum pattern requirement
- Has a calculable typical gap
- Is not currently active
- Is within the next `BUY_SOON_DAYS` window relative to its expected due point
- Should be classified as `soon`
- Should be auto-added

### `optional`

Example item: `coca cola`

| Feature | Sample value |
|---|---|
| `occurrence_count` | `5` |
| `unique_days` | `5` |
| `typical_gap` | `14 days` |
| `last_purchased` | `2026-04-05` |
| `days_since_last` | `4` |
| `overdue_ratio` | `4 / 14 = 0.29` |
| `is_active` | `false` |
| `confidence` | `medium` |

Classification:

- Meets the minimum pattern requirement
- Has a calculable typical gap
- Is not currently active
- Is not urgent yet
- Should be classified as `optional`
- Should not be auto-added

## Notes for Stage 1

- `DESIGN.md` defines the rules and examples above, but it does not define implementation-specific row models, formulas beyond the named features, or additional fuzzy matching rules.
- `DEVELOPMENT.md` requires real-data manual validation before moving to the next stage. These examples should therefore be reviewed against actual Todoist shopping history before implementation begins.
