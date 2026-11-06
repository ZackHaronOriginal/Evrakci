# Evrakçı, first module: Tara ve Ayır (scan and split). Design

Date: 2026-11-06
Status: draft for approval

## 1. Intent and the why

Chamber of commerce staff regularly have to turn big paper piles into one PDF per document.
Examples: 400–800 *seçim yetki belgesi* company files, or a mixed pile of member documents.
Today that means unstapling, then scanning **one document at a time**, then switching to the next.
It is slow and tedious. Nobody names the resulting files, because naming 800 files by hand is pointless.

Evrakçı should let staff unstaple once, feed the pile through the copier's **document feeder (ADF)**
in a few big batches, and do all the splitting, naming and checking on the computer.

Evrakçı is planned as an **all-round quality-of-life toolbox** for chamber paperwork, not a fix for
one problem. This document covers only the **first module**. Everything in it is built to be
**configurable, not hardcoded for any one document**. Its building blocks (jobs, the page
timeline, the template and variable system, the OCR engine) are meant to be reused by later
modules (Section 9).

### Who uses it

Chamber office staff on ordinary Windows office PCs. They are not technical. They know the copier
and Windows, and nothing about OCR or Python.

### What success looks like

- One job takes a 100–800+ page pile, scanned as several feeder batches, and produces one correctly
  split PDF per document. Each PDF is named from data on the page (for example sicil no, company
  type and company name). A spreadsheet lists them all.
- The person only steps in to set up the rules for the job and fix mistakes.
- It is clearly faster than scanning document by document.

## 2. Goals, non-goals, anti-goals

### Goals (first module)

1. Combine several scanned PDFs (feeder batches) into one job, in order.
2. Split the job into documents using **two equally important tools** that can be mixed freely in
   one job (Section 4):
   - **QR separator pages**
   - **range rules**: filters applied to a selected stretch of pages, such as "every N pages is
     one document"
3. Optionally drop empty pages (a per-job switch; see 4.1).
4. A **timeline editor** ("a video editor for mass PDFs") where staff see every page, apply rules
   and document types to ranges, and fix cuts by hand.
5. OCR every output page, so the PDFs are searchable and text can be copied.
6. Assign a **document type** (a template) to ranges, for example "this range is all seçim yetki
   belgesi". Use that template's variables to read fields and **name the files**.
7. Review and fix the found fields before export.
8. Export the PDFs to a folder the user picks, plus `index.xlsx`.
9. A **template creator**: staff open a sample document, create variables such as
   `{Firma_Unvani}` and mark where each one is on the page. No code changes and no model
   training.

### Non-goals (not in this module)

- Makbuz and fatura handling, and scans from the flatbed glass (small slips cannot go through the
  feeder).
