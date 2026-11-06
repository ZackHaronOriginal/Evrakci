# Architecture

The full design is in
[superpowers/specs/2026-11-06-scan-and-split-design.md](superpowers/specs/2026-11-06-scan-and-split-design.md).
This page is a short map of the code.

## Deployment model

Evrakçı is a **desktop application** installed on the chamber's own computers (Windows first).
No document data leaves the machine, which is the main KVKK (Turkish data protection law)
argument and a core product promise.

## One core, two entry points

```
              ┌──────────────────────┐      ┌───────────────────────────┐
              │ evrakci (CLI)        │      │ evrakci-arayuz (window)   │
              │ src/evrakci/cli/     │      │ src/evrakci/ui/  PySide6  │
              └──────────┬───────────┘      └─────────────┬─────────────┘
                         └──────────────┬─────────────────┘
                                        ▼
                         core: src/evrakci/pipeline/  (never imports Qt)
```

- The **command line** is built first and can do everything.
- The **window** is a second entry point that calls the same core, so both always behave the same.

## Core modules (`src/evrakci/pipeline/`)

| Module | Role |
|---|---|
| `separator.py` | The printable QR separator sheet (QR on both sides) and its payload |
| `analyze.py` | Looks at each scanned page once: is it a QR page, how much ink does it have (`PageInfo`) |
| `job.py` | The `Job`: batches, page info and every user edit (filters, cuts, deletions, rotations). All edits are methods here |
| `cuts.py` | `compute_documents(job)`: turns a job into documents from QR pages, manual cuts and filters |
| `writer.py` | Writes one PDF per document |
| `store.py` | Jobs on disk |

Coming next (see the roadmap in `docs/superpowers/plans/`): OCR, templates and variables, review
and export (named PDFs, PDF/A-2b, `index.xlsx`), then the window.

## Splitting rules

- QR pages cut, and never reach the output.
- Filters apply only to the pages the user selected. "Every N pages is one document" restarts
  counting after any cut. The last-applied filter wins on overlaps.
- Everything between two cuts with no filter is one document.
- Blank pages **never** cut. A per-job switch can leave empty pages out of the output.

## Storage

```
<app data>/Evrakci/jobs/<job id>/job.json          job state (format version 1)
<app data>/Evrakci/jobs/<job id>/batches/b1.pdf    copy of each scanned batch
```

`job.json` is written to a temporary file and renamed, so a crash never leaves it half-written.
Pages are identified as `<batch id>/<index>`, so edits stay on their pages when batches are reordered.

## Technology

| Part | Tech |
|---|---|
| Window | PySide6 (Qt for Python, LGPL) |
| PDF | pikepdf (write), pypdfium2 (render) |
| QR | segno (make), zxing-cpp (read) |
| OCR | Tesseract or RapidOCR, chosen after the engine test; OCRmyPDF for the text layer and PDF/A without Ghostscript |
| Packaging | Folder build + Windows installer, so Qt stays replaceable (LGPL) |

## Data handling

- Job data lives in the user's app-data folder, never inside the repository.
- Tests and demos use synthetic documents only (`tests/fakes.py`).
