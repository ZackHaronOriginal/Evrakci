# Plan 2 summary: OCR

- **Works:** searchable Turkish text layer as PDF/A-2b (OCRmyPDF internal backend, no Ghostscript),
  plain-PDF fallback recorded in the file's check reasons; engine comparison on synthetic pages.
- **CLI:** `evrakci ocr`, `evrakci ocr-karsilastir`, `evrakci ocr-modelleri-indir`.
- **Decisions:** Tesseract + `tur_best` (owner's pick after `docs/ocr-motor-karsilastirma.md`:
  94.7 % exact fields vs 51.6 % for RapidOCR, which misreads ı/İ). Official data SHA-256 pinned;
  ASCII-safe copies for non-ASCII Windows paths (per user).
- **Reviews:** `7935107`, `90557b7`; fresh review 2026-11-08 → `fab4c0e` (8 new tests).
- **Second fresh review (2026-11-09, report in the session):** 18 findings, all fixed in `1b7d1e1`
  (`tests/test_ocr_review2.py`, 26 tests): private per-user ASCII folders and per-run temp
  folders on Windows (scans never readable by other users), copies used only when every file
  verifies, `default_engine()` never raises, no console windows, timeouts, Ghostscript never
  run (pypdfium rasterizer, no optimizer), `mode="redo"` for scanners' own text, Tesseract 4
  layouts, cut-off downloads, page-by-page comparison, Turkish font message.
