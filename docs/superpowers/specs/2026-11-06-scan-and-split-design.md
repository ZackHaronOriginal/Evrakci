# Evrakçı, first module: Tara ve Ayır (scan and split). Design

Date: 2026-11-06
Status: draft for owner approval

## Words used in this document

| Word | Meaning |
|---|---|
| **Job** | One pile of paper being processed: one or more scanned PDFs, worked on together |
| **Batch** | One scanned PDF from one run through the copier's document feeder |
| **Cut** | A point between two pages where one document ends and the next begins |
| **QR page** | A printed separator sheet with a QR code. Where it appears, the app makes a cut |
| **Filter** | Something the user applies to a **selected** stretch of pages to make cuts, for example "every N pages is one document" |
| **Template** | A user-made description of one kind of document: which **variables** to read, where they are, and how to name the file |
| **Variable** | A user-named value read from the page, written in curly braces, for example `{Firma_Unvani}`. The user picks every name |
| **Section** | A box drawn on an example document, saying where to read a variable |
| **Variant** | An extra section for the same variable, drawn on another example document of the same kind |

## 1. Why this exists

Chamber of commerce staff regularly have to turn big paper piles into one PDF per document.
Examples include 400–800 *seçim yetki belgesi* company files, or a mixed pile of member documents.
Today that means unstapling, then scanning **one document at a time**, then switching to the next.
It is slow and tedious. Nobody names the files, because naming 800 files by hand is pointless.

With Evrakçı, staff unstaple once and feed the pile through the copier's **document feeder** in a
few big batches. All splitting, naming and checking happens on the computer.

Evrakçı is planned as an **all-round quality-of-life toolbox** for paperwork, not a fix for one
problem. This document covers only the **first module**.

**Two principles for everything in it:**

- **Configurable, not hardcoded.** The code contains nothing specific to any document, field or
  chamber. Users create all of that themselves.
- **Reusable.** The building blocks (jobs, the page timeline, templates and variables, the OCR
  engine) are meant to be reused by later modules (Section 9).

### Who uses it

Office staff on ordinary Windows PCs. They are not technical. They know the copier and Windows,
and nothing about OCR or programming.

### What success looks like

- One job takes a 100–800+ page pile, scanned as several batches, and produces one correctly split
  PDF per document. Each PDF is named from values read off its pages, using the variables in the
  template the user chose. A spreadsheet lists every file.
- The user only selects pages, applies filters and templates, and fixes mistakes.
- It is clearly faster than scanning document by document.

## 2. Goals, non-goals, anti-goals

### Goals (first module)

1. Combine several batches into one job, in order.
2. Split the job into documents with **QR pages** and **filters**. Both are equally important, and
   each job uses whatever mix fits (Section 4).
3. A **timeline editor**, like a video editor for big PDFs. The user sees every page, selects
   stretches of pages, applies filters and templates, and adds, moves or removes cuts by hand
   (Section 5).
4. OCR every output page, so the PDFs are searchable and text can be copied.
5. A **template creator**. The user opens an example document, creates variables with any names
   they want, draws where each one is, and adds variants from other example documents
   (Section 6.2).
6. Apply a template to a selection ("these pages are all seçim yetki belgesi"). The app reads that
   template's variables from each document and **names the files**.
7. Review and fix the values read before export.
8. Export the PDFs to a folder the user picks, plus `index.xlsx`.

### Non-goals (not in this module)

- Makbuz and fatura handling, and scans from the flatbed glass (small slips cannot go through the
  feeder).
- Re-attaching separately scanned items to the documents they came from.
- General PDF editing tools, beyond the timeline's own page operations (Section 5).
- Guessing which template a document needs when the user hasn't said (Section 6.4).
- Local AI models for reading values (planned for later, Section 9).
- Cloud processing, a hosted version, multi-user or network features. For now, templates move
  between PCs by export and import; network sharing comes later.

### Anti-goals (failure even if it "works")

- **More paper handling than today.** For example, requiring a separator before every document,
  or any special paper or printer.
- **Documents leaving the machine.** No network calls with document content, ever (KVKK).
- **Silently wrong output.** A wrong or missing value must be visible in review, never quietly
  baked into a file name.
- **The app assuming what users need.** No built-in fields, field types or document kinds.
- Staff needing to understand OCR or programming to do a normal job.
- The window freezing during long work.

## 3. Constraints

- **Platform:** a Python 3.11+ desktop app using PySide6 (Qt), as already started in this repo.
  Windows comes first; Linux and macOS should keep working.
- **Hardware:** ordinary office PCs with only a CPU (no GPU assumed). About 800 pages must finish in
  reasonable time (target in Section 6.1).
