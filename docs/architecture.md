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
| `render.py` | Renders a job page at 300 dpi as displayed; converts millimetre boxes to pixels |
| `templates/model.py` | Templates: user-named variables, sections (page + mm box), file-name pattern, threshold |
| `templates/store.py` | One UTF-8 JSON file per template; import/export |
| `templates/read.py` | Reads a document's variables: variants in the user's order, first confident wins, otherwise flagged with every reading kept |
| `review.py` | Fixing values: the user's corrections win over later readings |
| `naming.py` | Safe Windows file names from patterns; clash numbering |
| `export.py` | Export plan: each document's name, values and "needs check" reasons |
| `index.py` | `index.xlsx` (every cell as text, so OCR'd `=…` never becomes a formula) |
| `settings.py` | App settings (retention) in `<app data>/settings.json` |
| `ocr/engine.py` | The OCR engine interface (`read_page`, `read_region`) |
| `ocr/tesseract.py` | Tesseract engine; the three official Turkish data files with pinned checksums; `default_engine()` (tur_best when installed) |
| `ocr/rapid.py`, `ocr/models.py` | RapidOCR engine (optional extra) with checksum-verified models |
| `ocr/textlayer.py` | Searchable text layer via OCRmyPDF, PDF/A-2b with the internal backend, plain-PDF fallback |
| `ocr/synthetic.py`, `ocr/metrics.py`, `ocr/compare.py`, `ocr/preprocess.py` | The engine comparison (`evrakci ocr-karsilastir`) |

Coming next (see the roadmap in `docs/superpowers/plans/`): the window and the installer.

## Splitting rules

- QR pages cut, and never reach the output.
- Filters apply only to the pages the user selected. "Every N pages is one document" restarts
  counting after any cut. The last-applied filter wins on overlaps.
- Everything between two cuts with no filter is one document.
- Blank pages **never** cut. A per-job switch can leave empty pages out of the output.

## Storage

```
<app data>/Evrakci/jobs/<job id>/job.json          job state (format version 2; version 1 still loads)
<app data>/Evrakci/templates/<template id>.json    one template
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
| OCR | Tesseract with the official `tur_best` data (owner's pick after the engine test); OCRmyPDF for the text layer and PDF/A-2b without Ghostscript |
| Packaging | Folder build + Windows installer, so Qt stays replaceable (LGPL) |

## Data handling

- Job data lives in the user's app-data folder, never inside the repository.
- Tests and demos use synthetic documents only (`tests/fakes.py`).
