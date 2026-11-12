# Plan 2b: OCR Text Layer. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every exported PDF gets a searchable Turkish text layer and is saved as PDF/A-2b, without
Ghostscript. If a file fails the PDF/A check, it is written as a plain searchable PDF and the reason
is recorded. This also adds a standalone `evrakci ocr` command.

**Architecture:**
- `pipeline/ocr/textlayer.py` wraps OCRmyPDF's Python API with `--pdfa-backend internal`.
- Tesseract's language data comes from `default_tessdata()`: verified `tur_best` when present,
  otherwise the system `tur`. This is a **provisional default** until the owner picks the engine;
  both of the owner's options are Tesseract, so only this default changes.
- A separate data folder gets Tesseract's small `configs`/`tessconfigs` folders copied in, because
  Tesseract needs them for its `hocr`/`txt` output.
- `is disa-aktar` adds the text layer by default.
- Variable reading (Plan 3) uses `default_engine()`, which is the same Tesseract setup.

**Tech Stack:**
- OCRmyPDF ≥ 17.13 (MPL-2.0)
- `pikepdf[pdfa]` ≥ 10.15 (MPL-2.0, plus jsonschema, referencing, fonttools, rpds-py, attrs, all
  MIT)
- Tesseract 5

**Spec:** `docs/superpowers/specs/2026-11-06-scan-and-split-design.md` §6.1 (output, PDF/A without
Ghostscript) and §7

## Global Constraints

- Never call or bundle Ghostscript: `pdfa_backend="internal"` always. Tests run where `gs` is
  absent.
- PDF/A failure falls back to a plain PDF (`output_type="pdf"`), and the result records
  `pdfa=False` with a Turkish note. It is never silent.
- The core never imports Qt.
- Turkish CLI text. Commits authored by ZackHaronOriginal with no Claude lines.
- `ruff check .` and `pytest -q` pass before each commit.
- Tests that need Tesseract use `needs_tesseract`.

## Review Focus

1. **An input page that already has text** (a digital PDF mixed into the scans). Its existing text
   is kept and the page is not re-OCR'd (`mode="skip"`), with no crash. Test in Task 2.
2. **Encrypted or broken input** gives a Turkish error, never a traceback. Test in Task 2.
3. **Tesseract missing at export time.** `is disa-aktar` stops before writing anything, with a
   Turkish message that names `--metin-katmani-yok`. Test in Task 3.
4. **A `tur_best` folder without config files** (a fresh download). `prepare_tessdata` fills in the
   configs, and OCR works. Test in Task 1.
5. **Non-ASCII paths** (`C:\Users\Şükrü\...`) for both the data folder and the output. Test in
   Task 2, using a Turkish temp path.

---

### Task 1: Tesseract data setup and default engine

**Files:**
- Modify: `src/evrakci/pipeline/ocr/tesseract.py`, `src/evrakci/pipeline/ocr/compare.py` (use the
  moved `system_tessdata`), `src/evrakci/cli/ocr.py` (`ocr-modelleri-indir` calls
  `prepare_tessdata`)
- Test: `tests/test_ocr_tesseract.py`

**Interfaces:**
- Produces, in `ocr/tesseract.py`:
  - `system_tessdata() -> Path | None` (moved from `compare._system_tessdata`)
  - `prepare_tessdata(folder: Path) -> None`: copies `configs/` and `tessconfigs/` from
    `system_tessdata()` into `folder` when they're missing
  - `@dataclass(frozen=True) class TessData: language: str; folder: Path | None` (`None` means the
    system folder)
  - `default_tessdata() -> TessData`: when `verify_tur_best(tessdata_best_dir())` holds, calls
    `prepare_tessdata(tessdata_best_dir())` and returns `TessData("tur", tessdata_best_dir())`;
    otherwise returns `TessData("tur", None)`
  - `default_engine() -> TesseractEngine`, built from `default_tessdata()`

- [ ] **Step 1: Write the failing tests**

```python
@needs_tesseract
def test_prepare_tessdata_copies_configs(tmp_path):
    shutil.copy(system_tessdata() / "tur.traineddata", tmp_path)
    prepare_tessdata(tmp_path)
    assert (tmp_path / "configs" / "hocr").is_file()

def test_default_falls_back_to_system(tmp_path, monkeypatch):
    monkeypatch.setenv("EVRAKCI_TESSDATA_BEST", str(tmp_path / "none"))
    assert default_tessdata() == TessData("tur", None)
```

- [ ] **Step 2: Run the tests to make sure they fail**
- [ ] **Step 3: Implement**
- [ ] **Step 4: Run the tests**: `pytest tests/test_ocr_tesseract.py -q` passes, and ruff is
  clean.
- [ ] **Step 5: Commit**: `feat: Tesseract data setup and default engine`

---

### Task 2: Text layer with PDF/A-2b and fallback

