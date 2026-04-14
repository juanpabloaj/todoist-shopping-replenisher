# Process Audit 001

## Scope

Second multi-agent trial using:
- `codex` as implementor
- `claude` as reviewer/validator
- external orchestration through tmux plus durable artifacts

Repository under test:
- `todoist_shopping_replenisher`

Comparison baseline:
- a previous multi-agent trial in another repository

## Outcome

WI-001 closed as `pass_with_debt`.

Technical result:
- the repository received a meaningful improvement set
- the implementor added real fixes and hardening
- the reviewer validated the changes and closed with explicit debt

Process result:
- the trial ended more cleanly than the earlier external trial
- but the same central failure mode repeated: stale review after filesystem changes

## What Improved Compared To Trial 1

1. The implementor completed the work with fewer process misses.
- In the first trial, the implementor delayed required artifacts and had to be pushed repeatedly to write them.
- In this second trial, the implementor produced the contract, implementation record, validation record, and board updates in a more orderly way.

2. The final technical work was better scoped.
- In the first trial, there was a notable gap between the initial task framing and the actual useful work, and the implementor had to broaden the scope mid-flight.
- In this second trial, the implementor identified a concrete set of repository-wide improvements and delivered them coherently.

3. The reviewer’s final verdict was structurally better.
- The final review clearly separated:
  - verified improvements
  - accepted debt
  - remaining non-blocking concerns
- The final board state and review artifact were consistent.

4. The artifact set was stronger.
- The implementation record and validation record were materially useful, not decorative.
- They made it easier to compare the reviewer’s claims against the actual code state.

## What Repeated From Trial 1

1. The reviewer became stale after code and artifact changes.
- This happened in the earlier external trial.
- It happened again here.
- In both cases, the reviewer continued from an earlier blocked narrative instead of replacing it immediately with a fresh filesystem-based review.

2. The orchestrator still had to correct review drift explicitly.
- In both trials, external intervention was needed to force the reviewer to stop relying on prior state and re-check current files.
- This confirms that the reviewer does not yet enforce the re-review rule reliably on its own.

3. tmux remained only an execution layer.
- As in the first trial, tmux was useful for launching and observing agents.
- It did not solve semantic coordination.
- The real source of truth remained the board, artifacts, and direct file inspection.

## What Was Better Than Trial 1

The reviewer did not miss a real technical bug this time.
- In the first trial, the reviewer found a genuine syntax bug introduced by the implementor, and this was valuable.
- In the second trial, the reviewer’s main problem was stale process state, not a missed technical defect.
- That suggests the technical quality of the implementor’s work was stronger in the second run.

The implementor also did not repeatedly claim a nonexistent fix after direct file verification pressure was applied.
- In the first trial, that happened and required several correction loops.
- In the second trial, the main friction was review freshness rather than false fix claims.

## Main Remaining Failure Mode

The dominant unresolved problem is now clear:

> A reviewer that has already issued a blocked verdict tends to remain anchored to that prior narrative even after the filesystem changes.

This is the failure mode most likely to corrupt multi-agent closure.

The workflow rule already says re-review must be based on the current filesystem state. The problem is not that the rule is missing. The problem is that it is not being followed reliably without orchestration pressure.

## Comparison Summary

### Trial 1: previous external repository
- More chaotic
- Stronger technical bug caught by reviewer
- Weaker artifact discipline from implementor
- More direct orchestrator intervention needed on both sides

### Trial 2: `todoist_shopping_replenisher`
- Cleaner implementation and artifact production
- Better final technical outcome
- Reviewer still drifted stale after state changes
- Final closure was achieved, but only after explicit re-review forcing

## Process Judgment

The method is improving, but the core autonomy problem is not solved.

What the trials now show consistently:
- implementor/reviewer separation is valuable
- durable artifacts are valuable
- tmux is useful operationally
- stale review is the main coordination failure mode

This means the method is usable, but not yet safely self-propelled.

## Recommended Next Rule

Add an operational re-review trigger that is impossible to ignore:

> If a review verdict is older than the latest code or artifact change, the board must not remain `ready_for_review`; it must move to a distinct `re_review_required` state until the reviewer re-reads the current filesystem state and rewrites the verdict.

Reason:
- `ready_for_review` is too weak once a stale verdict already exists
- a separate state makes the coordination problem visible immediately

## Secondary Recommendation

Require the reviewer to explicitly reference current-file evidence in any blocking verdict after a resubmission.

That means:
- quote the current file content or command result
- do not cite earlier grep output or earlier review text

## Final Assessment

Compared to the first trial, this second trial shows better technical execution and better artifact hygiene.

However, both trials converge on the same conclusion:
- the workflow is useful
- the role split is useful
- but the reviewer still needs stronger forcing around fresh-state review after changes

That is the next problem to solve.
