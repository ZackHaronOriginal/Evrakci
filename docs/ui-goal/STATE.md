# Run state

Updated after every accepted step. A new session or a compacted one reads this first.

## Where we are (2026-11-19)

- Phase 0: steps done; the Opus review found must-fix items now being handled: perf script
  measured with a forced repaint (fixing; perf-before.json will be re-run twice and the current
  file kept as v1), B-032 repro test, B-020 raised to S1 (fixing), suite.txt (done), second
  shortcut runs (done). Exit then waits on owner Q-01 (B-005). B-032 (S1) is fixed in Phase 2
  step 2 by the plan's order. Correction: Phase 1 work was started and committed (4cd57d)
  before Phase 0 exited, because Phase 0's exit is blocked on the owner; the run rules allow
  work that does not depend on the answer.
- Phase 1: all steps done (rules.json, rules-conflicts.md, tools/ui_measure.py + test,
  baseline/measure-before.*). Phase 1 Opus review running (`.claude/gorevler/p1-phase-review.md`).
  Owner questions Q-02 (conflicts) and Q-03 (enforcement) queued; until answered every rule is
  "reported" and nothing in the look changes.
- Phase 5a-5c research: done and committed (inventories verified, competitors re-checked,
  14 findings files). Opus research review running (`.claude/gorevler/p5-research-review.md`).
- Next: act on the three reviews (fix or ledger), then Phase 2 (Kontrol performance fix).

## Phase 0 evidence (docs/ui-goal/baseline/)

- Suite (baseline/suite.txt): run 1 at 0a28b16 1093 passed / 6 skipped, 330 s; run 2 at 79c2405 1094 passed / 6
  skipped / 31 xfailed (added: perf-script test, ledger repros). The plan's "1081 at e1e3276"
  differs because e1e3276 and HEAD collect the same 1099 tests; 1093 + 6 is the full set.
  ruff clean both times.
- screenshots-matrix.txt (72 shots, 0 clipping, run twice identical), shortcuts.tsv (run
  twice identical), shortcuts-divergent.txt and shortcuts-check.txt (exit 1: 40 bindings have no
  test; Phase 3; second run added after the review, identical),
  keywalk.txt (all six tabs OK, default and dark/150 %, run twice identical).
- perf-before.json (v1, forced repaint per step; the review showed this hides B-032): fake x2
  sets, slow, real once (first-paint spread 21 %); being re-measured.
  Real-PDF RSS ~1186 MB after the sweep (fake ~211 MB): Phase 2 memory target.
  Frame log (real scroll path, backing store): ~304/309 frames show a wrong page and 305
  stale while the service is 100 % loaded: B-032. The Phase 0 review checks whether this is
  the real bug or an offscreen artifact; Phase 2 must not use it before that verdict.
- Ledger: S1 5 (B-011, B-021, B-023, B-029 fixed in cefd148 + faf32a5; B-005 waits for Q-01),
  S2 2 (B-008, B-032), S3 21, S4 4, 1 not a bug; B-033, B-034 needs-repro (from 5a).

## Notes for later phases

- Selective undo (a queued toast undoing its own older step) is a Phase 5 idea, not built.
- tests/ui/test_feedback.py::test_toast_times_out failed once under heavy parallel load and
  passes alone: timing-sensitive; watch it in full-suite runs.
- Phase 2 inputs: B-032, perf-before.json, findings-performance.md (cap cache by bytes).

- Last commit: see `git log -1` (faf32a5 when written)
- Open owner questions: `OWNER-QUEUE.md` (Q-01, Q-02, Q-03 blocking)