**Files:**
- Create: `src/evrakci/pipeline/ocr/textlayer.py`
- Modify: `pyproject.toml` (`ocrmypdf>=17.13`, `pikepdf[pdfa]>=10.15`)
- Test: `tests/test_textlayer.py`

**Interfaces:**
- Produces:
  - `@dataclass(frozen=True) class TextLayerResult: path: Path; pdfa: bool; note: str | None`
  - `add_text_layer(src: Path, dst: Path, tessdata: TessData | None = None, pdfa: bool = True,
    jobs: int | None = None) -> TextLayerResult`
- The call is `ocrmypdf.ocr(src, dst, language=tessdata.language, output_type="pdfa-2" if pdfa
  else "pdf", pdfa_backend="internal", mode="skip", jobs=jobs, progress_bar=False)`.
  - `TESSDATA_PREFIX` is set to `tessdata.folder` during the call and restored afterwards.
- On `ExitCode.pdfa_conversion_failed`, or a PDF/A exception: retry with `output_type="pdf"` and
  return `pdfa=False, note="PDF/A doğrulanamadı; normal PDF yazıldı"`.
- Error mapping (raise `EngineUnavailable` with these messages):
  - missing Tesseract: `"Tesseract bulunamadı"`
  - encrypted input: `"PDF şifreli: {name}"`
  - other OCRmyPDF errors: `"Metin katmanı eklenemedi: {name} ({reason})"`

- [ ] **Step 1: Write the failing tests** (using `needs_tesseract`; inputs from `fakes`)

```python
def test_pdfa_with_turkish_text(tmp_path):  # tmp_path / "Şükrü" as folder
    result = add_text_layer(src, out)
    assert result.pdfa and pikepdf.open(out).open_metadata().pdfa_status == "2B"
    assert "Örnek Kayıt Şişli 2026" in page_text(out, 0)

def test_falls_back_to_plain_pdf(monkeypatch, tmp_path):
    # wrap ocrmypdf.ocr: first call (pdfa) returns ExitCode.pdfa_conversion_failed, second runs normally
    result = add_text_layer(src, out)
    assert not result.pdfa and "PDF/A" in result.note and out.is_file()

def test_page_with_existing_text_kept(tmp_path): ...   # a pikepdf page with a text operator plus one scan page
def test_encrypted_input(tmp_path): ...                # EngineUnavailable, "şifreli"
def test_plain_pdf_option(tmp_path): ...               # pdfa=False → no PDF/A metadata, text present
```

  Write each `...` test in full from its comment. `page_text(path, index)` (a pypdfium2 helper) is
  added to `fakes.py`.

- [ ] **Step 2: Run the tests to make sure they fail**
- [ ] **Step 3: Implement**
- [ ] **Step 4: Run the tests**: they pass, and ruff is clean.
- [ ] **Step 5: Commit**: `feat: searchable text layer with PDF/A-2b and plain-PDF fallback`

---

### Task 3: `evrakci ocr` and text layer on export

**Files:**
- Modify: `src/evrakci/cli/ocr.py` (adds the `ocr` command), `src/evrakci/cli/jobs.py`
  (`disa-aktar`)
- Test: `tests/test_cli_ocr.py`, `tests/test_cli_edit.py`

**Interfaces:**
- `evrakci ocr GIRIS.pdf CIKTI.pdf [--pdf]`
  - prints `Metin katmanı eklendi: CIKTI.pdf (PDF/A-2b)`, or `(normal PDF: <note>)`
- `evrakci is disa-aktar ID --cikti DIR [--metin-katmani-yok]`
  - by default each written file gets the text layer in place: written to a temp name, then
    replaced
  - each file line gets ` (PDF/A-2b)` or ` (normal PDF: <note>)`
  - before writing anything, it checks `default_engine().available()`; if that fails, it exits 2
    with `Tesseract bulunamadı. Metin katmanı olmadan yazmak için --metin-katmani-yok kullanın.`
  - progress goes to stderr as `Metin katmanı: n/N belge`
- Existing export tests pass `--metin-katmani-yok` where they don't test OCR.

- [ ] **Step 1: Write the failing tests**
  - `test_ocr_command` (PDF/A output and message)
  - `test_export_adds_text_layer` (2 documents; both PDF/A with text)
  - `test_export_without_tesseract` (monkeypatch `default_engine` to an unavailable one; exit 2,
    message, no files written)
- [ ] **Step 2: Run the tests to make sure they fail**
- [ ] **Step 3: Implement**
- [ ] **Step 4: Run the whole suite**: it passes, and ruff is clean.
- [ ] **Step 5: Commit**: `feat: evrakci ocr command and text layer on export`

---

### Task 4: Docs and licenses

- Modify:
  - `docs/dependency-licenses.md`: the `pikepdf[pdfa]` extras, all MIT
  - `README.md`, `README.tr.md`: the command-line section gets `evrakci ocr`, and a note that
    export adds a Turkish text layer and PDF/A-2b
  - `docs/architecture.md`: the OCR modules
- Run `pytest -q && ruff check .`, then commit: `docs: OCR text layer`
