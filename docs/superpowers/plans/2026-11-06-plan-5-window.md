# Plan 5: The Window (`evrakci-arayuz`). Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Status: waiting for the owner's approval of the mockups**
> (`docs/superpowers/mockups/kartotek/*.png`, the Kartotek look the owner chose on 2026-11-07). Nothing in this plan is built before that approval.
> If the owner asks for changes, this plan is revised first.

**Goal:** A PySide6 window over the same core as the CLI, with these tabs:
- **Yükle:** jobs and batches
- **Kontrol:** the timeline editor, like a video editor
- **Şablonlar:** the template creator (draw boxes, add variants from other examples)
- **Değerler:** the review table
- **Dışa Aktar:** export
- **Rehber:** the scanning guide

It must stay smooth with 800+ pages, and undo/redo every edit.

**Architecture:**
- `src/evrakci/ui/` holds Qt code only. Every change goes through the same core functions the CLI
  uses: `Job` methods, `compute_documents`, `read_document`, `plan_export`, `write_documents`,
  `add_text_layer`, `write_index`, and the template store.
- **One controller per open job** (`JobController`):
  - owns the `Job`, the `JobStore` and a `QUndoStack`
  - every edit is a `QUndoCommand` that applies a core method and can reverse it, by saving and
    restoring `job_to_dict`
  - it auto-saves after each command
  - views listen to one signal, `job_changed`
- **Slow work runs in `QThreadPool` workers** with progress and cancel: page analysis, thumbnails,
  reading values, export and template tests. The window never blocks.
- **Thumbnails:** rendered at about 100 px height by a worker on request, kept in an LRU cache of
  about 400 entries, and only for pages scrolled into view.

**Tech Stack:** PySide6 (LGPL, already a dependency); pytest-qt (MIT, dev only) for UI tests with
`QT_QPA_PLATFORM=offscreen`.

**Spec:** §4–§7 and the approved mockups.

## Global Constraints

- `src/evrakci/pipeline/` stays free of Qt. All UI text is Turkish.
- **No logic duplicated from the core.** The UI only calls core functions.
- **Look:** follows `DESIGN.md` and the approved mockups (`docs/superpowers/mockups/kartotek/*.png`, the Kartotek look the owner chose on 2026-11-07).
  Colours and sizes come from one token table (`src/evrakci/ui/theme.py`), so looks can be made
  configurable later.
- Cut types look different, and the same everywhere (position and pictogram first, colour repeats it):
  - each document starts with a manila guide tab above its pages
  - QR cut: tab on the left with a QR pictogram, solid blue line
  - filter cut: tab in the centre with a funnel and a dashed orange edge and line
  - manual cut: tab on the right with scissors, solid red line
  - dropped empty page: dashed sheet labelled "boş"
- "Kontrol" is always an orange signal rider with a warning icon and text, never colour alone.
- The Kontrol screen has a whole-job strip above the timeline: one hairline per page, an orange
  rider per document that needs a check, and a bracket for the visible part (click to jump). The
  timeline heading names the first and last document in view ("Belge 40 — Belge 43").
- Every edit can be undone (Ctrl+Z / Ctrl+Y), and the job is saved after each edit.
- Shortcuts: Ctrl+1…5 tabs and F1 for Rehber; N / Shift+N next / previous kontrol; F filter, K cut, T template,
  B draw box, Enter accept suggestion, F2 type a value, V draw a new variant.
- Long work shows progress, can be cancelled, and never freezes the window.
- Colour contrast meets WCAG AA. Body text is 15 px and the smallest text is 13 px.

## Review Focus

1. **800+ pages:** the first paint stays under 1 s and scrolling never renders off-screen pages.
   Test: a 1000-page fake job; only visible thumbnails are requested.
2. **Undo after reload:** the undo stack is per session. Reopening a job starts with an empty
   stack, and the saved state is exactly what was on screen.
3. **Drawing boxes on rotated or non-A4 examples** gives correct millimetres in the page's
   displayed orientation, the same mapping as `render.mm_box_to_pixels`.
4. **Editing a value in the review table while a read is running.** The user's edit wins
   (`edited=True` is kept by `is oku`).
5. **Closing the window during export.** It asks first; on cancel the export stops cleanly and
   leaves the folder in the same state the CLI would.

---

