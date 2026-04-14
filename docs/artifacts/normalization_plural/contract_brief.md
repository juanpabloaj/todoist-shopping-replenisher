# Phase 1 — Contract Brief: Revisit Normalization Quality for Conservative Plural Handling

## Stage
Revisit normalization quality for conservative plural handling (technical_debt.md, Medium Priority)

## Proportionality
Documentation-only task. No production logic changes. Phase 3 abbreviated (no new code paths to review adversarially). Phase 5 not required.

**Question**: what contract or assumption changes in this stage?

**Answer**: makes the current tradeoff explicit in three places: source code, documentation, and test commentary. No behavior changes.

## Problem Analysis

The current `_singularize_word` strips the final `s` from any word longer than 3 chars that ends in `s`. This produces awkward canonical names for Spanish `-es` plurals:

- `luces → luce` (should be `luz`, but that requires a z↔c spelling change — not representable without a dictionary)
- `papeles → papele` (should be `papel`, but stripping `-es` instead of `-s` would break English words like `noodles → noodle`)

### Why improving the heuristic is unsafe

A rule like "strip `-es` when the stem ends in a consonant" fails for English:
- `noodles` → stem `noodl` ends in `l` (consonant) → rule fires → canonical `noodl` (WRONG, current behavior `noodle` is correct)
- `pickles` → same problem

A rule like "strip `-les` → `-l`" fails for the same reason. There is no safe heuristic to distinguish `papeles` (Spanish, strip `-es`) from `noodles` (English, strip `-s`) without language detection or a morphology dictionary.

### Why the current behavior is acceptable

The conservative `-s` strip avoids false merges:
- `papeles` and `papel` normalize differently (`papele` vs `papel`) — they do NOT merge incorrectly
- `luces` and `luz` normalize differently (`luce` vs `luz`) — they do NOT merge incorrectly
- The imperfect canonical names are consistently applied, so history grouping still works correctly for items purchased under the same name

The awkwardness is cosmetic (report readability, Todoist task names) not functional.

## Chosen approach: document the tradeoff explicitly

The expected outcome from technical_debt.md allows "document the current tradeoff more explicitly." This is the safe path.

## Changes required

### 1. `shopping_replenisher/normalize.py` — add comment to `_singularize_word`

Add a block comment explaining:
- The known imperfect cases (`luces → luce`, `papeles → papele`)
- Why a more precise fix is unsafe without language detection
- That this is intentional for v1

### 2. `docs/domain_rules.md` — expand the Light Singular/Plural Heuristic section

After the existing table, add a subsection "Known imperfect outputs" that:
- Lists `luces → luce` and `papeles → papele` as known cases
- Explains that Spanish `-es` plurals with irregular stems cannot be handled by a simple suffix rule
- Confirms that the conservative `-s` strip is intentional: avoids incorrect merges at the cost of cosmetic awkwardness
- States that a proper fix requires a Spanish morphology dictionary or language detection, which is out of scope for v1

### 3. `tests/test_normalize.py` — no changes needed

The test file already contains an inline comment documenting these cases:
```python
# Spanish plurals ending in -es: strip only the final s (conservative)
# "papeles" → "papele" is imperfect but safe — no incorrect merge
```
No test modifications required.

## Out of scope / exclusions

- No changes to normalization behavior — changing canonical forms would invalidate existing purchase history grouping
- No addition of known-variants lookup table or dictionary-based normalization (v1 constraint from DESIGN.md)
- No test changes — tests already document the imperfect cases
- No changes to `history.py`, `scoring.py`, or any other module
**Invariant**: the existing test cases (`luces → luce`, `papeles → papele`) are correct for the current behavior and must continue to pass without modification.

## What the reviewer will check in Phase 4

- `normalize.py` contains an explicit comment naming the known imperfect cases and explaining why a fix is unsafe
- `docs/domain_rules.md` contains a "Known imperfect outputs" subsection in the plural heuristic section
- No test was modified or removed
- No production code behavior was changed (existing tests pass unchanged)
- The comment/doc explains the tradeoff, not just acknowledges the symptom
