# Plan 2 summary: OCR

- **Works:** searchable Turkish text layer as PDF/A-2b (OCRmyPDF internal backend, no Ghostscript),
  plain-PDF fallback recorded in the file's check reasons; engine comparison on synthetic pages.
- **CLI:** `evrakci ocr`, `evrakci ocr-karsilastir`, `evrakci ocr-modelleri-indir`.
- **Decisions:** Tesseract + `tur_best` (owner's pick after `docs/ocr-motor-karsilastirma.md`:
  94.7 % exact fields vs 51.6 % for RapidOCR, which misreads ı/İ). Official data SHA-256 pinned;
  ASCII-safe copies for non-ASCII Windows paths (per user).
- **Reviews:** `7935107`, `90557b7`; fresh review 2026-11-08 → `fab4c0e` (8 new tests).
