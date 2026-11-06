# Plan 2a: OCR Engine Test. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compare Tesseract and RapidOCR on Turkish text so the owner can pick the OCR engine.
Ship a command, `evrakci ocr-karsilastir`, that runs the same comparison on synthetic pages here
and on real scans on the owner's PC.

**Architecture:**
- Engines live behind one small interface in `src/evrakci/pipeline/ocr/`. That interface is the
  start of Plan 2b's engine layer, so the engine chosen later plugs in unchanged.
- A synthetic page generator draws Turkish text with known word boxes, and makes it look like a
  scan.
- Pure metric functions score each engine.
- A runner writes a Markdown report.
- The command line drives both modes: synthetic pages, or real PDFs with an optional JSON file of
  boxes and expected text.

**Tech Stack:**
- Tesseract 5 (external program, Apache-2.0), with `tur` and `tur_best` data
- rapidocr (Apache-2.0, code and models), onnxruntime (MIT), opencv-python-headless (Apache-2.0)
- Pillow, pypdfium2, pytest

**Spec:** `docs/superpowers/specs/2026-11-06-scan-and-split-design.md` §6.1 (engine test and engine
choice)

## Global Constraints

- `src/evrakci/pipeline/` never imports Qt.
- RapidOCR and onnxruntime are an **optional extra**, `pip install -e ".[rapidocr]"`. The core must
  import and run without them.
- Tesseract is an external program, found on `PATH`, at `EVRAKCI_TESSERACT`, or in the usual Windows
  install folder.
- **Model files** are never committed.
  - RapidOCR models are taken from the folder named by `EVRAKCI_MODEL_DIR`, or the app data folder
    `models/`.
  - If a model is missing, it is downloaded from RapidOCR's official URL.
  - Every model file is **verified against RapidOCR's own SHA-256** (from its
    `default_models.yaml`) before use. A mismatch means the file is not used.
  - Models used: detection `ch_PP-OCRv5_det_mobile`, recognition `latin_PP-OCRv5_rec_mobile`.
  - `multi_PP-OCRv6_rec_small` is optional, used only where it can be downloaded.
- **Tesseract data:** `tur` (system install) and `tur_best` (from `EVRAKCI_TESSDATA_BEST`, or the app
  data folder `tessdata_best/`). An engine whose data is missing is reported as "not available"
  and skipped, never a crash.
- Only synthetic documents in tests and in the repo. Real scans stay on the owner's PC; the report
  for them is written wherever they choose.
- Turkish for the CLI and report text, English for code.
- Every new dependency goes into `docs/dependency-licenses.md`.
- `ruff check .` and `pytest -q` pass before each commit.
- Commits are authored by ZackHaronOriginal and carry no Claude lines.
- Tests that need an engine skip when it's missing, through a pytest marker. CI installs Tesseract
  (`apt-get install tesseract-ocr tesseract-ocr-tur`).

## Review Focus

1. **Turkish case mapping.** Python's `"i".upper()` is `"I"`, not `"İ"`. Metrics must compare exact
   code points and never case-fold. Test in Task 3.
2. **Text that is decomposed vs. composed** (`"İ"` vs. `"İ"`). Engines may return either.
   Normalize both truth and reading to NFC before comparing. Test in Task 3.
3. **An empty box or an engine returning nothing** gives exact-match False and CER 1.0, with no
   division by zero. Test in Task 3.
4. **A missing engine or missing model data** is reported "kullanılamıyor" with its reason, and the
   other engines still run. Tests in Tasks 1, 2 and 5.
5. **Real PDFs with mixed page sizes or rotation**, and boxes given in millimetres. Box coordinates
   map through the page's real size at the render dpi. Test in Task 5.

---

### Task 1: Engine interface and Tesseract engine

**Files:**
- Create: `src/evrakci/pipeline/ocr/__init__.py`, `src/evrakci/pipeline/ocr/engine.py`,
  `src/evrakci/pipeline/ocr/tesseract.py`
- Modify: `tests/conftest.py` (create): marker `needs_tesseract`, skipped when
  `TesseractEngine.available()` is falsy
- Test: `tests/test_ocr_tesseract.py`

**Interfaces:**
- Produces, in `ocr/engine.py`:
  - `@dataclass(frozen=True) class Word: text: str; box: tuple[int, int, int, int]; confidence:
    float`. The box is pixel `(x0, y0, x1, y1)`; confidence is 0–1.
  - `@dataclass(frozen=True) class Reading: text: str; confidence: float` (text is NFC; lines are
    joined with `" "`)
  - `class EngineUnavailable(Exception)` (Turkish message)
  - `class OcrEngine(Protocol)`: `name: str`; `read_page(image: Image) -> list[Word]`;
    `read_region(image: Image) -> Reading`