- **Offline:** everything runs on the PC.
- **Licensing:** the app is AGPL-3.0-or-later, and commercial licensing is possible via the CLA.
  Every dependency must pass [dependency-licenses.md](../../dependency-licenses.md). That means no
  PyQt, no PyMuPDF and no Ghostscript.
- **Language:** the UI and user docs are in Turkish. Code and code comments are in English.
- **Data:** the repo is public, so tests and demos use only synthetic documents. Job data lives in
  the user's app-data folder, never in the repo.
- **Architecture:** the processing code (`src/evrakci/pipeline/`) never imports Qt.
- **Install:** a normal Windows installer. It is built as a folder, not one single file, so the Qt
  libraries stay replaceable as their LGPL license requires.

## 4. Splitting

How a pile is split varies from job to job. Sometimes QR pages do most of the work, sometimes
filters do. Both are first-class.

### 4.1 Scanning

- Staff unstaple the pile and feed it in batches; an office copier feeder takes a few dozen sheets
  at a time.
- A job is an ordered list of batches. Staff can add, remove and reorder batches.
- **Blank pages never cause a cut.** Only QR pages, filters and manual cuts split documents.
- With double-sided scanning, one-sided pages produce empty backs. A per-job switch,
  "Boş sayfaları at" (drop empty pages), leaves them out of the output.
  - It is off by default.
  - Dropped pages stay visible, greyed out on the timeline, and come back with one click.

### 4.2 QR pages

- A QR page is a printed A4 sheet with a QR code and a short Turkish note
  ("AYIRAÇ – bu sayfa çıktıya girmez").
- It **only marks a cut** and carries no other information.
- Staff put QR pages **before and after** a document that needs to be fenced off, for example a
  5-page record inside a run of 2-page records.
- The app prints QR pages. They are reusable: staff pull them out after scanning and use them
  again.
- The app finds QR pages automatically, makes a cut at each one, and leaves them out of the
  output.
- The QR code is printed on **both sides** of the sheet, so it works the same in single- and
  double-sided scans.

### 4.3 Filters

- **Nothing is applied automatically.** The user **selects** a stretch of pages on the timeline and
  applies a filter to it, like applying an effect to a clip in a video editor.
- The first filter is **"every N pages is one document"**, with N chosen by the user. More filters
  can be added later.
- A filter never counts across a cut. After any cut (QR or manual), counting starts again at 1.
- If the pages don't divide evenly by N, the leftover pages become a shorter last document, which
  is **flagged** in review.

### 4.4 Pages with no filter

Wherever no filter is applied, **everything between two cuts (or the start or end of the job) is
one document.** So a pile fenced entirely with QR pages needs no filters at all.

### 4.5 Manual cuts

On the timeline, the user can add, move and remove any cut with the mouse or keyboard. A manual
cut works exactly like a QR page that was added after scanning.

### 4.6 When filters, templates and cuts meet (my call)

- Filters and templates stay attached to the **pages** they were applied to, not to page
  positions. Deleting, restoring or reordering pages never shifts them onto other pages.
- If two filters, or two templates, are applied to overlapping pages, **the one applied last wins**
  on the overlap.
- If a document ends up covering pages with two different templates, it uses the template of its
  **first page**, and is flagged in review.
- After every edit, the app recalculates all cuts from QR pages, manual cuts and filters. Undo,
  redo and auto-save work on this.

## 5. Timeline editor (Kontrol screen)

A scrolling strip of page thumbnails for the whole job, like a video editor's timeline:

```
[QR]─┬─ filter: every 2 pages ──────┬─[QR]─ 5-page doc ─[QR]─┬─ every 2 ─ ...
     │ p1 p2 │ p3 p4 │ p5 p6 │ ...  │      p41 … p45         │ p47 p48 │
       template: Seçim Yetki Belgesi                             ...
```

- Cuts are clearly visible. Each document is shown as its own band. QR cuts, filter cuts and
  manual cuts look different from each other.
- The user selects pages by dragging, then applies a filter, a template, or both.
- Page operations: rotate a page, delete a page, and bring back a dropped empty page.
- A large view of the selected page.
- **Undo and redo** for every edit.
- It stays smooth with **800+ pages**: thumbnails load as they scroll into view, and slow work never
  freezes the window.
- Jobs save automatically. Closing and reopening the app picks up where the user left off.
- **Several jobs can be saved (my call):** a simple job list on the Yükle screen, so a big pile can
  be paused while a small urgent job runs.

The exact look is open. Mockups will be reviewed with the owner before the UI is built.

## 6. OCR, templates and naming

### 6.1 OCR engine

Research (November 2026, web only; key claims are re-checked in the test below):

