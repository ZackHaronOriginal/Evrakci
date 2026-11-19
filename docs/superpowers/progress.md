# Progress: Plans 1–7

Last checked 2026-11-13: **1091 tests pass** (6 skipped), `ruff check .` is clean.

| Plan | State | Review fixes (commit) |
|---|---|---|
| 1 Core, CLI, splitting | done | — |
| 2a OCR engine test | done; owner picked Tesseract + tur_best | report `docs/ocr-motor-karsilastirma.md` |
| 2b OCR text layer | done | "fix: address OCR text layer review findings" |
| 3 Templates | done | "fix: address template review findings" |
| 4 Review and export | done | "fix: address review and export review findings" |
| 5 Window | done; Kartotek look approved 2026-11-07 | "fix: address the window review findings" |
| 6 Windows installer | done; Tesseract built from source by vcpkg; Windows run 42561985121 green | "fix: address Windows installer review findings" |
| 2–4, 6 second review | done 2026-11-09; four fresh whole-plan reviews, every finding fixed | `1b7d1e1`, `3636dae`, `edaac39`, `df04532` |
| 7 Linux build | done; GitHub Actions build and clean Debian 12 / Ubuntu 24.04 installs are green (run 42552347140) | "fix: address the Linux build review findings" |

## What works (CLI)

- `evrakci ayirac`: prints the QR separator sheet.
- `evrakci is olustur | ekle | parti-tasi | parti-sil | goster | listele | sil`: jobs and batches.
- `evrakci is filtre | kes | sayfa | bos-sayfalar`: splitting by "every N pages" on selected pages,
  manual cuts, delete, undelete, rotate and blank pages.
- `evrakci is sablon-uygula | oku | degerler | deger`: apply templates, read values, fix values.
- `evrakci is disa-aktar`: named PDFs, `index.xlsx` and `[kontrol]` marks.
- `evrakci sablon …`: create, edit, test, import and export templates, with user-named variables
  and ordered variants.
- `evrakci ocr`: Turkish text layer, PDF/A-2b, falling back to plain PDF.
- `evrakci ocr-karsilastir` and `ocr-modelleri-indir`: compare OCR engines and download OCR data.
- `evrakci ayar`: settings, including retention.

## Key decisions

- **OCR:** Tesseract + tur_best, chosen by the owner. OCRmyPDF uses its internal PDF/A backend,
  with no Ghostscript.
- **Installer:** cx_Freeze folder build (PSF licence, not the GPL PyInstaller) with Inno Setup and a
  per-user install. Only `tesseract.exe`, its DLLs and tur_best are bundled.
- **Non-ASCII Windows paths:** handled with ASCII-safe copies of the Tesseract data and temp folders.
- **Values:** stored under permanent variable keys, so renaming a variable keeps its values.

## Plan 5: the window (`evrakci-arayuz`)

Six tabs over the same core as the CLI, in the approved Kartotek look (`DESIGN.md`,
`docs/superpowers/mockups/kartotek/`):

- **Yükle:** jobs, batches (drag-drop or file dialog, reorder, remove), analysis with cancel.
- **Kontrol:** whole-job strip (one line per page, a rider per document to check), guide-tab
  timeline (QR left, filter centre, manual right), filters on a selection, cuts, rotate,
  delete, merge, undo/redo, N / Shift+N to the next check. Smooth at 1000 pages.
- **Şablonlar:** draw boxes on a mm grid, variants from other example documents, try order,
  file-name pattern, live "what do the boxes read".
- **Değerler:** review table, only-checks filter, accept suggestion (Enter), type (F2),
  draw a new variant (V), background reading where your corrections always win.
- **Dışa Aktar:** the same export as `is disa-aktar` (shared core `export_job`), retention.
- **Rehber:** the scanning guide and separator sheets to print.

Decisions: font is Segoe UI (Atkinson not approved); export and "corrections win" moved into
the core so CLI and window share them; batch add is an undoable edit; template edits have
their own undo. Full list of rulings: Plan 5 section of the final summary.

## 2026-11-13: UI overhaul (direction A, Fluent 2 Mica)