- Produces, in `ocr/tesseract.py`:
  - `class TesseractEngine`, constructed as `TesseractEngine(lang: str = "tur", tessdata_dir: Path |
    None = None, name: str = "tesseract-tur")`
  - `available() -> str | None`: `None` when usable, otherwise a Turkish reason (binary not
    found, or language data missing)
  - `find_tesseract() -> Path | None`
- Calls `tesseract stdin stdout -l {lang} --psm {6 for regions, 3 for pages} [--tessdata-dir D]
  tsv` through `subprocess`, with the image as PNG on stdin. It parses the TSV level-5 rows, and
  confidence is `conf / 100`. `read_region` joins the words in reading order, and its confidence
  is the mean of the word confidences (0.0 if there are no words).

- [ ] **Step 1: Write the failing tests**

```python
@needs_tesseract
def test_reads_turkish_region():
    reading = TesseractEngine().read_region(render_line("İSTANBUL Şişli Çağrı Öğün ığdır"))
    assert reading.text == "İSTANBUL Şişli Çağrı Öğün ığdır" and reading.confidence > 0.5

@needs_tesseract
def test_page_words_have_boxes():
    words = TesseractEngine().read_page(render_line("Kayıt 2026"))
    assert [w.text for w in words] == ["Kayıt", "2026"]
    assert all(w.box[2] > w.box[0] and w.box[3] > w.box[1] for w in words)

def test_missing_language_reported(tmp_path):
    assert "dil" in (TesseractEngine(lang="tur", tessdata_dir=tmp_path).available() or "")
```

  `render_line(text)` is added to `tests/fakes.py`. It draws the text in DejaVuSans 40 px on white,
  with a 20 px margin, using `ocr.synthetic.find_font` (Task 3). Until Task 3 exists, a local
  helper in `fakes.py` uses the DejaVu path.

- [ ] **Step 2: Run the tests to make sure they fail**: `pytest tests/test_ocr_tesseract.py -v`
  fails with `ModuleNotFoundError`.
- [ ] **Step 3: Implement** the files above.
- [ ] **Step 4: Run the tests**: `pytest tests/test_ocr_tesseract.py -v && ruff check .` gives 3
  passed.
- [ ] **Step 5: Commit**: `feat: OCR engine interface and Tesseract engine`

---

### Task 2: RapidOCR engine with verified models

**Files:**
- Create: `src/evrakci/pipeline/ocr/models.py`, `src/evrakci/pipeline/ocr/rapid.py`
- Modify: `pyproject.toml`, adding the extra `rapidocr = ["rapidocr>=3.4", "onnxruntime>=1.17"]`;
  `tests/conftest.py`, adding the marker `needs_rapidocr`
- Test: `tests/test_ocr_rapid.py`

**Interfaces:**
- Produces, in `ocr/models.py`:
  - `@dataclass(frozen=True) class ModelFile: key: str; url: str; sha256: str; file_name: str`
  - `model_dir() -> Path`: `EVRAKCI_MODEL_DIR` if set, otherwise
    `platformdirs.user_data_path("Evrakci", appauthor=False) / "models"`
  - `official_model(version: str, kind: str, key: str) -> ModelFile`: read from rapidocr's
    `default_models.yaml` (`onnxruntime[version][kind][key]`)
  - `ensure_model(model: ModelFile, download: bool = True) -> Path`
    - uses an existing file whose sha256 matches
    - otherwise downloads to `<name>.part`, verifies, and renames
    - raises `EngineUnavailable` on a mismatch or a failed download, and never keeps a
      mismatched file
- Produces, in `ocr/rapid.py`:
  - `class RapidOcrEngine`, constructed as `RapidOcrEngine(rec_key: str =
    "latin_PP-OCRv5_rec_mobile", rec_version: str = "PP-OCRv5", name: str = "rapidocr-v5-latin")`
  - `available() -> str | None`
  - `read_page` and `read_region` (same contract as Task 1)
- The engine uses detection `ch_PP-OCRv5_det_mobile` (PP-OCRv5) with the angle classifier
  turned off.
- Word boxes: RapidOCR returns line boxes. If the result carries word results, use them;
  otherwise split each line box evenly by character count across its words.

- [ ] **Step 1: Write the failing tests**

