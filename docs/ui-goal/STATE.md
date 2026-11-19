# Run state

Updated after every accepted step. A new session or a compacted one reads this first.

- Phase: 0 (ground truth and "before" numbers)
- Done in Phase 0:
  - step 1 suite run 1: 1093 passed, 6 skipped, 330 s; ruff clean (run 2 on 79c2405 in progress).
    The plan's "1081 passed at e1e3276" differs: e1e3276 and HEAD collect the same 1099 tests
    (only the version string changed since), so 1093 + 6 is the full set here.
  - steps 2, 4, 5: `baseline/screenshots-matrix.txt` (72 shots, 0 clipping), `shortcuts.tsv`,
    `shortcuts-divergent.txt`, `shortcuts-check.txt` (exit 1: 40 bindings have no test),
    `keywalk.txt` (all six tabs OK, default and dark/150 %). Each run twice, identical.
  - step 3: `baseline/perf-before.json` (fake x2, slow, real; 5 runs each). Script extended in
    75291cc (renders at first paint, RSS, --runs, real-scroll --frame-log).
  - step 6: jitter reproduced by the frame log (~304/309 real-scroll frames show a wrong page,
    305 stale) while the service has 100 % loaded: ledger B-032. To be checked by the phase
    review: is the "viewport did not move" frame log an offscreen artifact or the real bug?
  - step 7: ledger triaged (S1 5, S2 2, S3 21, S4 4, 1 not a bug). Repro tests in
    tests/ui/test_ledger_{a,b,c}.py as strict xfail.
- Step in progress: step 8, S1 fixes B-011, B-021, B-023, B-029 (spec p0-s1-fixes). B-005 waits
  for the owner (Q-01).
- Next: gates on the S1 fixes, commit; Phase 0 Opus review (perf script vs real paint path);
  then Phase 1, and start Phase 5a-5c research in the background.
- Last commit: see `git log -1` (79c2405 when written)
- Open owner questions: `OWNER-QUEUE.md` (Q-01 blocking: Phase 0 exit)
- Evidence: `docs/ui-goal/baseline/`
