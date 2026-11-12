# Confirmed decisions: UI/UX overhaul

Confirmed by the owner on 2026-11-12. These override the research files where they disagree (GOAL.md §2).

| # | Decision (confirmed) |
|---|---|
| D1 | **Identity.** The logo palette is the brand: cabinet green `#3f5a4c` is the accent, manila `#e9d9a6` marks a filed document or document start, and signal orange `#e8731a` is used only for "kontrol" (needs a check). Everything else is rebuilt. |
| D2 | **Feel.** Office-class: Windows 11/Fluent proportions, a command bar per tab, quiet surfaces, 1 px hairlines, one accent. Not a web dashboard. |
| D3 | **Font.** Bundle **Inter** (SIL OFL 1.1, approved by the owner) static Regular/Medium/SemiBold, falling back to Segoe UI Variable, then Segoe UI. The licence is recorded in `packaging/licenses/` and `docs/dependency-licenses.md`. |
| D4 | **Type scale.** Body 15/21 px, secondary 13/18, captions 13 px (the floor), section 17/24, panel 20/28, page 24/32. Tabular figures on all numbers. |
| D5 | **Scale and density.** Text size 100 / 115 / 130 / 150 %. Densities Sıkı / Normal / Geniş give rows 32 / 40 / 48 and controls 28 / 32 / 40. Default is Normal. |
| D6 | **Geometry.** 4 px grid; spacing {4, 8, 12, 16, 24, 32, 48}; radii 4 (controls), 8 (dialogs, menus, popovers), 2 (page sheets), and no others. |
| D7 | **Motion.** Durations 0 / 80 / 120 / 180 / 240 ms. Curves: standard (0.2,0,0,1), enter (0,0,0,1), exit (0.3,0,1,1), linear. Nothing over 240 ms except indeterminate progress. No motion on repeated actions (arrow keys, accept-next). Reduced motion follows Qt 6.12 `motionPreference` or the OS, and can be overridden. |
| D8 | **Icons.** Lucide (ISC) SVGs at 16/20/24 px, recoloured from tokens; they replace the current sprite, whose names stay as aliases. |
| D9 | **Themes.** Light (default), Dark, and High contrast (follows the OS high-contrast palette). Follows the OS scheme by default; manual override in Ayarlar. |
| D10 | **Contrast.** Body and table text ≥ 7:1; secondary text ≥ 4.5:1; component edges, icons and focus ≥ 3:1. Unit-tested per token pair, per theme. |
| D11 | **Focus.** Fluent ring: 2 px outer + 1 px inner, painted by a QProxyStyle/overlay on every focusable widget, never hidden. |
| D12 | **Stopped redesign.** The 4 uncommitted screen files (`kontrol.py`, `sablon.py`, `timeline.py`, `yukle.py`) were discarded with `git checkout --`; work starts from HEAD `6fd57a0`. |
| D13 | **Core.** No changes to `src/evrakci/pipeline/` or the CLI unless a UI feature truly needs a core hook; any such hook is minimal and tested. |

## Execution notes

- Orchestration: multi-agent Workflow, approved by the owner. Model tiering: Opus for direction, foundation, integration and review; Sonnet for per-tab build work; Haiku for mechanical checks.
- Phase 0 baseline at HEAD `6fd57a0`: `pytest` 526 passed / 6 skipped (after installing `tesseract-ocr` + `tesseract-ocr-tur` in the build container; without them `test_missing_language_reported` fails because it lacks the `needs_tesseract` guard). `ruff check .` clean.
- The UXKIN MCP server does not connect here, so `ui-design-review:ui-compare` falls back to platform conventions.

## Owner answers after mockup round 1 (2026-11-12)

- **Mockups not approved.** The owner's verdict: "it still looks like an old, bad office program", and the skills were not applied well enough. A second direction round follows. The bar is a modern 2026 desktop app, not legacy Office: D2's "Office-class" means calm and solid like current Microsoft 365 / Windows 11 apps, not Office 2010 chrome.
- **Wording (accepted):** "Kontrol" everywhere: "Sonraki kontrol" (N), "Önceki kontrol" (Shift+N), "Kontrol gerekenler". One status vocabulary: Emin / Orta / Kontrol / Okunamadı; İncelendi / İncelenmedi. "Şüpheli" is retired.
- **Kontrol interactions (all accepted):**
  - U = "Sonraki incelenmemiş".
  - Enter = "Belgeyi onayla" (mark the document reviewed and move on).
  - Deleting is undoable instead of confirmed: the item names the count, and Ctrl+Z restores (research 04 r11).
  - Thumbnail size is set by the status-bar zoom slider.

## Owner answer after mockup round 2 (2026-11-12)

- **Direction A, "Fluent 2 Mica", chosen** ("A is much better"). It is Windows 11 / Microsoft 365 native: the tabs sit in a Mica-toned title band, there is one icon-first command bar, the work lies on a tonal layer, and the inspector is a set of Settings-style cards. The source is `docs/ui-goal/mockups/directions/a/` (tokens.css, shell.css, README.md).
- **A's deviations, taken as accepted with the pick** (README §5 there; the owner can still object):
  1. No resting menu row. Menus open with Alt+D/E/G/T/A/Y (the row appears on Alt), the "≡" button and Ctrl+K.
  2. Tonal layers plus 1 px strokes on layers and cards; hairlines only between table rows and menu groups.
  3. Radius 8 also on the work layer and cards.
  4. Buttons identified by their label need no 3:1 border; inputs keep a 3:1 bottom edge.
  5. 36 px icon buttons in a 44 px command bar.
  6. The status-bar zoom shows only "%"; its tooltip names what it zooms.
  7. The title-band search opens the command palette.
  8. Command-bar labels are 15 px.
- These supersede D2 and D6 where they differ.

## Owner correction after round 3 (2026-11-12)

The owner rejected the round-3 "final" set: "this was not the look I approved", citing the logo and the tab shapes. Round 3 had changed A's approved chrome. It made the tabs text-only with a trapezoid selected tab, moved ≡ to the left and the job name to the status bar, restyled the inspector, and changed spacing and labels.

**Rule from now on:** direction A's approved PNGs and code (`mockups/directions/a/`) are the visual source of truth.
- The chrome, logo, tabs, command bar, inspector style and spacing are kept exactly.
- New tabs, states and themes are added in A's style without changing anything approved.
- Any improvement is proposed separately and applied only after the owner approves it.
- Round-3 deviations 9–17 are void.