```python
def test_checksum_mismatch_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("EVRAKCI_MODEL_DIR", str(tmp_path))
    model = ModelFile("x", "https://invalid.invalid/x.onnx", "0" * 64, "x.onnx")
    (tmp_path / "x.onnx").write_bytes(b"wrong")
    with pytest.raises(EngineUnavailable):
        ensure_model(model, download=False)
    assert not (tmp_path / "x.onnx").exists()

def test_official_model_has_checksum():
    m = official_model("PP-OCRv5", "rec", "latin_PP-OCRv5_rec_mobile")
    assert len(m.sha256) == 64 and m.file_name == "latin_PP-OCRv5_rec_mobile.onnx"

@needs_rapidocr
def test_reads_region():
    reading = RapidOcrEngine().read_region(render_line("Şişli Çağrı Öğün 2026"))
    assert "2026" in reading.text and reading.confidence > 0.5

@needs_rapidocr
def test_page_words_have_boxes():
    words = RapidOcrEngine().read_page(render_line("Kayıt 2026"))
    assert len(words) == 2 and words[0].box[2] <= words[1].box[0] + 5
```

  `test_official_model_has_checksum` is skipped (`importorskip("rapidocr")`) when the extra isn't
  installed.

- [ ] **Step 2: Run the tests to make sure they fail**: `ModuleNotFoundError`
- [ ] **Step 3: Implement.** `needs_rapidocr` skips when `RapidOcrEngine().available()` is not
  None.
- [ ] **Step 4: Run the tests**: 4 passed (or skipped without the extra), and ruff is clean.
- [ ] **Step 5: Commit**: `feat: RapidOCR engine with checksum-verified models`

---

### Task 3: Synthetic test pages and metrics

**Files:**
- Create: `src/evrakci/pipeline/ocr/synthetic.py`, `src/evrakci/pipeline/ocr/metrics.py`
- Test: `tests/test_ocr_metrics.py`, `tests/test_ocr_synthetic.py`

**Interfaces:**
- Produces, in `ocr/metrics.py`:
  - `TURKISH_CHARS = "ıiİIşŞğĞçÇöÖüÜ"`
  - `normalize(text: str) -> str`: NFC, whitespace collapsed, stripped. No case change, ever.
  - `edit_ops(truth: str, read: str) -> list[tuple[str, str | None, str | None]]`: Levenshtein
    alignment with backtrace. Ops are `("eq"|"sub"|"del"|"ins", truth_char, read_char)`.
  - `cer(truth, read) -> float`: edits divided by `max(len(truth), 1)`, after normalize
  - `turkish_char_errors(truth, read) -> tuple[int, int]`: `(wrong, total)`, counting truth chars
    in `TURKISH_CHARS` whose aligned op is not `eq`
  - `exact(truth, read) -> bool`: after normalize
  - `box_hit(truth_box, read_box) -> bool`: the center of `read_box` lies inside `truth_box`
- Produces, in `ocr/synthetic.py`:
  - `find_font(serif: bool = False) -> Path`: tries DejaVu and Liberation on Linux, Arial and Times
    on Windows, and Helvetica on macOS; raises `FileNotFoundError` otherwise
  - `@dataclass(frozen=True) class TruthBox: text: str; box: tuple[int, int, int, int]`
  - `@dataclass class SyntheticPage: image: Image; fields: list[TruthBox]; words: list[TruthBox]`
  - `make_pages(count: int, seed: int = 0, dpi: int = 300, degrade: bool = True) ->
    list[SyntheticPage]`
    - A4 grayscale, deterministic for a seed.
    - Each page has 8–12 single-line **fields**, built from random Turkish syllables plus digits,
      dashes and dots, at least half containing a char from `TURKISH_CHARS`, in mixed case.
      Fields use sans or serif at 9–14 pt.
    - Each field box is its text bbox padded by 2 mm.
    - `words` holds each word's own box.
    - `degrade` adds about 0.7° rotation of the page content, gaussian noise (σ 8), a slight blur
      (radius 0.6) and a JPEG round-trip at quality 60. Boxes are rotated with the content.
- These are benchmark generators, not document kinds. The syllables and words are invented.

- [ ] **Step 1: Write the failing tests**

