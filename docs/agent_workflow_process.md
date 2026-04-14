# Agent Development Workflow

## Purpose

This workflow is for software projects where multiple agents work with limited shared context and the human does not want to supervise every step.

Its purpose is to prevent these failure modes:

- the implementor self-certifies its own work
- weak tests are treated as sufficient
- the task scope is followed literally even when it is wrong or incomplete
- unresolved issues are noted vaguely and then ignored
- local changes create cross-module inconsistency
- important context is lost between agents or sessions
- the process itself degrades unless it is audited periodically

The goal is not maximum ceremony. The goal is the smallest process that still makes agents self-critical.

---

## Roles

**Implementor**

- makes the change
- writes or updates tests
- identifies residual issues

**Reviewer**

- independently checks whether the change is actually sufficient
- challenges scope, tests, and consistency
- decides whether the work item is closed

**Validator** (only when needed)

- runs the changed behavior in a realistic environment
- confirms observable behavior, not structural quality

A single agent must not act as both Implementor and Reviewer for the same work item.

---

## Unit of Work

A work item is any change being closed under this workflow. A work item may be a large development stage or a smaller individual task.

Use this workflow for any work item that is more than trivial. For trivial edits, use the abbreviated rule at the end.

---

## Required Workflow

Each work item has four required steps.

### 1. Contract

Before implementation, write a short contract containing:

- what is being changed
- what is not being changed
- why any exclusion is safe
- any known judgment call in the scope

A statement like "no production changes" is not enough by itself. If something is excluded, say why that exclusion is safe.

If the contract includes a non-obvious scope decision, the Implementor must answer before implementation starts:

- Do you agree with this decision?
- What is the strongest alternative?
- What risk does this scope create?
- Does this require an explicit exclusion?

If the scope is not clear enough to answer these questions, the contract is not ready.

### 2. Implementation

The Implementor:

- makes the change
- adds or updates tests
- records what changed

Before finalizing the implementation record, the Implementor must check:

- What new code has no caller or no reachable execution path?
- What new inputs are accepted without validation?
- What new configuration values were added, and where are they actually consumed?
- What new external calls were added, and what timeout and error handling do they use?
- What cross-module assumption does this change rely on?

At the end of implementation, the Implementor must produce one artifact containing:

- files changed
- behavior changed
- tests added or run
- residual findings, each labeled as one of:
  - **accepted risk** — must point to an explicit exclusion in the contract
  - **deferred debt** — must be added to the project's debt backlog
  - **scope insufficiency** — the work item is not ready to close

Generic "known risks" are not allowed.

### 3. Independent Review

The Reviewer checks the work item independently.

The Reviewer may use shared facts:

- files changed
- tests added
- commands run
- contract text
- implementation record

The Reviewer must not rely on the Implementor's judgment that the change is sufficient.

The Reviewer must answer:

- Is the scope still correct?
- Would at least one important test fail if the core change were reverted?
- Are any residual findings misclassified?
- Does any accepted risk lack a valid exclusion?
- Is there dead code, hidden inconsistency, or duplicated logic introduced by the change?
- Should this work item actually be reopened or expanded?

The Reviewer produces one verdict:

- **pass**
- **pass with debt**
- **blocked**

A work item is not closed without a written review verdict.

### 4. Validation

A Validator is required only if the work item changes real runtime behavior in a way that cannot be trusted from tests alone.

Examples:

- end-to-end execution path changes
- external integration behavior
- environment-dependent behavior
- scheduling or operational behavior

The Validator records:

- what was run
- what environment or data was used
- what happened
- whether anything failed

If validation is required and not done, the work item is not closed.

---

## Minimum Evidence for Closure

A work item is closed only if all of the following are true:

- the contract exists
- the implementation record exists
- the review verdict exists
- validation exists when required
- no residual issue remains unlabeled
- no issue labeled scope insufficiency remains unresolved

If code or tests change after the review verdict, all affected artifacts must be updated before the work item is considered closed.

Passing tests alone is never enough.

---

## Bug Response

When a real bug is discovered, do not only patch the immediate symptom.

The responsible agent must:

1. Fix the bug.
2. Search the codebase for the same class of bug.
3. Add a regression test for the discovered bug.
4. Identify which workflow step should have caught it.

If the bug shows that the workflow missed something systematically, record that in the next process audit.

---

## Shared Context Rule

Agents do not share reliable memory.

If something is not written in a durable project artifact, other agents must assume it does not exist.

For each work item, leave enough durable context so another agent can answer:

- what changed
- why it changed
- what was intentionally excluded
- what remains unresolved
- what the reviewer concluded

Do not rely on chat history as the primary source of truth.

---

## Process Audit

After every 3 closed work items, or immediately after a process failure, run a process audit.

A process failure includes:

- a closed work item being reopened
- an artifact contradicting the final code
- an accepted risk later turning into scope insufficiency
- a review that clearly just repeated the implementor's framing

In the audit, both Implementor and Reviewer answer:

- Did review actually happen independently?
- Were any accepted risks weakly justified?
- Did any deferred issue turn out to be scope insufficiency?
- Did any artifact become stale immediately after closure?
- Is there a repeated failure mode the workflow is not catching?
- Does the workflow need to be simplified, tightened, or corrected?

Record the audit in a durable project file.

---

## Abbreviated Rule for Trivial Work

If a work item:

- does not change behavior
- does not add or change tests materially
- does not involve a judgment call
- does not affect cross-module contracts

then the minimum process is:

- one short contract line
- one short implementation record
- one independent review verdict

Do not use the abbreviated rule if there is any real doubt about scope, correctness, or contract impact.

---

## Final Principle

The workflow is working if the human does not need to catch obvious scope mistakes, weak tests, vague unresolved issues, or missing context by hand.

If the human is repeatedly doing that, the workflow is failing, no matter how complete the paperwork looks.
