# Agent-Driven Development: Quality and Closure Process

A workflow proposal for projects where autonomous agents implement and a reviewer validates.

---

## Context and Problem

In staged development with autonomous implementors, the following failure modes recur across projects:

- Dead code accumulates when scaffolding is added speculatively and never cleaned up
- Config values are loaded but never validated or consumed by production code
- Tests are written to pass, not to protect — they do not fail when the code they cover is removed
- External integrations ship without operational requirements (timeouts, error wrapping)
- Cross-module inconsistencies go undetected because each stage is reviewed in isolation
- Real bugs are patched locally without asking whether the same class of bug exists elsewhere
- Structural review happens at the end of the project, when the cost of fixing is highest
- Residual issues are recorded as generic "risks" without classification — hiding whether they represent acceptable deferral, tracked debt, or an incomplete stage contract

These failures share a root cause: **the workflow optimized for forward momentum rather than robust closure**. "Tests pass" became the criterion for done. It is not sufficient.

---

## Roles

This document uses role names, not agent names. The same pattern applies regardless of which tools or models fill each role.

**Implementor** — writes code, writes tests, performs adversarial self-review before declaring a stage done.

**Reviewer** — performs independent structural review using different criteria than the implementor. Owns the stage-exit decision. Never accepts the implementor's self-certification as a substitute for independent review.

**Validator** — confirms observable business behavior and real-world correctness. Should not be the first line of defense against operational defects or structural problems. If the validator is finding missing timeouts or broken config contracts, the upstream process has failed.

The critical principle: **the reviewer must not use the same success criterion as the implementor.** If both ask "do tests pass?", there is no independent review.

---

## Stage Workflow

Every stage follows five explicit phases. The proportionality rule below describes when phases may be abbreviated.

### Phase 1 — Contract Review (Reviewer + Implementor, before coding)

Define before any implementation begins:

- What are the inputs, outputs, and failure behavior of this stage?
- What cross-module dependencies does this stage introduce or modify?
- For each new configuration value:
  - Is it required or optional?
  - What validation rule applies (type, format, range, allowed values)?
  - What is the default behavior when absent?
  - What is the first production code that reads it?
- For each new external integration:
  - What are the operational requirements? (timeout, retry policy, error wrapping)
- Are there shared concepts this stage touches? (datetime/timezone interpretation, error handling, allowed values, data boundaries)
- What is explicitly out of scope for this stage, and why?
  - For each exclusion: state what invariant or existing mechanism makes it safe to exclude.
  - "No production changes" is not a sufficient exclusion on its own — it must be paired with the reason (e.g., "the runner already enforces this invariant").

This phase produces a short checklist, not a design document. Its purpose is to make implicit contracts explicit before the implementor begins.

### Phase 1.5 — Judgment Check (Implementor, before contract is finalized)

**Triggered when the contract contains a non-obvious decision.** Examples:

- Narrowing scope to documentation only instead of fixing behavior
- Explicitly not correcting production code (accepting a tradeoff)
- Choosing between two or more technically plausible approaches
- Deferring a class of fix rather than patching the immediate symptom

When triggered, the implementor must answer these four questions before the contract is finalized:

1. Do you agree with this decision?
2. What is the strongest alternative you see?
3. What hidden implementation risk does this contract create?
4. Does this decision require a new Phase 1 exclusion?

The reviewer then finalizes the contract brief based on the implementor's response. This is not asking the implementor to overrule the reviewer — it is forcing a second technical pass before scope is frozen.

**This phase is not required for every task.** It is only required when the contract contains a real judgment call, not just task decomposition.

### Phase 2 — Implementation (Implementor)

The implementor writes code and tests under two hard constraints:

- No configuration field is added without a real production consumer in this stage, or an explicitly tracked task for a future stage.
- No external network call ships without an explicit timeout and wrapped errors.

### Phase 3 — Adversarial Self-Review (Implementor, before claiming done)

Before declaring implementation complete, the implementor must answer:

- What new code has no caller in production or test code?
- What inputs are accepted without validation?
- What assumptions does this stage make that differ from other modules?
- What operational behaviors are absent? (timeouts, retries, fallbacks)
- If I revert the core change of this stage, which test fails?
- Does any finding during self-review indicate that the stage contract is too narrow or incomplete?

Every residual issue must be classified as one of the following before declaring done:

- **Accepted risk** — the stage contract is still sufficient; the issue is real but explicitly out of scope and safe to defer. Must reference the Phase 1 exclusion that covers it, and explain why that exclusion still holds after implementation.
- **Deferred debt** — the issue does not block closure, but must be recorded in the technical debt backlog before the stage is closed.
- **Scope insufficiency** — the finding indicates the current stage contract is incomplete or misleading. The stage must not be declared done until the contract is amended or the reviewer explicitly approves the narrower scope.

A residual issue may not be recorded as a generic "risk" without one of these three labels.

This is not optional. A stage that cannot answer these questions is not done.

