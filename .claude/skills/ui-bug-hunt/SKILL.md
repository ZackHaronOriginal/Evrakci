---
name: ui-bug-hunt
description: Use when asked to find, triage or regression-check UI bugs in the Evrakçı window (clipping, focus, theme, zoom, keyboard-only use) or before a UI release. Runs the screenshot matrix, clipping check and keyboard walkthrough, then records findings in docs/ui-goal/bugs.md.
---

# UI bug hunt

Everything runs offscreen with invented demo data (`tools/screenshots.py:build`); never use
real documents. Targets come from PRODUCT.md (1366x768 up to 1920x1080, weak eyesight, keyboard
heavy, WCAG AA) and DESIGN.md (three themes, text 100-150 %, no hex outside tokens).

## 1. Screenshot matrix and clipping check

```bash
QT_QPA_PLATFORM=offscreen python tools/screenshots.py matrix /tmp/shots          # exit 1 on clipping
QT_QPA_PLATFORM=offscreen python tools/screenshots.py matrix --allow /tmp/shots  # report only
QT_QPA_PLATFORM=offscreen python tools/screenshots.py matrix --compare /tmp/shots
QT_QPA_PLATFORM=offscreen python tools/screenshots.py states /tmp/states         # empty states, loupe, drop overlay
```

The matrix is 6 tabs x {light, dark, hc} x {1366x768, 1920x1080} x text {100, 150} = 72 files
named `<tab>-<theme>-<w>x<h>-<text>.png` (tab slugs: yukle, kontrol, sablonlar, degerler,
disa-aktar, rehber). Each `KIRPILMA` line in the output is a finding (elided text, text wider
than its room, widget cut by its parent, card cut by a scroll edge, table cell too narrow);
the last line `ÖZET` gives the counts. Then look at the PNGs: open them (Read tool) at least for
every tab in `dark-1366x768-150` and `hc-1366x768-100`, the worst cases. Look for: low
contrast text, orange used for anything but Kontrol (DESIGN.md "Rider Means Kontrol"), status
shown by colour alone, text under 13 px, overlapping or misaligned items, wrong paper colour in
dark, missing focus ring, a scrollbar where the layout should fit at 100 %.
`--compare` prints a coarse drift against `docs/ui-goal/mockups/final-a/png`; it is a signal, not a pass mark.

Existing guards to extend instead of duplicating: `tests/ui/test_phase4.py`
(`test_no_tab_clips_at_1366x768_100_percent`, `test_targets_are_at_least_24_px`),
`tests/ui/test_card_scroll.py`, `tests/ui/test_tokens.py` (contrast), `tests/ui/test_theme.py`.

## 2. Keyboard-only walkthrough, per tab

Automated Tab walk (focus order, traps, unnamed controls, work area reachable):

```bash
QT_QPA_PLATFORM=offscreen python .claude/skills/ui-bug-hunt/keywalk.py
QT_QPA_PLATFORM=offscreen python .claude/skills/ui-bug-hunt/keywalk.py --tab degerler --theme hc --text 150
```

Then do the manual part in code with `QTest` (or on a real window if one is available) for each
tab, mouse never touched: Ctrl+1..6 reaches the tab and puts focus in the main view; every
command-bar button is reachable (Tab) and fires with Space/Enter; every command has its key
(see the `shortcut-audit` skill); Ctrl+K opens the palette, Shift+F1 the sheet, Ctrl+F finds,
Esc closes dialogs and never discards work; F6 moves between regions; a right-click menu (see top25.md item 7) has a keyboard way to open; focus is always visible (2 px outer + 1 px inner ring) and returns to
where it was after a dialog closes. Primary journey: open job, check a document in Kontrol
(arrows, N, Enter), correct a value in Değerler (Enter / F2 / Esc), export (Ctrl+E).

## 3. Theme and zoom matrix

Themes: light, dark, hc (`theme.manager().set_mode(...)`, also Ayarlar). Text size 100, 115, 130,
150 % (`set_text_scale`), densities Sıkı / Normal / Geniş. The matrix covers 100 and 150; spot-check
115 and 130 with `keywalk.py --text 130` and a one-off screenshot of the tab that looks tightest
(Değerler, Kontrol inspector, title band at 150 %). In hc check that selection, focus, disabled
and Kontrol are distinguishable without colour. Kontrol zoom (status-bar slider) at min and max
page size, and Ctrl+wheel on Kontrol, Şablonlar and Rehber. Do not change runtime theme and
screenshot: shots are taken from windows built fresh in each theme.

## 4. Record findings in `docs/ui-goal/bugs.md`

One row per bug, newest last, never delete a row (change Status instead). Columns:

| ID | Sev | Tab | Where (theme / size / text) | Repro | Expected vs actual | Evidence | Status |
|---|---|---|---|---|---|---|---|

- ID: `B-NNN`, continuing the existing sequence (B-001 to B-031 came from the feature inventories).
- Severity: **S1** data loss, wrong silent output, or a flow that cannot be completed by keyboard;
  **S2** unreadable or unusable in a supported theme/size (clipped text, lost focus, contrast
  below D10), or Kontrol not shown with icon + word; **S3** visible but workable (misalignment,
  inconsistent spacing or wording); **S4** polish.
- Repro: numbered steps from a fresh `screenshots.build` window, with exact keys or the matrix
  file name (`kontrol-dark-1366x768-150.png`). A bug without a repro is marked `needs-repro`.
- Evidence: PNG name, the `KIRPILMA` line, or the failing test name. Do not commit PNGs
  (`.gitignore` excludes them except `docs/screenshots`); cite the command instead.
- Status: `open`, `fixed (commit or test name)`, `wontfix (reason)`, `needs-repro`.
- Check the ledger for duplicates before adding. When fixing a bug, add a regression test in
  `tests/ui` (offscreen, the `demo` fixture pattern in `tests/ui/test_phase4.py`) and reference
  it in Status.

Report: counts by severity, S1/S2 rows verbatim, anything not checked (no real Windows,
no Turkish keyboard, no real scanner documents).
