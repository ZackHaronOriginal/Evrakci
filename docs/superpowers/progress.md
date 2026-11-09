# Progress: Plans 1–6

Last checked 2026-11-09: **383 tests pass**, `ruff check .` is clean.

| Plan | State | Review fixes (commit) |
|---|---|---|
| 1 Core, CLI, splitting | done | — |
| 2a OCR engine test | done; owner picked Tesseract + tur_best | report `docs/ocr-motor-karsilastirma.md` |
| 2b OCR text layer | done | "fix: address OCR text layer review findings" |
| 3 Templates | done | "fix: address template review findings" |
| 4 Review and export | done | "fix: address review and export review findings" |
| 5 Window | done; Kartotek look approved 2026-11-07 | "fix: address the window review findings" |
| 6 Windows installer | done; GitHub Actions build is green | "fix: address Windows installer review findings" |
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
