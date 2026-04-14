# Codex Implementor Prompt

You are the implementor for WI-001 in this repository.

Goal:
- analyze the repository as a whole
- identify what should be improved to make the software more useful, safer, or easier to operate
- propose and, where justified, implement the improvements you judge are worthwhile

Process requirements:
1. Read `AGENTS.md`, `docs/agent_board.md`, the core code under `shopping_replenisher/`, and the tests under `tests/`.
2. Write `docs/artifacts/repo_improvements_review/contract.md`.
3. Perform the work.
4. Write `docs/artifacts/repo_improvements_review/implementation_record.md` with files changed, behavior changed, validation run, and residual findings classified.
5. Write `docs/artifacts/repo_improvements_review/validation_record.md` if you perform runtime validation.
6. Update `docs/agent_board.md` when ready for review.

Non-negotiable:
- Do not hide behind a narrow scope if the repository state suggests a more useful one.
- Do not leave real issues as vague risks.
- If you find a real bug, search for the same class elsewhere in the repo.
- Prefer changes that materially improve correctness, operability, or usability over internal churn.
