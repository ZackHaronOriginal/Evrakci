# Plan 1: Splitting Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the processing code (no UI) for the following:
- turn scanned batch PDFs into a saved job
- find QR separator pages and empty pages
- calculate document cuts from QR pages, manual cuts and "every N pages" filters
- write one PDF per document

A small command-line tool lets the owner try it before the timeline screen exists.

**Architecture:**
- Everything lives in `src/evrakci/pipeline/` and never imports Qt.
- A `Job` is plain data (batches, per-page analysis, the user's edits) saved as JSON in the job's
  own folder.
- `compute_documents(job)` is a pure function that turns a job into a list of documents. The
  timeline screen (Plan 2) and export (Plan 5) will both call it.

**Tech Stack:** Python 3.11+, pikepdf (MPL-2.0), pypdfium2 (Apache-2.0/BSD-3), Pillow (HPND),
segno (BSD-3, QR generation), zxing-cpp (Apache-2.0, QR reading), platformdirs (MIT), pytest, ruff.

**Spec:** `docs/superpowers/specs/2026-11-06-scan-and-split-design.md` (Sections 4, 6.1 output
rules, and 10)

### Roadmap (one plan per part of the spec; each ends with working software)

1. **Splitting engine** (this plan)
2. Timeline editor screen, after the owner reviews mockups
3. OCR engine test (Tesseract vs RapidOCR) and the OCR layer
4. Template creator, and reading variables
5. Review table and export (named PDFs, PDF/A-2b, `index.xlsx`)
6. Windows installer

## Global Constraints

- Python `>=3.11`.
- `src/evrakci/pipeline/` never imports `PySide6`.
- Every new dependency must be MIT, BSD, Apache-2.0, MPL-2.0, HPND, or LGPL used as a separate
  library.
  - No PyMuPDF, no PyQt, no Ghostscript.
  - Record each new dependency in `docs/dependency-licenses.md`.
- UI text and user docs are in Turkish. Code, comments and test names are in English.
- Only synthetic documents in tests and in the repo. Tests generate their PDFs in `tmp_path`.
- **Blank pages never cause a cut.** Only QR pages, manual cuts and filters cut.
- QR pages are always left out of the output.
- "Drop empty pages" (`drop_empty`) is **off by default**. Dropped pages can be restored.
- Filters only apply to the pages they were applied to.
  - The last-applied filter wins where filters overlap.
  - A filter never counts across a cut. Counting restarts at 1 after any cut.
  - Leftover pages become a shorter document flagged `"leftover"`.
- Wherever no filter applies, everything between two cuts is one document.
- `ruff check .` and `pytest -q` pass before every commit.

## Review Focus

The five failure modes most likely to bite users that the main tests don't cover. Each one has a
test in the task that owns that code:

1. **Pages already rotated or landscape in the scan** (a `/Rotate` already set on the PDF page).
   The user's rotation must add to the existing one, not replace it. Test in Task 5.
2. **A QR page photocopied small, slightly skewed or faint** still counts as a separator. Test in
   Task 2.
3. **A broken, encrypted or 0-page PDF added as a batch** gives a clear Turkish error and doesn't
   create a half-made job. Test in Task 6.
4. **A job where everything is separators, or every page is deleted** gives zero documents, and
   writing writes nothing, without crashing. Tests in Tasks 4 and 5.
5. **Reordering batches, or adding the same file twice:** page identities stay unique per batch,
   and filters stay on their own pages after a reorder. Turkish letters in folder paths
   (`Gökçe Şahin`) work. Tests in Tasks 4 and 6.

---

### Task 1: Separator sheet and test fakes

**Files:**
- Modify: `pyproject.toml` (add `segno>=1.6`, `zxing-cpp>=2.2`, `platformdirs>=4.0`, `pillow>=10`
  to `dependencies`, each with a license comment like the existing ones)
- Create: `src/evrakci/pipeline/separator.py`
- Create: `tests/fakes.py`
- Test: `tests/test_separator.py`

**Interfaces:**
- Produces, in `evrakci.pipeline.separator`:
  - `SEPARATOR_PAYLOAD: str = "EVRAKCI-AYIRAC-1"`
  - `is_separator_payload(text: str) -> bool`: true when `text` starts with `"EVRAKCI-AYIRAC"`
  - `render_separator_image(dpi: int = 150) -> PIL.Image.Image`: one A4 page, white, grayscale
    (`"L"`)
    - large QR in the middle (error correction `"h"`, about 9 cm wide)
    - the text `"AYIRAÇ"` above it and `"Bu sayfa çıktıya girmez"` below it
  - `make_separator_pdf(path: Path, sheets: int = 1) -> Path`: writes `2 * sheets` identical pages
    (front and back of each sheet, as spec 4.2 requires) and returns `path`
- Produces, in `tests/fakes.py` (test-only helpers, 100 dpi A4 pages, 827×1169 px):
  - `text_page(label: str = "") -> Image`: white page with several dark text-like rectangles
    (ink well above the empty threshold)
  - `empty_page(speckles: int = 30) -> Image`: white page with a few 1-px dark dots (scanner dust)
  - `qr_page(scale: float = 1.0, angle: float = 0.0) -> Image`: `render_separator_image(dpi=100)`,
    optionally shrunk by `scale` (pasted onto a white A4) and rotated by `angle` degrees
  - `make_pdf(path: Path, pages: list[Image]) -> Path`: saves a multi-page PDF with Pillow at
    `resolution=100`

- [ ] **Step 1: Write the failing tests** in `tests/test_separator.py`

```python
def test_payload_recognised():
    assert is_separator_payload(SEPARATOR_PAYLOAD)
    assert is_separator_payload("EVRAKCI-AYIRAC-2")
    assert not is_separator_payload("https://example.com")

def test_separator_pdf_has_front_and_back(tmp_path):
    path = make_separator_pdf(tmp_path / "ayirac.pdf", sheets=3)
    assert len(pikepdf.open(path).pages) == 6

def test_separator_image_qr_decodes():
    texts = [b.text for b in zxingcpp.read_barcodes(render_separator_image(dpi=100))]
    assert texts == [SEPARATOR_PAYLOAD]
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `pytest tests/test_separator.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'evrakci.pipeline.separator'`

- [ ] **Step 3: Implement `separator.py` and `tests/fakes.py`** with the signatures above.
  - Generate the QR with `segno.make(SEPARATOR_PAYLOAD, error="h")`, rendered to a PNG in memory
    and pasted onto the page.
  - Use `ImageFont.load_default(size=...)` for the text.
  - Write PDFs with Pillow's `save(..., save_all=True, append_images=..., resolution=dpi)`.

- [ ] **Step 4: Install and run the tests**

Run: `pip install -e ".[dev]" && pytest tests/test_separator.py -v && ruff check .`
Expected: 3 passed, ruff clean

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src/evrakci/pipeline/separator.py tests/fakes.py tests/test_separator.py
git commit -m "feat: printable QR separator sheet"
```

---

### Task 2: Page analysis (QR and ink)

**Files:**
- Create: `src/evrakci/pipeline/analyze.py`
- Test: `tests/test_analyze.py`

**Interfaces:**
- Consumes: `is_separator_payload` (Task 1); `tests/fakes.py` helpers
- Produces, in `evrakci.pipeline.analyze`:
  - `EMPTY_INK_RATIO: float = 0.003`
  - `@dataclass(frozen=True) class PageInfo: ink_ratio: float; is_separator: bool`, with property
    `is_empty -> bool` (`ink_ratio < EMPTY_INK_RATIO and not is_separator`)
  - `analyze_pdf(path: Path, progress: Callable[[int, int], None] | None = None) -> list[PageInfo]`
    - one entry per page, in page order
    - calls `progress(done, total)` after each page
  - `class BatchError(Exception)`: raised with a Turkish message when the file can't be opened as
    a PDF or has 0 pages

- [ ] **Step 1: Write the failing tests** in `tests/test_analyze.py`

```python
def test_kinds_detected(tmp_path):
    pdf = make_pdf(tmp_path / "b.pdf", [text_page(), empty_page(), qr_page(), text_page()])
    infos = analyze_pdf(pdf)
    assert [i.is_separator for i in infos] == [False, False, True, False]
    assert [i.is_empty for i in infos] == [False, True, False, False]

def test_small_skewed_qr_still_separator(tmp_path):   # Review Focus 2
    pdf = make_pdf(tmp_path / "b.pdf", [qr_page(scale=0.35, angle=5)])
    assert analyze_pdf(pdf)[0].is_separator

def test_progress_reported(tmp_path):
    pdf = make_pdf(tmp_path / "b.pdf", [text_page(), text_page()])
    calls = []
    analyze_pdf(pdf, progress=lambda d, t: calls.append((d, t)))
    assert calls == [(1, 2), (2, 2)]

def test_not_a_pdf(tmp_path):
    bad = tmp_path / "bad.pdf"; bad.write_bytes(b"not a pdf")
    with pytest.raises(BatchError):
        analyze_pdf(bad)
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `pytest tests/test_analyze.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `analyze.py`.**
  - Render each page once with pypdfium2 at 100 dpi in grayscale (`page.render(scale=100/72,
    grayscale=True).to_pil()`).
  - Look for a QR with `zxingcpp.read_barcodes(img, formats=zxingcpp.BarcodeFormat.QRCode)`. The
    page is a separator if any decoded text passes `is_separator_payload`.
  - The ink ratio is the share of pixels below 160 after cropping 6% off every edge (scanners
    leave dark borders).
  - Close every page and document object. Wrap pypdfium2 errors in `BatchError("PDF açılamadı:
    {name}")`, and 0 pages in `BatchError("PDF boş: {name}")`.

- [ ] **Step 4: Run the tests**

Run: `pytest tests/test_analyze.py -v && ruff check .`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add src/evrakci/pipeline/analyze.py tests/test_analyze.py
git commit -m "feat: detect QR separator and empty pages"
```

---

### Task 3: Job model and JSON round-trip

**Files:**
- Create: `src/evrakci/pipeline/job.py`
- Test: `tests/test_job.py`

**Interfaces:**
- Consumes: `PageInfo` (Task 2)
- Produces, in `evrakci.pipeline.job`:
  - `page_id(batch_id: str, index: int) -> str` returns `f"{batch_id}/{index}"`
  - `parse_page_id(pid: str) -> tuple[str, int]`
  - `@dataclass(frozen=True) class Batch: id: str; file_name: str; page_count: int`
  - `@dataclass(frozen=True) class FilterApplication: page_ids: frozenset[str]; every_n: int`
  - `@dataclass class Job`, with fields:
    - `id: str`
    - `name: str`
    - `batches: list[Batch]`
    - `pages: dict[str, PageInfo]`
    - `drop_empty: bool = False`
    - `deleted: set[str]`
    - `restored: set[str]` (empty pages put back)
    - `rotations: dict[str, int]` (extra clockwise degrees: 0, 90, 180 or 270)
    - `manual_cuts: set[str]` (a cut **before** that page)
    - `removed_cuts: set[str]` (QR pages whose cut the user removed)
    - `filters: list[FilterApplication]` (in the order applied)

    All collections default to empty. Methods:
    - `ordered_page_ids() -> list[str]`: every page of every batch, batches in list order
    - `apply_filter(page_ids: Iterable[str], every_n: int) -> None`: appends; raises `ValueError`
      if `every_n < 1`
    - `rotate(pid: str, degrees: int) -> None`: adds, modulo 360; raises `ValueError` unless a
      multiple of 90
  - `JOB_FORMAT_VERSION = 1`, `job_to_dict(job: Job) -> dict`, `job_from_dict(data: dict) -> Job`
    (sets become sorted lists; `job_from_dict` raises `ValueError` on an unknown version)
- Produces, in `tests/fakes.py`: `job_from_kinds(spec: dict[str, str]) -> Job`
  - Builds a job directly, with no PDFs. Each batch id maps to a string of page kinds: `p` text,
    `e` empty, `q` QR. Example: `job_from_kinds({"a": "ppqp", "b": "pe"})`.

- [ ] **Step 1: Write the failing tests** in `tests/test_job.py`

```python
def test_order_follows_batches():
    job = job_from_kinds({"a": "pp", "b": "p"})
    job.batches.reverse()
    assert job.ordered_page_ids() == ["b/0", "a/0", "a/1"]

def test_round_trip():
    job = job_from_kinds({"a": "pqep"})
    job.drop_empty = True
    job.manual_cuts.add("a/3"); job.rotate("a/0", 90); job.apply_filter(["a/0", "a/3"], 2)
    assert job_from_dict(json.loads(json.dumps(job_to_dict(job)))) == job

def test_bad_inputs():
    job = job_from_kinds({"a": "p"})
    with pytest.raises(ValueError): job.apply_filter(["a/0"], 0)
    with pytest.raises(ValueError): job.rotate("a/0", 45)
    with pytest.raises(ValueError): job_from_dict({**job_to_dict(job), "version": 99})
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `pytest tests/test_job.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `job.py` and add `job_from_kinds` to `tests/fakes.py`.** The kinds map
  to `PageInfo` like this:
  - `p` → `PageInfo(0.05, False)`
  - `e` → `PageInfo(0.0, False)`
  - `q` → `PageInfo(0.02, True)`

  The page count comes from the string length, and the file name is `f"{batch_id}.pdf"`.

- [ ] **Step 4: Run the tests**

Run: `pytest tests/test_job.py -v && ruff check .`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/evrakci/pipeline/job.py tests/fakes.py tests/test_job.py
git commit -m "feat: job model with JSON round-trip"
```

---

### Task 4: Cut calculation

**Files:**
- Create: `src/evrakci/pipeline/cuts.py`
- Test: `tests/test_cuts.py`

**Interfaces:**
- Consumes: `Job`, `FilterApplication` (Task 3)
- Produces, in `evrakci.pipeline.cuts`:
  - `@dataclass(frozen=True) class Document: page_ids: tuple[str, ...]; flags: frozenset[str] =
    frozenset()`. The only flag for now is `"leftover"`.
  - `compute_documents(job: Job) -> list[Document]`
- Cuts that can be removed: QR cuts (through `removed_cuts`) and manual cuts. Cuts made by a filter
  change only by changing or removing that filter. (This was decided while writing the plan.)

- [ ] **Step 1: Write the failing tests** in `tests/test_cuts.py`. A helper turns documents into
  page lists: `ids = lambda docs: [list(d.page_ids) for d in docs]`.

```python
def test_qr_fences_and_is_dropped():
    job = job_from_kinds({"a": "ppqpppqpp"})
    assert ids(compute_documents(job)) == [["a/0","a/1"], ["a/3","a/4","a/5"], ["a/7","a/8"]]

def test_empty_pages_never_cut():
    job = job_from_kinds({"a": "pepep"})
    assert ids(compute_documents(job)) == [["a/0","a/1","a/2","a/3","a/4"]]
    job.drop_empty = True
    assert ids(compute_documents(job)) == [["a/0","a/2","a/4"]]
    job.restored.add("a/1")
    assert ids(compute_documents(job)) == [["a/0","a/1","a/2","a/4"]]

def test_filter_only_on_selection_and_leftover_flagged():
    job = job_from_kinds({"a": "ppppppp"})
    job.apply_filter([f"a/{i}" for i in range(5)], 2)          # pages 0-4 only
    docs = compute_documents(job)
    assert ids(docs) == [["a/0","a/1"], ["a/2","a/3"], ["a/4"], ["a/5","a/6"]]
    assert [d.flags for d in docs] == [set(), set(), {"leftover"}, set()]

def test_filter_restarts_after_qr_and_manual_cut():
    job = job_from_kinds({"a": "ppppqppppp"})
    job.apply_filter(job.ordered_page_ids(), 2)
    job.manual_cuts.add("a/8")
    assert ids(compute_documents(job)) == [
        ["a/0","a/1"], ["a/2","a/3"], ["a/5","a/6"], ["a/7"], ["a/8","a/9"]]

def test_last_filter_wins():
    job = job_from_kinds({"a": "pppppp"})
    job.apply_filter(job.ordered_page_ids(), 3)
    job.apply_filter(["a/0","a/1"], 1)
    assert ids(compute_documents(job)) == [["a/0"], ["a/1"], ["a/2","a/3","a/4"], ["a/5"]]

def test_removed_qr_cut_and_deleted_pages():
    job = job_from_kinds({"a": "ppqpp"})
    job.removed_cuts.add("a/2"); job.deleted.add("a/0")
    assert ids(compute_documents(job)) == [["a/1","a/3","a/4"]]

def test_nothing_left():                                      # Review Focus 4
    assert compute_documents(job_from_kinds({"a": "qqq"})) == []
    job = job_from_kinds({"a": "pp"}); job.deleted |= {"a/0", "a/1"}
    assert compute_documents(job) == []

def test_filter_follows_pages_after_batch_reorder():          # Review Focus 5
    job = job_from_kinds({"a": "pppp", "b": "pp"})
    job.apply_filter(["a/0","a/1","a/2","a/3"], 2)
    job.batches.reverse()
    assert ids(compute_documents(job)) == [["b/0","b/1"], ["a/0","a/1"], ["a/2","a/3"]]
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `pytest tests/test_cuts.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `compute_documents`.** It makes a single pass over the pages in order:

```
current = []; current_filter = None
for pid in job.ordered_page_ids():
    if pid in job.deleted: continue
    info = job.pages[pid]
    if info.is_separator:
        if pid not in job.removed_cuts: close()
        continue                                   # QR pages never reach the output
    if job.drop_empty and info.is_empty and pid not in job.restored: continue
    if pid in job.manual_cuts: close()
    f = last filter in job.filters whose page_ids contains pid, else None
    if f is not current_filter: close(); current_filter = f
    current.append(pid)
    if f is not None and len(current) == f.every_n: close()
close()
```

`close()` adds `current` as a `Document` if it isn't empty. It sets the `"leftover"` flag when
`current_filter` is set and `len(current) < current_filter.every_n`. Then it empties `current`
(and leaves `current_filter` as it is). Look up each page's filter with a dict built once,
`pid -> last FilterApplication`, so 800 pages stay fast.

- [ ] **Step 4: Run the tests**

Run: `pytest tests/test_cuts.py -v && ruff check .`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add src/evrakci/pipeline/cuts.py tests/test_cuts.py
git commit -m "feat: calculate document cuts from QR pages, manual cuts and filters"
```

---

### Task 5: Writing documents

**Files:**
- Create: `src/evrakci/pipeline/writer.py`
- Test: `tests/test_writer.py`

**Interfaces:**
- Consumes: `Document` (Task 4), `parse_page_id` (Task 3)
- Produces, in `evrakci.pipeline.writer`:
  - `write_documents(documents: Sequence[Document], batch_files: Mapping[str, Path], rotations:
    Mapping[str, int], out_dir: Path, stem: str = "belge") -> list[Path]`
    - writes `out_dir/{stem}_001.pdf`, `_002.pdf`, ... and creates `out_dir` if needed
    - returns the paths in document order
    - writes nothing for an empty list
  - Plan 5 replaces the numbered names with template names. Plan 3 adds the text layer.

- [ ] **Step 1: Write the failing tests** in `tests/test_writer.py`

```python
def test_pages_and_order(tmp_path):
    a = make_pdf(tmp_path / "a.pdf", [text_page("A0"), text_page("A1"), text_page("A2")])
    docs = [Document(("a/2",)), Document(("a/0", "a/1"))]
    out = write_documents(docs, {"a": a}, {}, tmp_path / "out")
    assert [p.name for p in out] == ["belge_001.pdf", "belge_002.pdf"]
    assert [len(pikepdf.open(p).pages) for p in out] == [1, 2]

def test_rotation_adds_to_existing(tmp_path):                 # Review Focus 1
    a = make_pdf(tmp_path / "a.pdf", [text_page()])
    with pikepdf.open(a, allow_overwriting_input=True) as pdf:
        pdf.pages[0].rotate(90, relative=False); pdf.save(a)
    out = write_documents([Document(("a/0",))], {"a": a}, {"a/0": 90}, tmp_path / "out")
    assert pikepdf.open(out[0]).pages[0].obj.Rotate == 180

def test_nothing_to_write(tmp_path):                          # Review Focus 4
    assert write_documents([], {}, {}, tmp_path / "out") == []
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `pytest tests/test_writer.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `write_documents`.**
  - Open each needed batch once with pikepdf.
  - For each document, create a new `Pdf`, append the source pages, then call
    `page.rotate(rotations.get(pid, 0), relative=True)` on the appended page.
  - Save the file.

- [ ] **Step 4: Run the tests**

Run: `pytest tests/test_writer.py -v && ruff check .`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add src/evrakci/pipeline/writer.py tests/test_writer.py
git commit -m "feat: write one PDF per document"
```

---

### Task 6: Job storage on disk

**Files:**
- Create: `src/evrakci/pipeline/store.py`
- Test: `tests/test_store.py`

**Interfaces:**
- Consumes: `analyze_pdf`, `BatchError` (Task 2); `Job`, `Batch`, `page_id`, `job_to_dict`,
  `job_from_dict` (Task 3)
- Produces, in `evrakci.pipeline.store`:
  - `default_root() -> Path`: `platformdirs.user_data_path("Evrakci", appauthor=False) / "jobs"`
  - `class JobStore`, constructed as `JobStore(root: Path)`. Methods:
    - `create_job(name: str, pdf_paths: Sequence[Path], progress: Callable[[int, int], None] |
      None = None) -> Job`
    - `add_batch(job: Job, pdf_path: Path) -> Batch`: analyzes, copies and saves
    - `save(job: Job) -> None`
    - `load(job_id: str) -> Job`
    - `list_jobs() -> list[Job]`, newest first
    - `batch_file(job: Job, batch: Batch) -> Path`
    - `batch_files(job: Job) -> dict[str, Path]`
  - Layout: `root/<job.id>/job.json` and `root/<job.id>/batches/<batch.id>.pdf`.
    - The job id is `uuid4().hex[:12]`.
    - Batch ids are `b1`, `b2`, ... and are never reused within a job.
  - `save` writes `job.json` to a temporary file and then renames it, so a crash never leaves a
    half-written job.

- [ ] **Step 1: Write the failing tests** in `tests/test_store.py`

```python
def test_create_save_load(tmp_path):
    src = make_pdf(tmp_path / "tarama.pdf", [text_page(), qr_page(), text_page()])
    store = JobStore(tmp_path / "Gökçe Şahin" / "jobs")          # Review Focus 5
    job = store.create_job("Seçim 2026", [src, src])             # same file twice
    assert [b.id for b in job.batches] == ["b1", "b2"]
    assert len(job.pages) == 6 and job.pages["b2/1"].is_separator
    job.manual_cuts.add("b1/2"); store.save(job)
    assert store.load(job.id) == job
    assert [j.id for j in store.list_jobs()] == [job.id]
    assert store.batch_file(job, job.batches[0]).exists()

def test_bad_batch_leaves_no_job(tmp_path):                       # Review Focus 3
    good = make_pdf(tmp_path / "ok.pdf", [text_page()])
    bad = tmp_path / "bozuk.pdf"; bad.write_bytes(b"%PDF-1.4 broken")
    store = JobStore(tmp_path / "jobs")
    with pytest.raises(BatchError):
        store.create_job("x", [good, bad])
    assert store.list_jobs() == [] and not any((tmp_path / "jobs").glob("*"))
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `pytest tests/test_store.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `store.py`.** `create_job` analyzes every input before creating any
  folder. It copies files with `shutil.copy2`. If anything fails after the folder exists, it
  removes the folder.

- [ ] **Step 4: Run the tests**

Run: `pytest tests/test_store.py -v && ruff check .`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add src/evrakci/pipeline/store.py tests/test_store.py
git commit -m "feat: save and load jobs in the app data folder"
```

---

### Task 7: Command-line tool `evrakci-ayir`

This lets the owner try the engine on real scans on their own PC before Plan 2 exists. It is not a
staff feature.

**Files:**
- Create: `src/evrakci/cli.py`
- Modify: `pyproject.toml`
  - add `[project.scripts] evrakci-ayir = "evrakci.cli:main"`
  - add `evrakci-ayirac = "evrakci.cli:separator_main"`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: `JobStore` (Task 6), `compute_documents` (Task 4), `write_documents` (Task 5),
  `make_separator_pdf` (Task 1)
- Produces:
  - `main(argv: Sequence[str] | None = None) -> int`
    - arguments: `PDF [PDF ...] --cikti DIR [--filtre BAS-SON:N ...] [--bos-sayfalari-at]`
    - `BAS-SON` are 1-based positions in the combined scan order (QR pages included), so the
      numbers match the order of the paper pile
    - it creates the job in a temporary `JobStore`, applies the options, writes the documents and
      prints one Turkish line per file: `belge_001.pdf: sayfa 1, 2`
    - returns `0`
    - a bad `--filtre`, or a `BatchError`, prints a Turkish error to stderr and returns `2`
  - `separator_main(argv: Sequence[str] | None = None) -> int`
    - arguments: `CIKTI.pdf [--adet N]`
    - writes a separator PDF with N sheets (default 10)

- [ ] **Step 1: Write the failing tests** in `tests/test_cli.py`

```python
def test_split_with_filter(tmp_path, capsys):
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()] * 4 + [qr_page()] + [text_page()] * 3)
    code = main([str(pdf), "--cikti", str(tmp_path / "out"), "--filtre", "1-4:2"])
    assert code == 0
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [
        "belge_001.pdf", "belge_002.pdf", "belge_003.pdf"]
    assert "belge_001.pdf: sayfa 1, 2" in capsys.readouterr().out

