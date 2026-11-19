# Run state

Updated after every accepted step. A new session or a compacted one reads this first.

## Where we are (2026-11-19, evening)

- Phase 0: done except the exit's owner part: Q-01 (B-005, last open S1 besides B-032 which is
  Phase 2's fix by plan order). Evidence complete: suite.txt (2 runs), perf-before.json v2
  (real path, abe8da4; v1 kept), shortcuts/keywalk/screenshots twice, ledger triaged. Review:
  .claude/gorevler/p0-phase-review.md; all its must-fixes done (B-020 29b5e01, perf script
  5b4d613, bookkeeping 302bb99).
- Phase 1: done. Review must-fixes done (be87491); measure-before re-baselined (d8c0538: 234
  fails, run twice identical). Phase-end full suite at d8c0538: 1110 passed, 6 skipped,
  27 xfailed, 2 failed (test_ui_measure probes broken by a stylesheet left by earlier tests);
  fixed in a075e9c and checked with tests/ui (664 passed, 27 xfailed; old file: 2 failed).
  ruff clean. Phase 0+1 report sent. Owner: Q-02 (25 conflict
  rows), Q-03 (enforcement). Then write the Phase 0+1 report (max 15 lines) to the owner.
- Phase 2: CLOSED. Fix bfb92bc + review fixes f35f56b; perf-after-phase2.json all targets met;
  full suite 1118 passed / 6 skipped / 26 xfailed (before f35f56b, which was checked with the
  Kontrol test files); Opus review found no S1/S2 (.claude/gorevler/p2-phase-review.md); F6/F7
  ledgered (B-042, B-043). Owner check Q-07. Report sent.
- Phase 3: DONE except its exit rule, which waits on the owner: 110 of 319 rows keep a strict
  xfail (Q-08 texts/decisions, Q-09 keys kept disabled because older tests pin it). Last fixes
  be26e31 (3F). Full suite on 3F: 2121 passed / 6 skipped / 205 xfailed, 1 flaky (margin test,
  fixed in be26e31, passes 3/3 under load). Review .claude/gorevler/p3-phase-review.md; leftovers
  ledgered B-048..B-050. Report sent.
- Phase 4 IN PROGRESS (spec .claude/gorevler/2026-11-19-p4-audit.md: Görev A = audit files,
  Görev B = fix step; step 7 lenses = Sonnet agent loading design-skills:design-critique,
  design-skills:accessibility-audit, audit-suite:audit-as-ux-eng, design-skills:interaction-design
  (or ux-writing), appending rows to <screen>-findings.md).
  Kontrol: audit + lenses done (32 findings; S2 01/02/03/08=B-033). Fix step RUNNING.
  Yükle: audit + lenses done (49 findings; S2 F-yukle-01; check F-yukle-42 undo of batch delete
  first: S1 if not undoable; F-yukle-39 load Qt's Turkish translation). Fix step next.
  Değerler: audit done (8529c72; 40 findings; S2 F-01 N key always first kontrol (triggered
  passes checked flag as step), F-02 long variable name overflow, F-03 double click confirms
  two). Lenses RUNNING. Fix step after.
  Then Şablonlar, Dışa Aktar, Rehber (Görev A, lenses, Görev B). After each fix step: Kapı 1
  (tests), Kapı G (matrix + ui_measure for the screen, open 2-3 shots), lenses (Haiku a+c, b+d),
  Sonnet reviewer, accept, commit, merge findings into bugs.md (ledger rows for S1/S2 and open S3).
  Phase 4 end: measure-after.tsv next to measure-before.tsv, quick perf check (perf_kontrol.py
  --runs 3), full suite, Opus whole-app review, owner check row (walk each screen).
  Lesson: run the FULL tests/ui after any fix step that enables/disables actions (3E broke
  older tests while its own file list passed).
- Phase 5d: ideas-ranking.md committed (e71981c), Q-06 waits for the owner. 5e waits on Q-06.
- Next after Phase 2: Phase 3 (shortcut contract; skill shortcut-audit), then Phase 4.

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
