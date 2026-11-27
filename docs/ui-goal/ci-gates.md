# CI gates (Phase 6, step 5)

What the two workflows check, and what they cannot.

| Check | Linux (`ci.yml`) | Windows (`windows-installer.yml`, Tests step) |
|---|---|---|
| `ruff check .` | yes | yes |
| `pytest -q` (all UI, contract and Kontrol correctness tests) | yes | yes |
| `audit_shortcuts.py --check` (registry rules, a test per key, page-specific notes in `shortcuts.md`) | yes | yes |
| `audit_shortcuts.py --contract docs/ui-goal/shortcut-contract.tsv` | yes | yes |
| `tools/ui_measure.py --out ui-measure.tsv --enforce` | yes, TSV uploaded as artifact `ui-measure` | no |
| `tests/test_perf_regression.py` (300-page Kontrol run, wrong / stale pictures must be 0) | yes, inside pytest | skipped (see below) |

All steps run with `QT_QPA_PLATFORM=offscreen`. The Windows steps use the same Python, PySide6 and
pytest that the installer build already installs; the audit script needs nothing else.

## Enforcement

`ui_measure.py --enforce` exits 1 only when a rule marked `"enforced": true` in
`docs/ui-goal/rules.json` fails. None is marked today (owner question Q-03), so the step passes and
only reports. When the owner answers Q-03, setting `enforced` on the chosen rules turns the gate on
without a workflow change.

## What cannot run in CI

- **Timing.** Frame times, first paint and settle time in `perf_kontrol.py` depend on the machine.
  CI asserts correctness only (`settled_loaded_pct_real == 100`, `frames_with_wrong == 0`,
  `frames_with_stale == 0`). The timing thresholds, the real-PDF run, slow disk, low memory and
  2000 pages are run by hand (`.claude/skills/perf-profile/SKILL.md`, `baseline/perf-final.json`).
- **Perf test on Windows.** `perf_kontrol.py` reads memory from `/proc` or the `resource` module,
  neither of which exists on Windows, so `test_perf_regression.py` is skipped there. Linux covers it.
- **`ui_measure.py` on Windows.** Not run: it measures fonts and pixels, and Windows renders
  Inter and the system fonts differently, so the numbers would not match the Linux baseline. Linux
  is the reference.
- **Manual rules.** 73 of the 103 rules in `rules.json` have `"measure": "manual"` (all `HIG-CTL`,
  `HIG-WIN`, `HIG-ICO`, `HIG-MOT`, most `HIG-SPC`, `HIG-FOC`, `HIG-CON`, and `DEC-CON-03`,
  `DEC-MOT-02`, `DEC-THM-01`, `DEC-IDN-01`, `DEC-FEL-01`, `AUD-KBD-02`, `AUD-TXT-01`). They need a
  person looking at the screen; `docs/ui-goal/audit/` and the ledger hold their findings.
  `DEC-MOT-01` is a unit test and runs inside pytest.
- **Real keyboard layouts and screen readers.** Turkish Q is checked by rule (no I, no Ctrl+Alt,
  no Turkish letters in a key) but not with a real layout; NVDA and Narrator need a Windows
  machine and a person (owner checklist, Phase 6).
- **Real scans, installer on a clean account, signing.** Owner steps
  (`docs/ui-goal/owner-checklist-phase6.md`); CI installs for the runner's user only.