- **Tesseract 5** (Turkish data `tur` / `tur_best`), used through OCRmyPDF, is the **baseline**.
  - It officially supports Turkish and is easy to install on Windows.
  - It gives word positions and a searchable PDF directly.
  - The owner has used it before.
- **RapidOCR** is the **main challenger**. It runs Baidu's PaddleOCR (PP-OCRv5) Latin-script models
  without Baidu's heavy framework.
  - Installs with pip only, and the models are about 90 MB.
  - CPU-friendly. Apache-2.0 license.
  - PaddleOCR scored strongest overall in the only Turkish benchmark found (OCRTurk, SIGTURK 2026).
    That benchmark did not test Tesseract.
  - Must be checked: whether its character set includes ı İ ş ğ ç ö ü.
- **Full PaddleOCR** runs the same models but with a much heavier install. It is only considered
  if it clearly beats RapidOCR.
- **PaddleOCR-VL**, a small AI model, doesn't give reliable word positions for reading inside a
  drawn box, and is likely far too slow on office CPUs. It moves to the "optional local AI later"
  idea (Section 9).
- **Ruled out:**
  - Surya: its model license blocks commercial use.
  - EasyOCR and docTR: they need PyTorch, are slow on CPU, and have no Turkish evidence.
  - MinerU: AGPL.
  - Large AI OCR models: too slow, and no word positions.

**Engine test (spike).** It compares Tesseract and RapidOCR, plus full PaddleOCR only if needed.

Test material:
- synthetic Turkish pages
- a few real pages the owner runs on their own PC (never committed)

What it measures:
- how often a value read **inside a drawn box** comes out exactly right, because that is what the
  app actually does
- the error rate on Turkish letters (ı/i, İ/I, ş, ğ, ç, ö, ü), separately from the overall error rate
- seconds per page on a typical office PC, measured on a 20-page batch
- install size and Windows setup effort
- whether the searchable text lines up with the page image

Tesseract is tested fairly, with the usual clean-up (straightening, black-and-white) and suitable
settings.

**Engine choice:**
- The test ends with a short report, and **the owner picks the engine**.
- Until then, other work continues on Tesseract.
- The rest of the code talks to OCR through one small interface, so the engine can be swapped
  later without changing anything else.

**Speed target:** about 800 pages in under about 30 minutes on a typical office PC, with a progress
bar and a cancel button.

**Output:** every exported PDF gets an invisible text layer, so it is searchable and text can be
copied.

**PDF/A without Ghostscript:**
- OCRmyPDF 17.13+ can produce PDF/A by itself (`--pdfa-backend internal`, using `pikepdf[pdfa]`,
  MPL-2.0) and checks its own result. Ghostscript (AGPL) is **not bundled and never called**.
- Default output: **PDF/A-2b**.
- If a file fails the PDF/A check, it is saved as a normal searchable PDF and marked in the index.
- What is lost without Ghostscript: CMYK or grey colour conversion and PDF/A image re-compression.
  Neither is needed here.
- Source: OCRmyPDF v17.13.0 release notes. To be confirmed in the engine test.

### 6.2 Templates (made by the user, no training)

**The app decides nothing about what a document contains.** It has no built-in fields, no field
types, no suggested variable names and no built-in document kinds. Users create all of it with the
template creator. The code only provides the tools.

**A template contains:**

- a **name**, chosen by the user
- **variables**, created and named by the user, written in curly braces, for example
  `{Firma_Unvani}` or `{Kayit_No}`. The user can add, rename and remove them at any time.
- for each variable, **one or more sections**: boxes drawn on example documents, saying "read this
  variable from here". Each section remembers which page it is on (first page, page 2, last page,
  and so on).
- a **file-name pattern** made from the variables, for example `{Kayit_No}_{Firma_Unvani}`
- for each variable, whether it is **required** for the file name, as the user decides

**Variants (several sections for one variable):**

- Documents of the same kind are not always laid out the same. A long value may take 2–3 lines
  instead of 1, or a value may sit higher or lower on some copies.
- So the user can give a variable **more than one section**. They open **another example document
  of the same kind**, draw the box where the value is on that one (different place, different
  height, and so on), and save it as a variant.
- When reading a document, the app tries the variants **in the order the user listed them**, and
  uses the first one that reads a confident result. If none does, the variable is flagged, and the
  reviewer sees what each variant read. (This order rule is my call.)
- The user can add a variant at any time, including from the review screen: when a document
  fails, they draw the right box on that document and save it as a new variant.

**Making a template, step by step:**

1. Open an example document.
2. Create a variable and name it.
3. Draw its box on the page.
4. Repeat for every variable needed.
5. Optionally open more example documents of the same kind and add variants.
6. Build the file-name pattern from the variables.
7. Test it on the examples or on some documents in the current job, see what each variable
   reads, then save.

