# Plan 3: Templates and Reading Variables. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Users create templates with their own named variables. Each variable has one or more
sections (a page plus a box), and each extra section is a variant. Users apply templates to pages
of a job, and the app reads every templated document's variables with OCR. It all works from the
CLI.

**Architecture:**
- `pipeline/templates/` holds three things:
  - the template model: plain data and JSON, with no built-in fields
  - a template store (one JSON file per template, plus import and export)
  - the reader, which tries sections in the user's order through the OCR engine interface
- `Job` gains template applications, plus the values read per document. Its format becomes
  version 2, and it migrates version 1 automatically.
- `pipeline/render.py` renders a job page at 300 dpi with rotation, and is shared with the window
  later.

**Tech Stack:** Python dataclasses + JSON, pypdfium2, the Plan 2 OCR engines (`default_engine()`
= Tesseract + tur_best).

**Spec:** `docs/superpowers/specs/2026-11-06-scan-and-split-design.md` §4.6, §6.2–6.5

## Global Constraints

- **The code has no built-in fields, field types, suggested variable names or document kinds.**
  - A variable name is any text the user types, trimmed, non-empty, without `{` or `}`. Names are
    unique within a template; Turkish letters and spaces are allowed.
  - The only demo content anywhere is a synthetic template in tests.
- A file-name pattern may only reference the template's own variables, as `{name}`. Literal text
  between them is allowed.
- Boxes are in **millimetres from the top-left of the page as displayed**, in the order
  `x0, y0, x1, y1`, with `x0 < x1` and `y0 < y1`. Pixels are 300 dpi renders.
- Section page: an `int`. `1, 2, …` counts from the document's first page; `-1` is the last page,
  `-2` the one before it.
- A reading is **confident** when its text is not empty and `confidence >= template.min_confidence`.
  The default is `0.70`, settable per template.
  - Sections are tried in list order, and the first confident one wins.
  - If none is confident: `flagged=True`, `value=""`, `suggestion` = the best non-empty reading,
    and every reading is kept.
- The last-applied template wins on overlapping pages. A document's template is that of its
  **first** page. If its pages carry different templates, the document is flagged
  `"mixed_templates"`.
- Job JSON `version: 2`, and version 1 files load unchanged with empty template data.
- Core never imports Qt; CLI text is Turkish; commits are authored by ZackHaronOriginal with no
  Claude lines.
- `ruff check .` and `pytest -q` pass before each commit.

## Review Focus

1. **Turkish variable names and file-name patterns** (`{Ünvan}`, `{Kayıt No}`), round-tripped
   through JSON, export and import on Windows (UTF-8 always, never the locale encoding). Tests in
   Tasks 1–2.
2. **A section page beyond the document's length** (page 3 on a 2-page document, or `-3`). It is
   skipped as "sayfa yok" in the readings, without crashing. Test in Task 4.
3. **Renaming a variable** updates the file-name pattern and stored values, and never leaves a
   dangling `{old}`. Test in Tasks 1 and 6.
4. **A template deleted while a job still refers to it.** Reading reports `Şablon bulunamadı` for
   those documents and continues with the others. Test in Task 7.
5. **A box partly outside the rendered page** (a section made on a Letter example, used on A4). It
   is clipped to the page, and a box entirely outside reads as empty. Test in Task 4.

---

### Task 1: Template model and validation

**Files:** Create `src/evrakci/pipeline/templates/__init__.py`, `src/evrakci/pipeline/templates/model.py`.
Test `tests/test_template_model.py`.

