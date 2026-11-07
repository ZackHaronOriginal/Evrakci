# Progress: Plans 1–6

Last checked 2026-11-07: **231 tests pass**, `ruff check .` is clean.

| Plan | State | Review fixes (commit) |
|---|---|---|
| 1 Core, CLI, splitting | done | — |
| 2a OCR engine test | done; owner picked Tesseract + tur_best | report `docs/ocr-motor-karsilastirma.md` |
| 2b OCR text layer | done | "fix: address OCR text layer review findings" |
| 3 Templates | done | "fix: address template review findings" |
| 4 Review and export | done | "fix: address review and export review findings" |
| 5 Window | **stopped: waiting for the owner to choose a design** | — |
| 6 Windows installer | done; GitHub Actions build is green | "fix: address Windows installer review findings" |

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

## Plan 5 status

1. PRODUCT.md is written.
2. Five design directions are in `.impeccable/mocks/decision/`:
   - Kartotek
   - Hat Haritası
   - Terminal Sarısı
   - Pul Katalog
   - Windows standardı
3. The owner chose **Kartotek**; all six screens are in `docs/superpowers/mockups/kartotek/`.

After the owner picks a direction, all six screens are drawn in it for approval, and only then is
the window built.