Owner picked direction A on the mockups; the look follows the approved PNGs in
`docs/ui-goal/mockups/final-a/png` exactly. Report with before/after images: `docs/ui-goal/REPORT.md`.

- **Phase 0-1:** decisions and HTML mockups of the six tabs. **Phase 2:** foundation (Inter font,
  Lucide icons, tokens, light/dark/high-contrast themes, motion with reduced motion, central action
  and shortcut registry, command palette, shortcut sheet, settings, toasts, taskbar, zoom, loupe)
  and the window chrome (tabs in the title band). **Phase 3:** all six tabs rebuilt to A, one undo
  history, context menus, zoom on every view. **Phase 4:** review fixes. **Phase 5:** README
  screenshots, this entry, the report.
- **Tests:** 1091 passed, 6 skipped; `ruff check .` clean. Screenshot matrix: 72 shots, `0 kırpılma/taşma`.
- **Top 25 QoL items:** 24 shipped, 1 deferred (item 25: first-run tour and completion sound).
  Details: `docs/ui-goal/top25.md`.
- **Open:** PROPOSALS items 1, 2, 4, 5 and the phase notes (P4-1 to P4-13, S/K/Y/E/D lists) in
  `docs/ui-goal/mockups/final-a/PROPOSALS.md` wait for the owner. Tabs at 150 % text: owner chose
  option b (overflow menu), built and tested.
  Approved for a later update: Şablonlar "show only the selected variable's boxes" (H) and
  "delete the selected box" (Del). Not tried with a real screen reader or on a real Windows machine.

### Test stability note (2026-11-13)

- **Settings leak, fixed in `f46c409`.** UI tests wrote into the real `~/.config/Evrakçı/Evrakçı.ini`, so a second full run inherited the first run's column widths, geometry and last tab and failed in bulk. `tests/conftest.py` now gives every test its own settings file.
- **Runs since then.** Four consecutive full runs passed: 1082 passed, 6 skipped, about 6 minutes each. They included a run stopping at the first failure, a run under deliberate CPU load, and two runs back to back.
- **PDFium threading, fixed.** The remaining bulk failures came from PDFium being used from several threads at once: window thumbnail workers and the main-thread analysis could clash. One clash left PDFium broken ("Data format error"), and every later PDF open in that process failed.
  - `pipeline/pdfium_lock.py` now puts every PDFium call (`render.py`, `analyze.py`, `ui/yukle_info.py`) under one process-wide lock. This is a minimal core hook under D13, tested in `tests/test_pdfium_lock.py`.
  - After the fix, three consecutive full runs passed: 1093 passed, 6 skipped.
  - **Known risk, not locked:** OCRmyPDF uses PDFium in its own threads during export. It is not under the lock, because locking it would stall thumbnails for the whole export.

### Builds on CI (2026-11-13)

- **Windows installer:** green at `e1e3276`, [run 43505690241](https://github.com/ZackHaronOriginal/Evrakci/actions/runs/43505690241).
  - The tests passed on Windows and the artifact `Evrakci-Kurulum` (63 MB) was built.
  - Earlier runs on this branch had stopped at their test step on three Windows-only failures. Fixed in `2fc5cb7` and `e1e3276`:
    - a PySide str→QChar quirk in the Turkish-glyph test;
    - the Değerler template picker 1 px short at 150 %;
    - a `/` vs `\` path compare.
- **Linux build:** green at the same commit, [run 43505690497](https://github.com/ZackHaronOriginal/Evrakci/actions/runs/43505690497).
- **Not done:** the installer has not been installed and clicked through on a real Windows desktop. That step needs a person.

### PDFium race confirmed (2026-11-14)

- **Without the lock:** 400 mixed render/analyse jobs on 8 threads gave 129 PDFium errors ("Sayfa 1 okunamadı"). After that, a fresh `render_page` on a valid PDF failed with "Failed to load page". These are the same symptoms as the earlier bulk test failures.
- **With `PDFIUM_LOCK`:** 0 errors, and later opens work.
- **Cause:** confirmed as unsynchronised PDFium use from several threads. The real settings-file leak (`tests/conftest.py`) was a separate issue, and both are fixed.