- Re-attaching separately scanned items to the documents they belong to.
- General PDF editing tools (beyond the split editor's own page operations in Section 5).
- Automatically classifying a mixed pile with no type given (see Section 6.4).
- Local AI models for field extraction (planned later, Section 9).
- Cloud processing, hosted version, multi-user or network features. Sharing templates over the
  network is planned for later; for now templates are moved between PCs by export and import.

### Anti-goals (failure even if it "works")

- **More paper handling for staff** than today. For example, requiring a separator before every
  document, or any special paper or printer.
- **Documents leaving the machine.** No network calls with document content, ever (KVKK).
- **Silently wrong output.** A wrong or missing field must be visible in review, never quietly
  baked into a file name.
- Staff needing to understand OCR, regex or Python to do a normal job.
- The window freezing during long work.

## 3. Constraints

- **Platform:** Python 3.11+, PySide6 (Qt) desktop app, as already started in this repo. Windows
  first; Linux and macOS should keep working.
- **Hardware:** ordinary office PCs, CPU only, no GPU assumed. A job of about 800 pages must finish
  in reasonable time; a target is set by the OCR spike (Section 6.1).
- **Offline:** everything runs locally.
- **Licensing:** the app is AGPL-3.0-or-later, with commercial licensing possible via the CLA.
  Every dependency must pass [dependency-licenses.md](../../dependency-licenses.md) (no PyQt,
  no PyMuPDF).
- **Language:** the UI and user docs are in Turkish. Code and code comments are in English.
- **Data:** the repo is public, so tests and demos use only synthetic documents. Job data lives
  in the user's app-data folder, never in the repo.
- **Architecture rule:** the processing pipeline (`src/evrakci/pipeline/`) never imports Qt.
- **Install:** a normal Windows installer, built as a folder build (not one static binary), so Qt
  stays replaceable as the LGPL requires.

## 4. Splitting

The same pile can need different splitting from job to job. Sometimes QR pages do most of the
work, sometimes range rules do. Both tools are first-class.

### 4.1 Scanning model

- Staff unstaple the pile and feed it in batches; an office copier feeder takes a few dozen
  sheets at a time.
- Each batch becomes one PDF. A job is an ordered list of batch PDFs. Staff can add, remove and
  reorder batches.
- **Blank pages are never used to split.** Only QR pages, range rules and manual cuts split.
- When a pile is scanned double-sided, one-sided pages produce empty backs. A per-job switch,
  "Boş sayfaları at" (drop empty pages), removes them from the output. Removed pages stay
  visible, greyed out on the timeline, and can be put back with one click. It is off by default,
  which suits single-sided scans.

### 4.2 QR separator pages

- A QR separator page is a printed A4 sheet with a QR code and a short Turkish label
  ("AYIRAÇ – bu sayfa çıktıya girmez").
- It **only marks a cut**. It carries no document type or other data. It is placed **before and
  after** a document that needs fencing off, for example a 5-page record inside a run of 2-page
  records.
- The app can print separator sheets. They are reusable: staff pull them out after scanning and
  use them again.
- Separator pages are detected automatically, turned into cuts, and removed from the output.
- The QR code is printed on **both sides** of the separator sheet, so it works the same in single-
  and double-sided scans, and its back never shows up as a stray page.

### 4.3 Range rules (filters on a selection)

- Nothing is applied automatically. Staff **select** a stretch of pages on the timeline and apply
  a filter to it, like applying an effect to a clip in a video editor. The first filter is
  **"every N pages is one document"**. More filters can be added later, such as "each page is its
  own document" (which is N = 1) or "the first page is separate".
- Rules never cross a QR cut. A QR cut always ends one document and starts the next. A range
  rule restarts its counting after each cut.
- If the pages inside a ranged section don't divide evenly by N, the leftover pages become a
  short last document and are **flagged** in review.

### 4.4 Pages with no filter

Wherever no filter is applied, **each stretch between two QR cuts (or the start or end of the job)
is one document.** So a pile fenced entirely with QR pages needs no rules at all.

### 4.5 Manual fixes

On the timeline, staff can add, move and remove any cut, by mouse and keyboard.

### 4.6 How rules, cuts and types interact (my call)

- Rules and type ranges are anchored to **page identities**, not page positions. Deleting,
  restoring or reordering pages never silently shifts them onto other pages.
- A manual cut works like a QR page added after scanning. Inside a selection that has an "every N
  pages" filter, the filter starts counting again after any cut.
- When rules or types overlap, **the most recently applied one wins** on the overlapping pages.
- A document that ends up spanning two typed ranges takes the type of its **first page** and is
  flagged in review.
- After any edit, the cut list is rebuilt from: QR cuts, then manual cuts, then rules, then the
  default. That rebuild is what undo/redo and auto-save store.

## 5. The timeline editor (Kontrol screen)

A horizontally or vertically scrolling strip of page thumbnails for the whole job, like a video
editor's timeline:

```
[QR]─┬─ every 2 pages ──────────────┬─[QR]─ 5-page doc ─[QR]─┬─ every 2 ─ ...
     │ p1 p2 │ p3 p4 │ p5 p6 │ ...  │      p41 … p45         │ p47 p48 │
         seçim yetki belgesi                    (type)            ...
```

- Cuts are clearly visible. Documents are shown as alternating bands. QR cuts, rule cuts and
  manual cuts look different from each other.
- The user selects a range by dragging, then applies a rule and/or a document type.
- Basic page operations: rotate a page, delete a page, put back a dropped empty page.
- A large view of the selected page.
- **Undo/redo** for every edit.
- It must stay smooth with **800+ pages**: thumbnails are rendered lazily, and nothing blocks the
  window.
- The job is saved automatically. Closing the app and reopening it resumes the job where it was.
- **Several jobs can be saved (my call):** a simple job list on the Yükle screen, so a big pile can
  be paused while a small urgent job runs.

The exact look is open, and mockups will be reviewed with the owner before building the UI.

## 6. OCR, document types and naming

### 6.1 OCR engine

- **Tesseract** (Turkish `tur` data) through OCRmyPDF is the baseline. The owner has used it
  before.
- **Baidu's PaddleOCR** (PP-OCRv5, and possibly PaddleOCR-VL) is a candidate. Before committing to
  an engine, a **spike** compares the two on synthetic Turkish documents (and, locally only, on a
  few real ones the owner supplies) on four things:
  - Turkish accuracy (ç ğ ı İ ö ş ü, numbers)
  - speed on CPU
  - install size and complexity on Windows
  - license
- The pipeline talks to OCR through a small engine interface, so the engine can be swapped
  without touching the rest.
- Output: every exported PDF gets a text layer, so it is searchable and text can be copied.
- **Engine choice (my call):** the spike ends with a short comparison report, and **the owner picks
  the engine**. Until then, the other work goes ahead on Tesseract behind the engine interface, so
  nothing waits on the spike. Working target: 800 pages OCR'd in under about 30 minutes on a
  typical office PC, with progress shown and cancel available.
- **PDF/A without Ghostscript:** OCRmyPDF 17.13+ can produce PDF/A-1b/2b/3b on its own, using
  `--pdfa-backend internal` and `pikepdf[pdfa]` (MPL-2.0), and validates the result itself.
  Ghostscript (AGPL) is therefore **not bundled and never called**.
  - Default output: **PDF/A-2b**.
  - If a file fails PDF/A validation, the app saves it as a plain searchable PDF and marks this
    in the index. It never silently falls back to Ghostscript.
  - Not available without Ghostscript: CMYK or grey colour conversion, and PDF/A image
    re-compression. Neither is needed here.
  - Source: OCRmyPDF v17.13.0 release notes. To be confirmed in the OCR spike.

### 6.2 Templates and variables (chamber-made, no training)

Nothing about any specific document is written into the code. Page counts, field positions and
which fields matter all come from **templates that staff create in the app**.

**Template creator:**

1. Open a sample document (scanned like the real ones).
2. Create **variables**, such as `{Firma_Unvani}`, `{Sicil_No}`, `{Sirket_Turu}` or `{Tarih}`.
   Any name the chamber wants.
3. For each variable, **select its place** on the page by drawing a box. The variable records the
   page (first page, page 2, last page, etc.) and the box.
4. Set options per variable:
   - **Value shape** (optional): pick from ready-made shapes such as text, number, sicil no, VKN,
     TCKN, date or amount, which clean and check what is read. Staff never write regex.
   - **Lines:** usually one line, but a long value (such as a long company name) can run onto 2–3
     lines. The variable can allow growing downward to take in the continuation lines.
   - **Search area when unsure or failed:** if the box reads nothing, or the result doesn't match
     the value shape or has low confidence, the app searches a **wider area around the box**. As
     another option, it can look for a **label** ("Sicil No:") anywhere on the page and read what
     follows it. This handles scans that are slightly shifted, and outside documents whose layout
     varies.
   - **Required or optional** for naming, set by staff.
5. Set the **file-name pattern** from the variables, for example
   `{Sicil_No}_{Sirket_Turu}_{Firma_Unvani}`.
6. **Test** the template on the sample, or on a few pages of the current job, and see what each
   variable reads before saving.

**Storage:** templates are stored on the PC, with **export and import** (a single file) to copy
them to other PCs. Sharing over a network folder comes later.

The app ships with a demo template built from a synthetic sample, only to show how templates
work.

### 6.3 Assigning types

Staff assign a template to a selection on the timeline, the same way they apply a range rule.
Every document in that selection uses that template's variables and naming. A document with no type gets only
OCR and a numbered fallback name.

### 6.4 Guessing types (deferred)

Automatic type detection for documents with no type assigned is **not in this module**. The
data model should leave room for it (for example, an optional list of keywords per template).

### 6.5 Naming and review

- Each found field records a confidence value. Missing or low-confidence fields are highlighted
  in a review table: one row per document, with a click-through to the page.
- File names are built from the pattern. Characters that are illegal in Windows file names are
  removed, and Turkish letters are kept. If two documents would get the same name, a number is
  added.
- Staff can edit any value in the review table.
- A document with a missing required field cannot be exported silently. It gets a fallback name
  and is marked in the index.

## 7. Export

- One PDF per document, with a text layer, written to a folder the user picks.
- `index.xlsx` with one row per document: file name, page count, source pages, document type,
  every field, and a "needs check" flag.
- After a successful export, the app may delete the job's files, depending on a retention setting.

## 8. Approaches considered

| | Approach | Trade-off | Decision |
|---|---|---|---|
| A | **Python + PySide6 (Qt) desktop app** | Already started, one language, OCR libraries are Python, and Qt handles big thumbnail views. A polished modern look takes more effort | **Chosen by the owner** |
| B | Local web app (Python backend, browser UI) | Rich editor UIs are easier, and it could become a hosted version later. But two languages and a clumsy "opens in browser" install | Rejected |
| C | Tauri/Electron shell plus a Python sidecar | Feels native with a web UI, but it is the most complex to build, package and debug with OCR models | Rejected |

On OCR customization, the owner chose **a template creator with variables placed on a sample
page, plus label search and a wider search area as fallbacks**, instead of training an OCR model. Local AI extraction was left as an optional later extra.

## 9. Later modules (context only, not designed here)

Evrakçı is an all-round QOL toolbox. These are listed so the first module doesn't block them:

- Makbuz and fatura handling, including flatbed scans of small slips, and re-attaching them to
  their documents.
- A wider PDF editing toolkit.
- Sharing templates between PCs over the network.
- Automatic type detection for mixed piles.
- Optional local AI (for example PaddleOCR-VL) to fill fields that rules and templates miss, on
  PCs strong enough to run it.
- More quality-of-life features the owner will bring.

## 10. Decided vs. left to the builder

**Decided by the owner:**
- desktop app (A)
- QR pages as cut marks only, used before and after fenced documents
- QR pages and range rules are equally important, and their mix varies by job
- range rules are filters applied to a selection; nothing is applied by default
- each stretch between QR cuts is one document unless a filter says otherwise
- range-based type assignment
- everything is configurable: a template creator with variables, drawn boxes, multi-line values
  and a wider search when unsure or failed; required fields set per variable
- templates stay on each PC for now, with export and import; network sharing comes later
- naming from page data such as sicil no, company type and company name
- PaddleOCR gets evaluated against Tesseract
- chambers make their own templates; no training
- makbuz, fatura and flatbed scans are out of scope for now

**My calls (owner can correct):**
- dropping empty pages is an optional per-job switch, never used for splitting; QR printed on both sides
- leftover pages from a range rule are flagged
- an `index.xlsx` is included
- no automatic type guessing in this module
- staff pick from ready-made value shapes instead of writing regex; label search as a fallback
- Turkish letters are kept in file names
- auto-save and resume of jobs, with several saved jobs
- how rules, cuts and types interact (4.6)
- the owner picks the OCR engine after the spike, and other work goes ahead on Tesseract until then
- PDF/A-2b by default through OCRmyPDF's internal backend (no Ghostscript), with a plain PDF if validation fails

**Left to the builder:**
- QR payload format and decoding library (license-checked)
- empty-page threshold
- job storage format
- thumbnail caching
- threading model
- the exact OCR engine interface
- template-box coordinate handling
- installer tooling
- the order of milestones inside this module (suggested: split engine → timeline editor → OCR
  spike and engine → template creator and naming → review and export → installer)

Also rewrite the README and `docs/architecture.md` to match this design. They currently lead with
makbuz and fatura.
