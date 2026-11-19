# Goal prompt for the quality run

Paste everything below the line as the goal. The plan it points to is the source of truth; this
prompt only says how to run it.

---

Run the Evrakçı quality plan docs/ui-goal/phase-plan.md, Phases 0 to 6 in order, on branch claude/focused-heisenberg-prspvt. Done when Phase 6's exit rule is met, or when every remaining step is blocked by an owner answer (then stop and say exactly what is needed).
START, and again after any compaction or new session:
1. Load the model-akisi skill (Skill tool) and follow it for every step. If it is missing, stop and tell the owner.
2. Read docs/ui-goal/STATE.md, docs/ui-goal/phase-plan.md (whole), docs/ui-goal/OWNER-QUEUE.md, docs/ui-goal/bugs.md, docs/ui-goal/decisions.md, PRODUCT.md, DESIGN.md. Trust these files, not memory.
3. Check: QT_QPA_PLATFORM=offscreen python -c "from PySide6.QtWidgets import QApplication; QApplication([])" works and pip install -e ".[dev]" is done. If Qt fails, install the README apt packages and say so.
EACH STEP (model-akisi mapped to this project):
- Task spec in .claude/gorevler/ (git-ignored). Sonnet implements. Kapı 1 (Haiku): ruff check . and the test files for what changed (full suite only at phase end). Kapı G (Haiku) for UI changes: tools/screenshots.py matrix for touched tabs with the clipping check, plus tools/ui_measure.py once it exists; then you (Opus) open the 2-3 worst screenshots yourself. Four Haiku lenses, a Sonnet reviewer, then your acceptance against what the owner asked. Research agents: Sonnet. Phase-end review: a fresh Opus agent on the whole phase diff and evidence. Every Agent call names its model.
- Use the project skills the plan names (perf-profile, shortcut-audit, ui-bug-hunt, feature-planning) and the design/audit skills in the plan's table as lenses (their web/React specifics do not apply to Qt).
- After every accepted step: commit, push, update STATE.md. Phase end: full suite and ruff, Opus phase review, fix or ledger its findings. No PR per phase; one PR to main only at the end of Phase 6 (repo PR template, no private content).
- From Phase 1 on, run Phase 5a-5c research (no code changes) in background Sonnet agents, reviewed by Opus, so the owner's ranking is ready before Phase 5.
HARD RULES:
- decisions.md and the plan's "Already decided" section are fixed. Fluent 2 (direction A) wins over Apple HIG; HIG is for principles. Any change to the approved look and any new Turkish text needs the owner's yes.
- Owner questions never idle the run: write them to OWNER-QUEUE.md (blocking or check), keep doing everything that does not depend on them, stop only when nothing else is left.
- Say done/clean/fixed only for what was measured, with the evidence file or test name. Never skip, weaken or delete a test to get green; change a test bound only on purpose, with the reason in the test.
- The repo is public. Never commit the model-akisi skill, Apple HIG text, real documents, task specs, screenshots outside docs/screenshots, or anything quoting the owner.
- No changes to src/evrakci/pipeline/ or the CLI unless a step truly needs a core hook (D13): minimal and tested. Window and CLI share one core.
- Tests use synthetic data only (tests/fakes.py, tools/screenshots.py:build).
- Same step fails twice on one model: move up a model. Round 3 of a step: stop it, write what was tried to OWNER-QUEUE.md, continue with other work.
- At about 150k tokens of context: update STATE.md, compact, reload model-akisi.
REPORT at each phase end, plain language, max 15 lines: what changed, numbers (tests, performance, measured rules, ledger counts by severity), what waits in OWNER-QUEUE.md, last commit.