### Task 1: JobController with undo
- Files: `src/evrakci/ui/controller.py`; test `tests/ui/test_controller.py`.
- Interface: `JobController(store, job)`, with methods:
  - `apply_filter(pids, n)`
  - `add_cut(pid)`, `remove_cut(pid)`
  - `apply_template(pids, tid)`
  - `rotate(pid, deg)`
  - `delete_page(pid)`, `undelete_page(pid)`
  - `set_drop_empty(bool)`
  - `set_value(doc, key, text)`
  - `undo()`, `redo()`

  It also has a `documents()` cache, and emits `job_changed`.
- Tests:
  - each edit is undone and redone exactly (compare `job_to_dict`)
  - every command saves the job
  - errors from the core (`ValueError`, `KeyError`) become a Turkish status message and change
    nothing

### Task 2: Thumbnail service
- Files: `src/evrakci/ui/thumbnails.py`; test `tests/ui/test_thumbnails.py`.
- Interface: `ThumbnailService(batch_files, height=100)` with `request(pid)`, emitting
  `ready(pid, QImage)`. It holds an LRU of 400 and drops requests that are no longer visible.
- Tests: an LRU bound; with 1000 fake pages, only the requested ids are rendered.

### Task 3: Timeline view (Kontrol)
- Files:
  - `src/evrakci/ui/timeline.py`: `TimelineModel` (a `QAbstractListModel` of pages, with roles
    for the document band, cut type before the page, dropped, flags and template name),
    `TimelineDelegate` and `TimelineView` (horizontal, range selection)
  - `src/evrakci/ui/kontrol.py`: the screen, with the toolbar, whole-job strip, guide-tab
    timeline, document table and side panel from `kartotek/kontrol.png`
- Tests:
  - the cut type before each page (QR, filter or manual) matches `compute_documents`
  - selecting pages 5–9 then "Filtre: her N sayfa" calls `apply_filter` with those ids
  - delegate paint smoke tests for each cut type, rendered offscreen
  - the 1000-page first paint

### Task 4: Yükle screen
- Files: `src/evrakci/ui/yukle.py`.
- What it does: a job list (`JobStore.list_jobs`); new job from PDFs (drag-drop or a file dialog);
  add batch; reorder or remove batches; analysis progress with cancel.
- Tests: creating a job from 2 synthetic PDFs through the screen gives the same job as
  `is olustur`.

### Task 5: Template creator (Şablonlar)
- Files:
  - `src/evrakci/ui/sablon.py`: template list; variable panel (add, rename, required; variants
    reorderable by drag)
  - `PageCanvas` (a `QGraphicsView`): rubber-band box drawing converted to mm in the displayed
    orientation, colour per variable, dashed variants
  - live "Bu kutular ne okuyor?" panel (a worker calling `read_document` on the example)
  - pattern bar with variable chips; import and export
- Tests:
  - drawing a rectangle at known pixels gives the expected `box_mm`, on A4, Letter and a rotated
    page
  - adding a variant from a second example appends a `Section` with `example` set
  - drag reorder calls `move_section`

### Task 6: Review table (Değerler)
- Files: `src/evrakci/ui/degerler.py`.
- What it does:
  - one row per templated document and one column per variable; unsure cells highlighted
  - a "Yalnızca kontrol gerekenler" filter
  - side preview with the box highlighted
  - "Öneriyi kabul et", "Elle yaz" and "Yeni varyant çiz" (which opens the template creator on
    this page)
  - "Değerleri oku" and "Yalnızca eksikleri oku" buttons (worker)
- Tests: an edited cell sets `edited=True`; accepting a suggestion; the filter hides documents
  that need no check.

### Task 7: Export and Guide
- Files: `src/evrakci/ui/disa_aktar.py`, `src/evrakci/ui/rehber.py`.
- Export: pick an empty folder; a text-layer option (on by default); progress and cancel; a result
  list with `[kontrol]` marks; "index.xlsx'i aç".
- Guide: `docs/tarama-rehberi.md` shown with `QTextBrowser.setMarkdown`, plus the separator
  sheet print button (`make_separator_pdf`, then open it).
- Tests: the export output matches `is disa-aktar` on the same job (same names, same index rows).

### Task 8: Main window, settings and close behaviour
- Files: `src/evrakci/ui/main_window.py` (tabs as in the mockups; a status bar; retention setting
  in an "Ayarlar" dialog) and `src/evrakci/app.py`.
- Tests:
  - the tab names match the mockups
  - closing during export asks first
  - reopening shows the last job

### Task 9: Installer refresh and docs
- Re-run the Windows workflow (the window replaces the placeholder).
- Add a screenshot of each screen to the README (synthetic data only).