def test_bad_filter(tmp_path):
    pdf = make_pdf(tmp_path / "t.pdf", [text_page()])
    assert main([str(pdf), "--cikti", str(tmp_path / "o"), "--filtre", "abc"]) == 2

def test_separator_command(tmp_path):
    assert separator_main([str(tmp_path / "a.pdf"), "--adet", "2"]) == 0
    assert len(pikepdf.open(tmp_path / "a.pdf").pages) == 4
```

- [ ] **Step 2: Run the tests to make sure they fail**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement `cli.py`** with `argparse`. Turkish help text. The printed page numbers
  are 1-based positions in the combined scan order.

- [ ] **Step 4: Run the whole suite**

Run: `pip install -e ".[dev]" && pytest -q && ruff check .`
Expected: all tests pass, ruff clean

- [ ] **Step 5: Commit**

```bash
git add src/evrakci/cli.py pyproject.toml tests/test_cli.py
git commit -m "feat: evrakci-ayir and evrakci-ayirac command-line tools"
```

---

### Task 8: Bring the docs in line with the design

**Files:**
- Modify: `README.md` and `README.tr.md`
  - "How it works" now reads: batches → QR pages and filters → timeline → OCR → templates →
    review → export.
  - Remove the makbuz/fatura framing; Evrakçı is an all-round quality-of-life toolbox.
  - Add the two commands from Task 7 under Development.
- Modify: `docs/architecture.md`
  - match spec sections 3–7
  - list the pipeline modules from this plan
  - storage is `job.json` per job folder, not SQLite
- Modify: `docs/tarama-rehberi.md`
  - replace the blank-separator section with QR separator sheets, placed before and after a
    document that needs fencing off
  - say blank pages never split anything
- Modify: `docs/dependency-licenses.md`: add segno (BSD-3), zxing-cpp (Apache-2.0), platformdirs
  (MIT), Pillow (HPND); mark Ghostscript as "not used"
- Modify: `samples/synthetic/README.md`: replace makbuz/fatura wording with "synthetic documents";
  point to `tests/fakes.py` and `evrakci-ayirac`
- Modify: `docs/superpowers/specs/2026-11-06-scan-and-split-design.md`: change line 4 to
  `Status: approved by owner, 2026-11-06`

- [ ] **Step 1: Make the edits above.**

- [ ] **Step 2: Check nothing still describes the old design**

Run: `grep -rniE "boş beyaz|blank sheet|makbuz / fatura|SQLite" README.md README.tr.md docs/*.md samples`
Expected: no matches, except in the "later modules" lists

- [ ] **Step 3: Commit**

```bash
git add README.md README.tr.md docs samples
git commit -m "docs: align README, architecture and scanning guide with the approved design"
```