```python
def test_turkish_case_never_folded():
    assert not exact("İstanbul", "istanbul") and not exact("ığdır", "iğdir")
    assert turkish_char_errors("ığdır", "iğdir") == (2, 3)  # ı, ğ, ı counted; both ı read as i
def test_nfc():
    assert exact("İ", "İ")
def test_empty_reading():
    assert cer("abc", "") == 1.0 and not exact("abc", "") and cer("", "") == 0.0
def test_cer_counts_edits():
    assert cer("Çağrı", "Cagri") == pytest.approx(3 / 5)
def test_box_hit():
    assert box_hit((0, 0, 10, 10), (4, 4, 8, 8)) and not box_hit((0, 0, 10, 10), (12, 0, 20, 5))
def test_pages_deterministic_and_rich_in_turkish():
    a, b = make_pages(2, seed=7), make_pages(2, seed=7)
    assert [f.text for f in a[0].fields] == [f.text for f in b[0].fields]
    fields = [f for p in a for f in p.fields]
    assert sum(any(c in TURKISH_CHARS for c in f.text) for f in fields) * 2 >= len(fields)
    assert a[0].image.size == (2480, 3508)
```

- [ ] **Step 2: Run the tests to make sure they fail**: `ModuleNotFoundError`
- [ ] **Step 3: Implement** both modules. Rotate the boxes by transforming their corners and taking
  the bounding box.
- [ ] **Step 4: Run the tests**: all pass, and ruff is clean.
- [ ] **Step 5: Commit**: `feat: synthetic Turkish test pages and OCR metrics`

---

### Task 4: Comparison runner and report

**Files:**
- Create: `src/evrakci/pipeline/ocr/compare.py`
- Test: `tests/test_ocr_compare.py`

**Interfaces:**
- Consumes: engines (Tasks 1–2), `make_pages` and metrics (Task 3)
- Produces:
  - `@dataclass class EngineResult`, with fields:
    - `name: str`
    - `unavailable: str | None`
    - `fields: int`
    - `exact: int`
    - `cer: float` (mean)
    - `tr_wrong: int`, `tr_total: int`
    - `page_seconds: float` (mean, from `read_page`)
    - `aligned: int`, `words: int` (truth words with a read word whose center hits them)
    - `samples: list[tuple[str, str]]` (the first 15 wrong `(truth, read)` pairs)
  - `compare_synthetic(engines: Sequence[OcrEngine], pages: Sequence[SyntheticPage]) ->
    list[EngineResult]`. Regions are cropped from the page with the field box.
  - `install_sizes() -> dict[str, int]`: bytes for the tesseract binary dir plus `tur` and
    `tur_best` data, and for the onnxruntime, rapidocr and opencv packages plus the model files,
    each counted only when present
  - `render_report(results, sizes, title: str, notes: list[str]) -> str`: Turkish Markdown with
    - a summary table (engine, exact %, CER %, Turkish-char error %, s/page, aligned %, size MB)
    - a "Hatalı okumalar" section per engine
    - the notes
- An unavailable engine still appears, as one row marked `kullanılamıyor: {reason}`.

- [ ] **Step 1: Write the failing tests.** They use a fake engine class in the test file that reads
  the truth back exactly, and a broken one that is unavailable.

```python
def test_perfect_engine_scores_full(fake_pages):
    [r] = compare_synthetic([PerfectEngine(fake_pages)], fake_pages)
    assert r.exact == r.fields and r.cer == 0 and r.tr_wrong == 0 and r.aligned == r.words

def test_unavailable_engine_listed(fake_pages):
    results = compare_synthetic([Unavailable()], fake_pages)
    assert results[0].unavailable == "yok" and "kullanılamıyor: yok" in render_report(results, {}, "T", [])

def test_report_has_table(fake_pages):
    text = render_report(compare_synthetic([PerfectEngine(fake_pages)], fake_pages), {}, "Başlık", ["not"])
    assert "| Motor |" in text and "100.0" in text and "not" in text
```

- [ ] **Step 2: Run the tests to make sure they fail**
- [ ] **Step 3: Implement.** Engines are probed with `available()` before use (the protocol gets a
  default `available()` returning `None`).
- [ ] **Step 4: Run the tests**: they pass, and ruff is clean.
- [ ] **Step 5: Commit**: `feat: OCR comparison runner and Markdown report`

---

### Task 5: `evrakci ocr-karsilastir` and real-scan mode

**Files:**
- Create: `src/evrakci/cli/ocr.py`
- Modify: `src/evrakci/cli/main.py` (register the commands)
- Test: `tests/test_cli_ocr.py`

**Interfaces:**
- `evrakci ocr-karsilastir --sentetik N [--tohum S] --cikti RAPOR.md`
  - runs every engine the code knows (`tesseract-tur`, `tesseract-tur_best`, `rapidocr-v5-latin`,
    `rapidocr-v6-multi`) on N synthetic pages
  - writes the report and prints its path