### Phase 4 — Independent Structural Review (Reviewer, independently)

The reviewer performs this phase **without reading the implementor's Phase 3 conclusions first**. Independence is the point.

The reviewer must check:

- Is there new code with no caller in production code?
- Are all new configuration values validated appropriately for their type and constraints?
- Are all new configuration values actually read by production code?
- Do all new external calls have explicit timeouts?
- Are cross-module invariants consistent? Specifically:
  - datetime and timezone interpretation
  - error handling and exception types
  - allowed values for configuration shared across modules
  - data boundaries and ownership between modules
- Is there duplicated logic that now exists in more than one module?
- Does at least one test cover invalid input or failure-path behavior for new code?
- Would at least one test fail if the core change of this stage were reverted?
- Has the implementor classified every residual issue? For each item labeled "accepted risk", verify it is actually covered by a Phase 1 exclusion — not merely assumed to be out of scope.

If any answer is "unknown", the stage is not closed.

### Phase 5 — End-to-End Validation (Validator)

For any stage that modifies the main execution path:

- A full end-to-end run must succeed with realistic or production data before the stage is closed.
- The validator confirms business correctness, not structural integrity. Structural integrity is owned by Phases 3 and 4.

---

## Proportionality Rule

Not every stage requires the full weight of the five-phase process.

A stage may abbreviate Phases 1 and 3 if **all three** of the following are true:

- No new configuration fields are added
- The main execution path is not modified
- No new external callers are introduced

In that case:
- Phase 1 is reduced to one question: "What contract or assumption changes in this stage?"
- Phase 3 is reduced to one question: "If I revert this change, which test fails?"

Phase 4 is never abbreviated. Phase 5 is required whenever the stage affects a real execution path and is not relaxed when applicable. The independence requirement for Phase 4 does not relax for trivial stages.

---

## Process Check — Periodic Workflow Audit

The stage workflow governs how individual items close. This section governs how the workflow itself stays honest over time. Without this, process drift accumulates silently.

### Trigger

A Process Check is mandatory in either of these conditions:

- **Every 3 closed items** — before starting the next item, both agents audit the last 3 closures.
- **Immediately** after any of the following:
  - A completed task had to be reopened or corrected post-closure
  - An artifact was found to contradict the final code state
  - A residual issue was reclassified from accepted risk or deferred debt to scope insufficiency
  - Phase 4 review appeared to restate implementor conclusions rather than challenge them

### Required questions

Both agents answer these questions independently, then compare. During a Process Check, each agent may inspect shared artifacts and code state, but must not rely on the other agent's judgment about whether the process worked correctly — the same independence rule that applies to Phase 4 applies here.

1. Did Phase 4 actually happen independently, or did it lean on implementor framing?
2. Were any accepted risks weakly justified — missing a valid Phase 1 exclusion or an invariant that actually holds?
3. Did any deferred debt item turn out to be scope insufficiency in disguise?
4. Did any artifact become stale immediately after closure (contradicted by code within one or two tasks)?
5. Is there a recurring failure mode across the last 3 items that the workflow does not currently address?
6. Should any existing phase, checklist item, or artifact requirement be removed, simplified, or strengthened?

### Output

Append findings to a rolling audit file kept in the project's documentation directory. Each project maintains its own file; the name and location are decided per project.

Each entry includes: the item count that triggered the check, answers to the six questions, any workflow changes agreed upon, and any task or artifact that must be reopened or corrected as a result. If no changes are needed, record that explicitly — a clean check is also a data point.

### Rule

If a Process Check is due and both agents skip it to start the next item, that is itself a workflow violation. Record it in `docs/process_audit.md` and explain why it was skipped.

---

## Checklists

### A. Stage Exit Checklist

This checklist is owned jointly: the implementor completes items marked **(I)**, the reviewer completes items marked **(R)** independently.

**Mechanical gates — Implementor (Phase 3)**
- [ ] **(I)** Linter and formatter pass with zero warnings or errors
- [ ] **(I)** All tests pass
- [ ] **(I)** No new code exists without a caller in production or test code
- [ ] **(I)** All new configuration values are validated appropriately for their type and constraints
- [ ] **(I)** All new configuration values are read by production code
- [ ] **(I)** All new external calls have an explicit timeout
- [ ] **(I)** At least one test covers an invalid-input or failure-path case

**Effectiveness gates — Reviewer (Phase 4, independent)**
- [ ] **(R)** At least one test would fail if the core change of this stage were reverted
- [ ] **(R)** No dead code introduced in this stage (verified by search, not assumed)
- [ ] **(R)** No duplicated logic across modules
- [ ] **(R)** Cross-module invariants are consistent: datetime/timezone, error types, config values, data boundaries
- [ ] **(R)** Test coverage is protective, not merely present

### B. Bug Response Checklist

When a real bug is discovered at any point:

1. Fix the immediate bug
2. Search the entire codebase for the same class of bug — not just the same file
3. Add a direct regression test that fails without the fix
4. Identify which Phase 3 or Phase 4 check should have caught this
5. Record unresolved instances or related debt in the project backlog

