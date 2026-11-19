# Goal prompt for the quality run

Paste everything below the line as the goal. The plan it points to is the source of truth; this
prompt only says how to run it.

---

Run the Evrakçı quality plan to the end: `docs/ui-goal/phase-plan.md`, Phases 0 to 6, in order,
on branch `claude/focused-heisenberg-prspvt`. The goal is reached when Phase 6's exit rule is met,
or when every remaining step is blocked by an owner answer (then stop and say exactly what is
needed).

**Before the first step, and again after any compaction or new session:**
1. Load the `model-akisi` skill (Skill tool) and follow it for every step. If it is not
   installed, stop and tell the owner; do not continue without it.
2. Read `docs/ui-goal/STATE.md`, `docs/ui-goal/phase-plan.md` (whole file), `OWNER-QUEUE.md`,
   `bugs.md`, `decisions.md`, `PRODUCT.md` and `DESIGN.md`. Trust these files, not memory.
3. Check the environment: `QT_QPA_PLATFORM=offscreen python -c "from PySide6.QtWidgets import
   QApplication; QApplication([])"` must work, and `pip install -e ".[dev]"` must be done. If Qt
   does not start, install the system packages listed in README (apt) and say so.

**How each step runs** (model-akisi, mapped to this project):
- Write a task spec in `.claude/gorevler/` (git-ignored). Sonnet implements. Kapı 1 (Haiku):
  `ruff check .` and the test files for what changed (the full suite only at phase end). Kapı G
  (Haiku) for any UI change: `tools/screenshots.py matrix` for the touched tabs with the clipping
  check, and `tools/ui_measure.py` once it exists; then you (Opus) open the 2 to 3 worst
  screenshots yourself. Four Haiku lenses, a Sonnet reviewer, then your acceptance against what
  the owner asked. Research and inventory agents: Sonnet. Phase-end review: a fresh Opus agent on
  the whole phase diff and its evidence. Give every Agent call a model.
- Use the project skills where the plan names them: `perf-profile`, `shortcut-audit`,
  `ui-bug-hunt`, `feature-planning`, and the design and audit skills listed in the plan's table
  (as lenses; their web/React specifics do not apply to Qt).
- After every accepted step: commit, push, update `STATE.md`. At the end of each phase: run the
  full suite and `ruff`, do the Opus phase review, fix or ledger its findings, then open or update
  one pull request for that phase (repo PR template; no private content).
- From Phase 1 on, run Phase 5a to 5c (research, no code changes) in background Sonnet agents,
  reviewed by Opus, so the owner's ranking is ready before Phase 5.

**Hard rules:**
- Decisions in `decisions.md` and the plan's "Already decided" section are fixed. Fluent 2
  (direction A) wins over Apple HIG; Apple HIG is used for principles. Any change to the approved
  look, and any new Turkish text, needs the owner's yes.
- Owner questions never idle the run: write them to `OWNER-QUEUE.md` (blocking or check), keep
  working on everything that does not depend on them, and stop only when nothing else is left.
- Say "done", "clean" or "fixed" only for what was measured, with the evidence file or test name.
  Never skip, weaken or delete a test to get green; change a test bound only on purpose, with the
  reason in the test.
- The repo is public. Never commit: the `model-akisi` skill, Apple HIG reference text, real
  documents, task specs, screenshots outside `docs/screenshots`, or anything quoting the owner.
- No changes to `src/evrakci/pipeline/` or the CLI unless a step truly needs a core hook (D13):
  minimal and tested. Window and CLI stay on the same core.
- Tests use synthetic data only (`tests/fakes.py`, `tools/screenshots.py:build`).
- Same step failing twice with one model: move up a model. Round 3 of the same step: stop that
  step, write what was tried to `OWNER-QUEUE.md`, continue with other work.
- Context: at about 150k tokens, update `STATE.md` and compact; reload `model-akisi` after.

**Report to the owner** at each phase end, in plain language, at most 15 lines: what changed,
the numbers (tests, performance, measured rules, ledger counts by severity), what is waiting in
`OWNER-QUEUE.md`, the PR link.