**Interfaces:**
- `@dataclass(frozen=True) class Section: page: int; box_mm: tuple[float, float, float, float];
  example: str | None = None` (the example document's file name, for information)
- `@dataclass class Variable: name: str; sections: list[Section]; required: bool = False`
- `@dataclass class Template: id: str; name: str; variables: list[Variable];
  filename_pattern: str = ""; min_confidence: float = 0.70; keywords: list[str]` (the keywords are
  reserved for later template guessing, and unused now)
- `class TemplateError(ValueError)` (Turkish message)
- Methods on `Template`:
  - `variable(name) -> Variable`
  - `add_variable(name, required=False)`
  - `remove_variable(name)`: also removes `{name}` from the pattern
  - `rename_variable(old, new)`: also rewrites `{old}` to `{new}` in the pattern
  - `set_required(name, bool)`
  - `add_section(name, section)`
  - `remove_section(name, index)`
  - `move_section(name, index, new_index)`
  - `set_pattern(pattern)`
  - `set_min_confidence(value)` (`0 < value <= 1`)
- `pattern_names(pattern) -> list[str]` (the names inside `{}` in order; raises on unbalanced
  braces)
- `validate_name(name) -> str` (returns the trimmed name, raises `TemplateError`)
- `template_to_dict`, `template_from_dict` (`"format": "evrakci-sablon", "version": 1`)

- [ ] **Step 1: Write the failing tests:**
  - `test_turkish_names_round_trip`: `{Ünvan}` and `{Kayıt No}`, through JSON with
    `ensure_ascii=False`
  - `test_pattern_only_known_variables`: `set_pattern("{Yok}")` raises, with the message
    containing `Yok`
  - `test_rename_updates_pattern`
  - `test_remove_variable_strips_from_pattern`
  - `test_bad_names`: `""`, `"a{b"`, a duplicate
  - `test_bad_box`: `x0 >= x1`
  - `test_section_order_ops`
  - `test_unknown_format_rejected`
- [ ] **Step 2: Run the tests to make sure they fail**
- [ ] **Step 3: Implement**
- [ ] **Step 4: Run the tests**: they pass, and ruff is clean.
- [ ] **Step 5: Commit**: `feat: template model with user-named variables and sections`

### Task 2: Template store, import and export

**Files:** Create `src/evrakci/pipeline/templates/store.py`. Test `tests/test_template_store.py`.

**Interfaces:**
- `default_template_root() -> Path`: `data_dir() / "templates"`
- `class TemplateStore`, constructed as `TemplateStore(root: Path)`. Methods:
  - `create(name) -> Template` (id `uuid4().hex[:10]`)
  - `save(t)` (atomic, UTF-8)
  - `load(id)` (`KeyError` if missing; `TemplateError` "Şablon dosyası okunamadı: {id}" if
    corrupt)
  - `list(on_error=None) -> list[Template]` (sorted by name, Turkish-aware via `casefold`)
  - `delete(id)`
  - `export(id, path)`
  - `import_file(path) -> Template`: gives a new id when the id already exists, keeps the name,
    and appends ` (2)` if a template with that name already exists
- [ ] **Steps 1–5:**
  - Tests:
    - `test_create_save_load_list`
    - `test_export_import_keeps_turkish`, which reads the exported file bytes as UTF-8
    - `test_import_clash_gets_new_id_and_name`
    - `test_corrupt_file_reported`
  - Watch them fail, implement, watch them pass, commit `feat: template store with import and
    export`.

### Task 3: Rendering job pages

**Files:** Create `src/evrakci/pipeline/render.py`. Test `tests/test_render.py`.

**Interfaces:**
- `render_page(batch_file: Path, index: int, rotation: int = 0, dpi: int = 300) -> Image`
  (grayscale `L`; applies the PDF's own `/Rotate`, then the user's extra rotation clockwise)
- `mm_box_to_pixels(box_mm, size, dpi=300) -> tuple[int, int, int, int]`: clipped to the
  image; returns `None` when the box lies wholly outside
- [ ] **Steps 1–5:**
  - Tests:
    - `test_rotation_applied`: a portrait page with rotation 90 renders landscape
    - `test_box_clipped`
    - `test_box_outside_is_none`
  - Commit `feat: render job pages and convert boxes`

### Task 4: Reading a document with a template

**Files:** Create `src/evrakci/pipeline/templates/read.py`. Test `tests/test_template_read.py`.

**Interfaces:**
- `@dataclass(frozen=True) class SectionReading: section: int; text: str; confidence: float;
  problem: str | None = None` (`problem` is `"sayfa yok"` or `"kutu sayfa dışında"`)
- `@dataclass(frozen=True) class VariableValue`, with fields:
  - `value: str`
  - `confidence: float`
  - `section: int | None`
  - `flagged: bool`
  - `suggestion: str`
  - `readings: tuple[SectionReading, ...]`
  - `edited: bool = False`
- `read_document(template: Template, page_count: int, page_image: Callable[[int], Image],
  engine: OcrEngine) -> dict[str, VariableValue]`
  - `page_image(i)` takes a 0-based index within the document
  - images are cached per page inside one call
- [ ] **Steps 1–5:**
  - Tests use a fake engine mapping crop size to `(text, conf)`, and synthetic pages:
    - `test_first_confident_variant_wins`: variant 1 low confidence, variant 2 confident →
      section 1 is chosen
    - `test_none_confident_flagged_with_suggestion`
    - `test_last_page_and_missing_page`: page `-1`, and page 3 of 2 gives "sayfa yok"
    - `test_box_outside_page`
    - `@needs_tesseract test_real_tesseract_reads_box`, with `render_line` pasted at a known mm
      position
  - Commit `feat: read template variables with ordered variants`

### Task 5: Templates in jobs (format v2)

**Files:** Modify `src/evrakci/pipeline/job.py`, `src/evrakci/pipeline/cuts.py`. Test
`tests/test_job_templates.py`.

**Interfaces:**
- `@dataclass(frozen=True) class TemplateApplication: template_id: str; page_ids: frozenset[str]`
- New `Job` fields:
  - `templates: list[TemplateApplication]`
  - `values: dict[str, dict[str, VariableValue]]` (keyed by the document's first page id)
  - `read_errors: dict[str, str]` (also keyed by first page id)
- `Job.apply_template(page_ids, template_id)`
- `document_template(job, document) -> tuple[str | None, bool]`: the template id, and whether
  it's mixed
- `compute_documents` adds the flag `"mixed_templates"`
- `JOB_FORMAT_VERSION = 2`; `job_from_dict` accepts 1 (empty template data) and 2
- [ ] **Steps 1–5:**
  - Tests:
    - `test_last_applied_template_wins`
    - `test_first_page_template_and_mixed_flag`
    - `test_v1_job_loads`
    - `test_values_round_trip`
  - Commit `feat: templates and read values in jobs`

### Task 6: `evrakci sablon` commands

**Files:** Create `src/evrakci/cli/templates.py`; modify `src/evrakci/cli/main.py` (adds global
`--sablon-kok DIR`). Test `tests/test_cli_templates.py`.

**Interfaces:** every command prints one Turkish confirmation line, and user errors exit with 2.
`ID` is the template id; names containing spaces are quoted.

| Command | Does |
|---|---|
| `sablon olustur AD` | prints the new id on its last line |
| `sablon listele` | `{id}  {ad}  {n} değişken` |
| `sablon goster ID [--json]` | variables, sections (sayfa, kutu mm, örnek), required flag, pattern, threshold |
| `sablon sil ID` | deletes the template |
| `sablon degisken-ekle ID AD [--zorunlu]` | adds a variable |
| `sablon degisken-sil ID AD` | removes a variable |
| `sablon degisken-adlandir ID ESKI YENI` | renames a variable |
| `sablon zorunlu ID AD (evet\|hayir)` | sets whether it is required |
| `sablon bolum-ekle ID AD --sayfa N --kutu x0,y0,x1,y1 [--ornek DOSYA.pdf]` | appends a variant; `--sayfa son` = `-1` |
| `sablon bolum-sil ID AD SIRA` | removes a variant (1-based) |
| `sablon bolum-tasi ID AD SIRA YENI_SIRA` | moves a variant (1-based) |
| `sablon dosya-adi ID KALIP` | sets the file-name pattern |
| `sablon esik ID DEGER` | sets the confidence threshold |
| `sablon disa-aktar ID DOSYA` | exports one file |
| `sablon ice-aktar DOSYA` | imports; prints the new id |

- [ ] **Steps 1–5:**
  - Tests:
    - `test_create_edit_show`: a full session, with Turkish names and spaces
    - `test_rename_variable_updates_pattern`
    - `test_bad_box_and_unknown_variable_errors`
    - `test_export_import_roundtrip`
  - Commit `feat: evrakci sablon commands`

### Task 7: Test a template, apply it, read a job

**Files:** Modify `src/evrakci/cli/templates.py`, `src/evrakci/cli/jobs.py`. Test
`tests/test_cli_template_read.py`.

**Interfaces:**
- `sablon test ID ORNEK.pdf`
  - reads the example as one document
  - per variable, prints `{AD}: "{değer}" (bölüm N, güven %)`, or `{AD}: OKUNAMADI`, then each
    variant's reading indented
- `is sablon-uygula ID BAS-SON SABLON_ID`: checks that the template exists, then records the
  application
- `is oku ID [--sadece-eksik]`
  - reads every document whose resolved template exists, keeping values the user edited
  - progress goes to stderr
  - prints one summary line per document: `{n}. belge ({şablon}): {AD}=değer, … [kontrol]`
  - a missing template gives `{n}. belge: Şablon bulunamadı: {id}`
  - saves the job
- `is goster` shows each document's template name and a `[kontrol]` mark when anything is flagged
- [ ] **Steps 1–5:**
  - Tests use `needs_tesseract` with synthetic documents: `render_line` text at fixed mm on A4,
    with two layouts, one of them shifted 10 mm down.
    - `test_template_test_command`
    - `test_apply_and_read_with_variants`: the shifted layout is read through variant 2
    - `test_deleted_template_reported`
    - `test_mixed_templates_flagged`
  - Commit `feat: apply templates and read job values`

### Task 8: Docs

README (both languages), with a "Şablonlar" section and an example CLI session;
`docs/architecture.md` (the templates modules and job format v2). Commit
`docs: templates`.
