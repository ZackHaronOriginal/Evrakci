# Run state

Updated after every accepted step. A new session or a compacted one reads this first.

## Where we are (2026-11-19, late)

- Phase 0: all steps and review must-fixes done except: perf-before.json v2 is being re-run
  (script at 5b4d613 measures the real path; run script /tmp/claude-0/perf2/run.sh, outputs in
  /tmp/claude-0/perf2/: fake x2, slow, real x2, 5 runs each; v1 kept as perf-before-v1.json).
  When done: combine into baseline/perf-before.json like v1 (medians, spread, notes: real-path
  loaded % is 0 because of B-032; first-paint spread). Phase 0 exit then waits only on owner Q-01
  (B-005). B-020 fixed (29b5e01). B-032 S1 is fixed in Phase 2 step 2.
- Phase 1: exit rule met (review .claude/gorevler/p1-phase-review.md). Must-fixes M1-M4 and
  L-1..L-8 being fixed by an agent (spec .claude/gorevler/2026-11-19-p1-review-fixes.md). After it:
  Kapı 1, commit, then re-run the full ui_measure matrix twice and replace
  baseline/measure-before.tsv + summary (only after the perf run finished). L-6 is ledger B-038.
- Phase 5a-5c: done, reviewed (.claude/gorevler/p5-research-review.md), corrections f754a5e.
  5d: agent writing docs/ui-goal/ideas-ranking.md; then Opus check and owner question Q-06
  (rank must/should/later/drop).
- Next after these: Phase 2 (Kontrol performance). Inputs: B-032 cause proven by the Phase 0
  review (TimelineView inherits QListView.scrollContentsBy which does not repaint this view;
  candidate fix in p0-phase-review.md section 1.4: override scrollContentsBy with
  viewport().scroll(dx, dy), and request thumbnails for visible_rows() from the scroll handler,
  not only from paint), perf-before.json v2, findings-performance.md (cap cache by bytes), real-PDF
  RSS ~1.2 GB.

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
- Ledger (see bugs.md): S1 B-011, B-020, B-021, B-023, B-029 fixed; B-005 waits for Q-01;
  B-032 S1 for Phase 2. New: B-033, B-034 needs-repro; B-035 S2, B-036 S3, B-037 S4, B-038 S2.

## Notes for later phases

- Selective undo (a queued toast undoing its own older step) is a Phase 5 idea, not built.
- tests/ui/test_feedback.py::test_toast_times_out failed once under heavy parallel load and
  passes alone: timing-sensitive; watch it in full-suite runs.
- Phase 2 inputs: B-032, perf-before.json, findings-performance.md (cap cache by bytes).

- Last commit: see `git log -1` (faf32a5 when written)
- Open owner questions: `OWNER-QUEUE.md` (Q-01, Q-02, Q-03 blocking)
