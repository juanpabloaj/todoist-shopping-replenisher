# Phase 3 — Risk Note: Revisit Normalization Quality for Conservative Plural Handling

## Residual Issues

### 1. `luces` and `papeles` still normalize to `luce` and `papele`
**Classification: accepted risk**
The awkward canonical forms remain. The documentation now explicitly explains why: a proper fix requires language detection or a morphology dictionary. No behavior change was made.
**Phase 1 exclusion reference**: the contract brief states that changing normalization behavior is out of scope because changing canonical forms would invalidate existing purchase history grouping.
**Why this still holds**: the imperfect forms are cosmetically awkward but functionally correct — items purchased under the same name will still group together consistently.

### 2. No new test coverage added
**Classification: accepted risk**
This is a documentation-only task. No new test cases were added because the tests already contain inline comments documenting the imperfect cases (`luces → luce`, `papeles → papele`).
**Phase 1 exclusion reference**: the contract brief explicitly states "No test changes — tests already document the imperfect cases."
**Why this still holds**: adding test cases for already-tested behavior would create duplicate coverage without improving mutation protection.