- `evrakci ocr-karsilastir PDF [PDF ...] [--kutular KUTULAR.json] --cikti RAPOR.md`
  - This is the real-scan mode, run on the owner's PC.
  - Each page is rendered at 300 dpi and every engine reads the full page. The report gives
    seconds per page and, per page, each engine's first 400 characters side by side.
  - With `--kutular`, it also scores boxes. The JSON is a list of `{"pdf": "a.pdf", "sayfa": 1,
    "kutu_mm": [x0, y0, x1, y1], "beklenen": "..."}`. Millimetres map to pixels through the page's
    real size (`page.get_size()` in points); `beklenen` is optional (no score without it).
- `evrakci ocr-modelleri-indir`: downloads and verifies the RapidOCR models and `tur_best` into the
  app data folder, printing one line per file (`hazır` / `indirildi` / `hata: ...`).
- Exit code 2 with a Turkish message on a missing file, a bad JSON file or a bad box.

- [ ] **Step 1: Write the failing tests**

```python
@needs_tesseract
def test_synthetic_report(tmp_path, capsys):
    out = tmp_path / "r.md"
    assert main(["ocr-karsilastir", "--sentetik", "1", "--cikti", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "tesseract-tur" in text and "| Motor |" in text

@needs_tesseract
def test_real_mode_with_boxes_in_mm(tmp_path):
    page = render_line("Örnek Kayıt 2026")          # placed at a known spot on an A4 page
    pdf = make_pdf(tmp_path / "a.pdf", [a4_with(page, at_mm=(20, 30))])
    boxes = tmp_path / "k.json"
    boxes.write_text(json.dumps([{"pdf": "a.pdf", "sayfa": 1,
        "kutu_mm": [18, 28, 140, 45], "beklenen": "Örnek Kayıt 2026"}]), encoding="utf-8")
    out = tmp_path / "r.md"
    assert main(["ocr-karsilastir", str(pdf), "--kutular", str(boxes), "--cikti", str(out)]) == 0
    assert "Örnek Kayıt 2026" in out.read_text(encoding="utf-8")

def test_bad_boxes_file(tmp_path, capsys):
    pdf = make_pdf(tmp_path / "a.pdf", [text_page()])
    bad = tmp_path / "k.json"; bad.write_text("{", encoding="utf-8")
    assert main(["ocr-karsilastir", str(pdf), "--kutular", str(bad), "--cikti", str(tmp_path / "r.md")]) == 2
    assert "Kutu dosyası okunamadı" in capsys.readouterr().err
```

  `a4_with(image, at_mm)` is added to `fakes.py` (pastes onto a 100 dpi A4 page).

- [ ] **Step 2: Run the tests to make sure they fail**
- [ ] **Step 3: Implement**
- [ ] **Step 4: Run the whole suite**: `pytest -q && ruff check .` passes.
- [ ] **Step 5: Commit**: `feat: evrakci ocr-karsilastir command`

---

### Task 6: Run the comparison, write the report, update docs

**Files:**
- Create: `docs/ocr-motor-karsilastirma.md` (the report, plus a short Turkish summary and
  recommendation at the top)
- Create: `docs/ocr-gercek-tarama-testi.md` (Turkish how-to for the owner's PC)
  - install Tesseract and the Turkish data on Windows
  - `pip install -e ".[rapidocr]"`, then `evrakci ocr-modelleri-indir`
  - run `ocr-karsilastir` on a few real scans, with a sample `kutular.json`
  - a reminder never to commit real scans or their reports
- Modify: `docs/dependency-licenses.md` (rapidocr, onnxruntime, opencv-python-headless, and their
  small dependencies: shapely, pyclipper, omegaconf, PyYAML, tqdm, colorlog, six, requests; the
  PaddleOCR model weights are Apache-2.0); `.github/workflows/ci.yml` (install
  `tesseract-ocr tesseract-ocr-tur`)

- [ ] **Step 1:** Run
  `evrakci ocr-karsilastir --sentetik 20 --tohum 1 --cikti docs/ocr-motor-karsilastirma.md`. Then
  run it again with `--tohum 2` and `degrade` both on and off, for a clean vs. scanned-looking
  note. Expected: the report is written with all available engines.
- [ ] **Step 2:** Add the summary and recommendation, write the how-to, and update the licenses and
  CI.
- [ ] **Step 3:** `pytest -q && ruff check .` passes.
- [ ] **Step 4: Commit**: `docs: OCR engine comparison report and real-scan guide`
- [ ] **Step 5:** The final whole-plan review, then **STOP**. Show the owner the results and ask
  them to pick the engine.