A bug that is fixed without step 2 is a patch. Steps 2–5 are what convert a patch into systemic hardening.

### C. Integration Checklist

For every new external API client or network call:

- [ ] Explicit timeout configured
- [ ] Transport and protocol errors are caught and wrapped in a domain error type appropriate to the integration
- [ ] Test for successful response
- [ ] Test for error response
- [ ] Test for malformed or unexpected response
- [ ] No hidden retry behavior unless explicitly designed and documented

### D. Configuration Checklist

For every new environment variable or configuration field:

- [ ] Required vs optional is explicit
- [ ] Type, format, range, and allowed values are validated at load time, not at first use
- [ ] Default behavior when absent is defined and tested
- [ ] Field is read by production code within this stage or the future stage is tracked
- [ ] Documented in the project's configuration reference

---

## Test Effectiveness Standard

A test that passes regardless of whether the code it covers is present is not regression coverage. It is documentation at best.

For every new test, the implementor must verify: **does this test fail if the code it claims to protect is removed or reverted?**

This rule is mandatory for:

- Bug-fix tests
- Config validation tests
- Date, time, and timezone handling
- Integration client behavior

If the answer is "I'm not sure", the test is not sufficient.

---

## Persistent Artifacts

Two artifacts must exist and stay current throughout the project:

**Review checklist** — the checklists above, kept in the repository. Updated when new categories of defect are discovered.

**Technical debt backlog** — a tracked list of known issues intentionally deferred. Prevents known problems from disappearing into chat history or commit messages. Every item deferred from a stage-exit check must appear here.

---

## Context Sharing Without Shared Memory

Agents do not share memory. Each role operates with its own context window and has no direct access to another agent's reasoning or session history. If state is not externalized, it does not exist for the rest of the workflow.

**The rule:** if an agent did not leave a compact external record, the other roles do not know what it did.

### Handoff Artifacts

Each phase must produce a durable artifact before the next phase begins. These do not need to be long — they need to be legible, structured, and written to disk.

| Phase | Artifact | Produced by |
|---|---|---|
| Phase 1 | Contract brief: inputs, outputs, failure behavior, new config, new invariants, open assumptions | Reviewer + Implementor |
| Phase 1.5 | Judgment check record: implementor's answers to the four questions; reviewer's final contract decision and any revised exclusions | Implementor + Reviewer |
| Phase 2–3 | Implementation record: files changed, behavior changed, tests added/run; each residual finding classified as **accepted risk** / **deferred debt** / **scope insufficiency** with Phase 1 exclusion reference | Implementor |
| Phase 4 | Review verdict: pass / blocked / pass-with-debt, findings, missing tests, items escalated to debt | Reviewer |
| Phase 5 | Validation record: what was run, with what data, what passed, what failed, exact reproduction details | Validator |

No stage is considered closed unless the relevant handoff artifacts exist in durable form.

**Artifact synchronization rule**: if code changes after a Phase 4 review verdict, any affected artifact for that task must be updated before the task is considered closed. A Pass verdict does not freeze the artifact set — it freezes the review criterion. If the implementation continues to evolve, the artifacts must follow.

### Facts vs Judgments

Shared artifacts should carry facts, not judgments. The reviewer must still form independent conclusions.

**Safe to share** (facts):
- files changed
- tests added or removed
- commands run and their output
- explicit contract statements
- environment and data used

**Must remain independent** (judgments):
- whether a test is protective
- whether code is dead
- whether cross-module consistency holds
- whether closure criteria are satisfied

Sharing a judgment pre-empts the independent review. Sharing a fact enables it.

### Minimum Viable Handoff

If the full artifact set feels heavy for a given stage, the minimum acceptable handoff is a short structured note covering:

1. What changed
2. What files were touched
3. What tests were added or run
4. What remains risky
5. What the next role should verify

This minimum applies to trivial stages. Non-trivial stages require the full artifact set.

### Recording Decisions as Rules

When a decision is made during any phase — a design choice, a constraint, a tradeoff — record it at the level of a reusable rule, not just as a patch description.

Instead of: *"fixed timezone bug"*
Write: *"configured timezone is authoritative over host-local time for all aware datetime interpretation"*

This turns a one-time fix into a constraint the whole workflow can apply consistently.

---

## Why This Works

The workflow described above prevents the failure modes listed at the top because:

- Structural problems are caught at stage boundary, not at project end
- Tests are evaluated for effectiveness, not just presence
- Dead code is caught by a mandatory caller check, not by periodic cleanup
- Cross-module inconsistencies surface in Phase 4's invariant check
- Bug fixes become class-wide audits rather than local patches
- The validator confirms behavior, not structural correctness — which is the appropriate division of responsibility

The core invariant of the whole process: **a stage is not done when tests pass. A stage is done when an independent reviewer has verified that the tests are protective, the code is clean, and the contracts are consistent.**