**Storage:** templates are kept on the PC. Each template can be exported to one file and imported on
another PC. Sharing over a network folder comes later.

The app may ship **one demo template** made from a synthetic example document, only to show how
templates work. It is an example, not a built-in document kind.

### 6.3 Applying templates

The user applies a template to a selection on the timeline, the same way they apply a filter.
Every document in that selection is read with that template. A document with no template gets
only OCR and a numbered file name.

### 6.4 Guessing the template (later)

Guessing which template a document needs, when the user hasn't applied one, is **not in this
module**. The data format should leave room to add it later.

### 6.5 Review and naming

- A **review table** has one row per document and one column per variable. Each value shows how
  confident the OCR was. Missing or unsure values are highlighted, and clicking a row opens the
  page.
- The user can edit any value.
- File names come from the template's pattern:
  - Characters that Windows doesn't allow in file names are removed.
  - Turkish letters are kept.
  - If two files would get the same name, a number is added.
- If a required variable is missing, the document is **never exported silently** with a bad name.
  It gets a numbered name and is marked "needs check" in the index.

## 7. Export

- One PDF per document, with a text layer, saved to a folder the user picks.
- `index.xlsx`, with one row per document:
  - file name, page count and source pages
  - the template used
  - one column per variable
  - a "needs check" mark
- A retention setting can delete the job's working files after a successful export.

## 8. Approaches considered

| | Approach | Trade-off | Decision |
|---|---|---|---|
| A | **Python + PySide6 (Qt) desktop app** | Already started, one language, the OCR libraries are Python, and Qt handles large thumbnail views well. A polished modern look takes more effort | **Chosen by the owner** |
| B | Local web app (Python processing, browser screen) | Rich editor screens are easier to build, and it could become a hosted version later. But two languages, and a clumsy "opens in the browser" install | Rejected |
| C | Desktop shell (Tauri or Electron) around a web screen, with Python underneath | Feels like a normal app with a web screen, but it is the most complex to build, package and debug with OCR models | Rejected |

**Reading values from documents:** the owner chose **user-made templates**. These are named
variables, boxes drawn on example documents, and variants from other examples of the same kind.
The owner chose this instead of training an OCR model. Local AI is an optional idea for later.

## 9. Later modules (context only, not designed here)

Evrakçı is an all-round quality-of-life toolbox. These are listed so the first module doesn't
block them:

- makbuz and fatura handling, flatbed scans of small slips, and re-attaching them to their
  documents
- a wider PDF editing toolkit
- sharing templates between PCs over the network
- guessing the template for documents in a mixed pile
- optional local AI (for example PaddleOCR-VL) to read values that templates miss, on PCs strong
  enough to run it
- more quality-of-life features the owner will bring

## 10. Who decided what

**Decided by the owner:**
- Desktop app with Python and Qt (approach A).
- QR pages only mark cuts. Staff put them before and after documents that need fencing off.
- QR pages and filters are equally important, and the mix varies by job.
- Filters are only applied to what the user selects. Nothing is applied by default.
- Everything between two cuts is one document, unless a filter says otherwise.
- Templates are applied to a selection of pages.
- Everything is configurable. Users create templates with their own named variables, drawn
  sections, variants from other example documents, and their own choice of required variables.
  The app has no built-in fields or document kinds.
- Templates stay on each PC for now, with export and import. Network sharing comes later.
- PaddleOCR (as RapidOCR) is tested against Tesseract. The owner picks the engine.
- Makbuz, fatura and flatbed scans are out of scope for now.

**My calls (the owner can change these):**
- Dropping empty pages is an optional per-job switch, off by default. Empty pages never cause cuts.
- QR codes are printed on both sides of the separator sheet.
- After any cut, a filter starts counting again. Leftover pages are flagged.
- For overlaps, the last-applied filter or template wins. A document covering two templates uses
  its first page's template.
- Variants are tried in the user's order, and the first confident result wins.
- Turkish letters are kept in file names.
- Jobs save automatically, and several jobs can be saved.
- An `index.xlsx` comes with every export.
- No template guessing in this module.
- PDF/A-2b by default, without Ghostscript. A plain PDF is used if the PDF/A check fails.

**Left to the builder:**
- what the QR code contains, and which library reads it (license-checked)
- how "empty" a page must be to count as empty
- how jobs are stored on disk
- thumbnail caching
- how background work is run
- the exact OCR interface
- how drawn boxes are stored and matched to scanned pages
- installer tooling
- the order of work inside this module. Suggested order:
  1. splitting engine
  2. timeline editor
  3. OCR engine test and OCR
  4. template creator and naming
  5. review and export
  6. installer

Also: rewrite the README and `docs/architecture.md` to match this design. They currently lead with
makbuz and fatura.
