# Threshold Notes

## Stage 7 Review

Date reviewed: `2026-04-09`

Command used:

```bash
uv run python -m shopping_replenisher.cli predict --json
```

## Real-Data Observations

The reviewed candidate output contained 5 candidates:

- `cafe expresso`
- `vacuno`
- `jugo`
- `pan`
- `yogurt`

Observed confidence and stability values from the run:

| Item | unique_days | gap_stddev | Confidence before tuning |
|---|---:|---:|---|
| `cafe expresso` | 5 | 5.70 | `medium` |
| `vacuno` | 9 | 4.95 | `medium` |
| `jugo` | 7 | 4.65 | `medium` |
| `pan` | 13 | 4.03 | `medium` |
| `yogurt` | 10 | 5.26 | `medium` |

## Assessment

The original `high` confidence rule in `scoring.py` was:

- `unique_days >= 6`
- `gap_stddev <= 3`

That cutoff was too strict relative to the validated shopping-history data. Items with strong purchase volume and reasonably stable gaps were still falling into `medium`, which made the `high` bucket effectively underused.

This was most visible for:

- `pan`: `13` unique days, `gap_stddev = 4.03`
- `vacuno`: `9` unique days, `gap_stddev = 4.95`
- `yogurt`: `10` unique days, `gap_stddev = 5.26`

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
