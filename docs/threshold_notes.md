# Threshold Notes

## Stage 7 Review

Date reviewed: `2026-04-09`

Command used:

```bash
uv run python -m shopping_replenisher.cli predict --json
```

## Anonymized Validation Observations

The reviewed candidate output contained 5 anonymized candidates:

- `item-a`
- `item-b`
- `item-c`
- `item-d`
- `item-e`

Observed confidence and stability ranges from the validation run:

| Item | unique_days range | gap_stddev range | Confidence before tuning |
|---|---:|---:|---|
| `item-a` | 4-6 | 5-6 | `medium` |
| `item-b` | 8-10 | 4-5 | `medium` |
| `item-c` | 6-8 | 4-5 | `medium` |
| `item-d` | 12-14 | 4-5 | `medium` |
| `item-e` | 9-11 | 5-6 | `medium` |

## Assessment

The original `high` confidence rule in `scoring.py` was:

- `unique_days >= 6`
- `gap_stddev <= 3`

That cutoff was too strict relative to the validated shopping-history data. Items with strong purchase volume and reasonably stable gaps were still falling into `medium`, which made the `high` bucket effectively underused.

This was most visible for:

- `item-d`: high purchase volume with moderately noisy intervals
- `item-b`: high purchase volume with moderately noisy intervals
- `item-e`: high purchase volume with moderately noisy intervals

These items show repeat purchase behavior with much stronger evidence than a typical `medium` candidate, even though they are not perfectly regular.

## Adjustment Applied

Updated `high` confidence threshold:

- From: `unique_days >= 6` and `gap_stddev <= 3`
- To: `unique_days >= 8` and `gap_stddev <= 5.5`

The `medium` threshold was kept unchanged:

- `unique_days >= 4` and `gap_stddev <= 7`

## Rationale

- Raise the volume requirement for `high` from `6` to `8` unique days so `high` still requires stronger evidence.
- Relax the stability cutoff from `3` to `5.5` because real shopping intervals are noisier than the original threshold allowed.
- Keep `medium` unchanged to avoid broadening candidate eligibility prematurely.
- Preserve a conservative bias: items still need both substantial history and moderate gap stability to reach `high`.

## Notes

- The reviewed run also showed some candidates with `days_since_last = -1`, which indicates purchase timestamps later than the local run date. That issue does not change the confidence heuristic directly, but it should be kept in mind during future real-data validation.
- Known operational risk: apply-mode idempotency still depends on the Todoist SQLite state being up to date before the next scheduled run. If a scheduled run happens before newly created tasks are reflected locally, the same item could be proposed again.
- No automatic retries are implemented for Todoist or Telegram failures. The next scheduled cron run is the intended retry mechanism.

## Auto-Add Threshold Review

Date reviewed: `2026-05-03`

Backtesting on an anonymized local validation history showed that
`BUY_SOON_DAYS=7` was useful for report visibility but too aggressive for
unattended writes. In a stateful simulation that suppressed an item after it
would have been added until the next observed purchase, the previous `soon`
auto-add policy produced lower short-window precision than a due-only policy:

| Policy | Relative auto-add volume | Short-window precision |
|---|---:|---:|
| `BUY_SOON_DAYS=7`, auto-add `now` + `soon` | Higher | Lower |
| Auto-add only when `overdue_ratio >= 1.0` | Lower | Higher |

The default auto-add policy was therefore separated from `BUY_SOON_DAYS`.
`BUY_SOON_DAYS` still controls which items are classified as `soon` in reports,
while `AUTO_ADD_MIN_OVERDUE_RATIO=1.0` controls unattended Todoist writes. This
keeps early candidates visible for manual review without creating tasks before
the item is due relative to its typical gap.
