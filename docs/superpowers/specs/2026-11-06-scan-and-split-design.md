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

Evrakçı is planned as a **toolbox** of quality-of-life features for chamber paperwork. This
document covers only the **first module**. Later modules (Section 9) must be possible without
rewriting this one.

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
   - **range rules** ("every N pages is one document")
3. Drop empty duplex backs automatically.
4. A **timeline editor** ("a video editor for mass PDFs") where staff see every page, apply rules
   and document types to ranges, and fix cuts by hand.
5. OCR every output page, so the PDFs are searchable and text can be copied.
6. Assign a **document type** to ranges ("this range is all seçim yetki belgesi"). Use that type's
   template or text rules to find fields and **name the files**.
7. Review and fix the found fields before export.
8. Export the PDFs to a folder the user picks, plus `index.xlsx`.
9. Let a chamber **add its own document types** without code changes and without training any model.

### Non-goals (not in this module)

- Makbuz and fatura handling, and scans from the flatbed glass (small slips cannot go through the
  feeder).
- Re-attaching separately scanned items to the documents they belong to.
- General PDF editing tools (beyond the split editor's own page operations in Section 5).
- Automatically classifying a mixed pile with no type given (see Section 6.4).
- Local AI models for field extraction (planned later, Section 9).
- Cloud processing, hosted version, multi-user or network features.

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
- Duplex scanning is expected. Empty backs are detected (near-blank page) and **dropped**.
  A blank page **never** means "new document". Separating is only done by QR pages and rules.
  Staff can restore a dropped page in the editor.

### 4.2 QR separator pages

- A QR separator page is a printed A4 sheet with a QR code and a short Turkish label
  ("AYIRAÇ – bu sayfa çıktıya girmez").
- It **only marks a cut**. It carries no document type or other data. It is placed **before and
  after** a document that needs fencing off, for example a 5-page record inside a run of 2-page
  records.
- The app can print separator sheets. They are reusable: staff pull them out after scanning and
  use them again.
- Separator pages are detected automatically, turned into cuts, and removed from the output.
- On a duplex scan the separator's back is blank and gets dropped like any other blank back.
  (The builder may instead print the QR on both sides.)

### 4.3 Range rules

- Staff select a range of pages on the timeline and apply a rule: **"every N pages is one
  document"**.
- Rules never cross a QR cut. A QR cut always ends one document and starts the next. A range
  rule restarts its counting after each cut.
- If the pages inside a ranged section don't divide evenly by N, the leftover pages become a
  short last document and are **flagged** in review.

### 4.4 Default

Wherever no rule is applied, **each stretch between two QR cuts (or the start or end of the job)
is one document.** So a pile fenced entirely with QR pages needs no rules at all.

### 4.5 Manual fixes

On the timeline, staff can add, move and remove any cut, by mouse and keyboard.

### 4.6 How rules, cuts and types interact (my call)

- Rules and type ranges are anchored to **page identities**, not page positions. Deleting,
  restoring or reordering pages never silently shifts them onto other pages.
- **Any cut restarts counting**, whether it is a QR cut or a manual one. Example: in an "every 2"
  run, a 3-page record with no QR around it gets a manual cut after its 3rd page, and everything
  after that stays in step. A manual cut works like a QR page added after scanning.
- When rules or types overlap, **the most recently applied one wins** on the overlapping pages.
- A document that ends up spanning two typed ranges takes the type of its **first page** and is
  flagged in review.
- After any edit, the cut list is rebuilt from: QR cuts, then manual cuts, then rules, then the
  default. That rebuild is what undo/redo and auto-save store.

### 4.7 What N counts (my call)

- By default, "every N pages" counts **kept pages** (after blank backs are dropped), because that
  is how staff think about it.
- A rule can switch to counting **sheets** (front and back), which is sturdier when a back
  with a stamp or show-through is not detected as blank.
- Any back that was kept but has very little ink is flagged on the timeline, so a slipped blank
  is easy to spot.

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
- Basic page operations: rotate a page, delete a page, restore a dropped blank.
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
- **PDF/A (my call):** the default output is a plain searchable PDF. PDF/A is an optional setting,
  available only when Ghostscript is installed. This keeps a Ghostscript-free commercial build
  possible (see dependency-licenses.md).

### 6.2 Document types (chamber-defined, no training)

A document type is **data, not code**. A chamber adds or edits types in the app, and they are
stored in the chamber's config folder. Each type has:

- a name, for example "Seçim Yetki Belgesi"
- **fields**, for example sicil no, ticaret sicil no, company type, company name, date. Each field
  is found by **one or both** of:
  - **Template:** a box drawn on a sample page ("the company name is here"). Best for the
    chamber's own forms, which have a fixed layout.
  - **Text rule:** a label to look for plus what follows it ("the number after 'Sicil No:'"),
    with ready-made patterns for common things (sicil no, VKN, TCKN, dates, amounts). Best for
    outside documents with varying layouts. Staff choose from patterns; they never write regex.
- for each field, whether it is **required for naming**
- a **file-name pattern**, for example `{sicil_no}_{sirket_turu}_{unvan}`
- (optional) **keywords** that identify the type, for later use (Section 6.4).

The app ships with a few example types, including seçim yetki belgesi, built from synthetic
samples.

### 6.3 Assigning types

Staff assign a type to a range on the timeline, the same way they apply a range rule. Every
document in that range uses that type's fields and naming. A document with no type gets only
OCR and a numbered fallback name.

### 6.4 Guessing types (deferred)

Automatic type detection for documents with no type assigned is **not in this module**. The
keyword field on types keeps that option open.

### 6.5 Naming and review

- Each found field records a confidence value. Missing or low-confidence fields are highlighted
  in a review table: one row per document, with a click-through to the page.
- File names are built from the pattern. Characters that are illegal in Windows file names are
  removed, and Turkish letters are kept. If two documents would get the same name, a number is
  added.
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

On OCR customization, the owner chose **chamber-defined document types (templates plus text rules),
not training an OCR model**. Local AI extraction was left as an optional later extra.

## 9. Later modules (context only, not designed here)

These are listed so the first module doesn't block them:

- Makbuz and fatura handling, including flatbed scans of small slips, and re-attaching them to
  their documents.
- A wider PDF editing toolkit.
- Automatic type detection for mixed piles.
- Optional local AI (for example PaddleOCR-VL) to fill fields that rules and templates miss, on
  PCs strong enough to run it.
- More quality-of-life features the owner will bring.

## 10. Decided vs. left to the builder

**Decided by the owner:**
- desktop app (A)
- QR pages as cut marks only, used before and after fenced documents
- QR pages and range rules are equally important
- each stretch between QR cuts is one document by default
- range-based type assignment
- naming from page data such as sicil no, company type and company name
- PaddleOCR gets evaluated against Tesseract
- chambers define their own document types; no training
- makbuz, fatura and flatbed scans are out of scope for now

**My calls (owner can correct):**
- blank pages are only dropped, never used as cuts
- leftover pages from a range rule are flagged
- an `index.xlsx` is included
- no automatic type guessing in this module
- staff pick from ready-made patterns instead of writing regex
- Turkish letters are kept in file names
- auto-save and resume of jobs, with several saved jobs
- how rules, cuts and types interact (4.6) and what N counts (4.7)
- the owner picks the OCR engine after the spike, and other work goes ahead on Tesseract until then
- plain PDF by default, with PDF/A optional

**Left to the builder:**
- QR payload format and decoding library (license-checked)
- blank-page threshold
- job storage format
- thumbnail caching
- threading model
- the exact OCR engine interface
- template-box coordinate handling
- installer tooling
- the order of milestones inside this module (suggested: split engine → timeline editor → OCR
  spike and engine → document types and naming → review and export → installer)

Also rewrite the README and `docs/architecture.md` to match this design. They currently lead with
makbuz and fatura.
