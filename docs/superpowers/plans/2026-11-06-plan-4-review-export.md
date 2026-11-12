# Plan 4: Review and Export. Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:**
- Staff list and fix read values from the CLI.
- Export then writes each document under a name built from the template's pattern, plus an
  `index.xlsx` that says exactly which files need checking and why.
- A retention setting can delete job files after export, or after N days.

**Architecture:**
- `pipeline/naming.py` is pure: it makes safe Windows file names, builds names from patterns, and
  numbers clashes.
- `pipeline/export.py` turns a job plus its templates into an export plan (name, values and
  "needs check" reasons per document), and writes the PDFs and the index through the existing
  writer and text-layer code.
- `pipeline/index.py` writes `index.xlsx` with openpyxl.
- `pipeline/settings.py` holds app settings, including retention.

**Tech Stack:** openpyxl (MIT, already a dependency), pikepdf, the Plan 2b text layer, the Plan 3
templates.

**Spec:** `docs/superpowers/specs/2026-11-06-scan-and-split-design.md` §6.5, §7

## Global Constraints

- **Windows-safe names**:
  - remove `<>:"/\|?*` and control characters
  - collapse whitespace
  - strip trailing dots and spaces
  - add `_` to reserved names (CON, PRN, AUX, NUL, COM1–9, LPT1–9, in any case)
  - limit the name to 120 characters before `.pdf`
  - **Turkish letters are kept**
- **A required variable that is missing or flagged is never put in a name.**
  - The document gets `belge_NNN.pdf` (NNN = its document number) and is marked
    `zorunlu değer eksik: {ad}`.
  - Flagged optional variables are left out of the name (`{name}` becomes empty), and are marked
    as well.
- Separators that become doubled by an empty optional value (`_`, `-`, `.`, space) are collapsed,
  and leading or trailing ones are stripped. A name that ends up empty falls back to `belge_NNN`.
- Clashing names get ` (2)`, ` (3)`, … in document order.
- Documents without a template, or whose template has no pattern, are named `belge_NNN.pdf`.
- Export refuses a folder that already holds any target file or `index.xlsx`, and writes nothing.
- **Needs-check reasons**, one per line in the index's "Kontrol" column:
  - `eksik sayfa`
  - `karışık şablon`
  - `şablon bulunamadı`
  - `okunamadı: {ad}`
  - `zorunlu değer eksik: {ad}`
  - `PDF/A değil: {not}`
  - `değerler okunmadı`
- Retention values:
  - `sakla` (the default; nothing is ever deleted automatically)
  - `disa-aktarinca-sil` (delete the job after a fully successful export)
  - a whole number of days N (delete jobs whose `job.json` is older than N days, checked when
    `is listele` or `is olustur` runs)
- Settings are stored in `<app data>/settings.json` (UTF-8). The core never imports Qt; the CLI is
  in Turkish; commits are authored by ZackHaronOriginal with no Claude lines; ruff and pytest pass.

## Review Focus

1. **Turkish names on Windows**: `İ`, `ı` and combining characters, normalized to NFC, so the
   same company never produces two different file names. Test in Task 1.
2. **Re-exporting after fixing values**: a new empty folder works; the same folder is refused with
   a clear message. Test in Task 4.
3. **Values for a document whose cuts changed after reading** (the first page id no longer starts
   a document). Those values are not shown or used; the document reports `değerler okunmadı`. Test
   in Task 3.
4. **Retention never deletes a job that is mid-export or was edited recently.** Only `job.json`'s
   modification time counts, and `disa-aktarinca-sil` deletes only after every file is written.
   Test in Task 6.
5. **An index cell starting with `=`, `+`, `-` or `@`** (an OCR'd value) must not become a formula
   in Excel. It is written as text. Test in Task 5.

---

### Task 1: Safe names from patterns

**Files:** Create `src/evrakci/pipeline/naming.py`. Test `tests/test_naming.py`.

**Interfaces:**
- `safe_filename(text: str) -> str` (NFC; the rules above; may return `""`)
- `build_name(pattern: str, values: Mapping[str, VariableValue], required: set[str]) ->
  tuple[str | None, list[str]]`
  - returns the name without `.pdf`, plus the check reasons
  - returns `None` when a required value is missing or flagged
- `unique_names(names: Sequence[str]) -> list[str]` (adds ` (2)`… to clashes, compared
  case-insensitively, as Windows does)

- [ ] **Steps:**
  - Tests:
    - `test_windows_forbidden_and_reserved`: `'A/B:C*?"<>|'`, `"CON"`, `"nul.txt"`, trailing dots
    - `test_turkish_kept_and_nfc`: `"İ"` vs `"İ"` give the same name
    - `test_long_name_cut`
    - `test_required_missing_gives_none`
    - `test_flagged_optional_left_out_and_separators_collapsed`: `"{A}_{B}_{C}"` with B flagged
      gives `"a_c"` plus the reason `okunamadı: B`
    - `test_unique_names_case_insensitive`: `["Örnek", "örnek", "Örnek"]` gives
      `["Örnek", "örnek (2)", "Örnek (3)"]`
  - Watch them fail, implement, watch them pass.
  - Commit `feat: safe file names from template patterns`

### Task 2: Writer with chosen names

**Files:** Modify `src/evrakci/pipeline/writer.py`. Test `tests/test_writer.py`.

**Interfaces:**
- `write_documents(..., names: Sequence[str] | None = None)` (names without `.pdf`; default is
  `belge_NNN`)
- The conflict check refuses if **any** target file, or `index.xlsx`, already exists, raising
  `FileExistsError` with the first clash's name.
- [ ] **Steps:**
  - Tests:
    - `test_custom_names`
    - `test_conflict_on_any_target_or_index`
  - Commit `feat: writer uses chosen names and checks every target`

### Task 3: Listing and fixing values

**Files:** Create `src/evrakci/pipeline/review.py`; modify `src/evrakci/cli/jobs.py`. Test
`tests/test_review.py`, `tests/test_cli_values.py`.

**Interfaces:**
- `document_values(job, document) -> dict[str, VariableValue] | None`: values only when they were
  read for exactly this document. They are stored under its first page id, along with the
  document's page tuple: `Job.value_pages[first] = tuple(page_ids)`.
  - `is oku` records `value_pages`.
  - Job format stays version 2, with the optional key `value_pages`.
- `set_value(job, first_pid, name, text)`: `edited=True`, `flagged=False`, `value=text` (NFC,
  trimmed)
- `accept_suggestion(job, first_pid, name)`
- CLI:
  - `is degerler ID [--kontrol]`
    - one block per templated document: `{n}. belge ({şablon}) sayfa …`
    - then `  {AD}: {değer}` lines, marked `[okunamadı, öneri: …]` or `[düzeltildi]`
    - `--kontrol` shows only documents needing a check
  - `is deger ID BELGE AD (DEGER | --oneri)`
    - `BELGE` is the document number from `is goster`
    - unknown document, variable, or a document with no values gives a Turkish error, exit 2
- [ ] **Steps:**
  - Tests:
    - `test_values_dropped_when_cuts_change`
    - `test_set_value_and_accept_suggestion`
    - `test_cli_list_and_fix`
    - `test_cli_errors`
  - Commit `feat: list and fix read values`

### Task 4: Export plan with names and checks

**Files:** Create `src/evrakci/pipeline/export.py`; modify `src/evrakci/cli/jobs.py`
(`disa-aktar`). Test `tests/test_export.py`, `tests/test_cli_edit.py`.

**Interfaces:**
- `@dataclass class ExportItem`, with fields:
  - `number: int`
  - `document: Document`
  - `name: str`
  - `template_name: str | None`
  - `values: dict[str, VariableValue]`
  - `checks: list[str]`
  - `pdfa: bool | None = None`
- `plan_export(job, templates: Mapping[str, Template | None]) -> list[ExportItem]`: names are made
  unique in document order
- `is disa-aktar` uses the plan:
  1. writes the PDFs under the planned names
  2. adds the text layer, appending `PDF/A değil: …` to the checks
  3. writes `index.xlsx` (Task 5)
  4. prints `{dosya}: sayfa … [kontrol: …]`
  5. prints a final line: `{n} belge yazıldı, {k} belge kontrol gerektiriyor. Liste: index.xlsx`
- [ ] **Steps:**
  - Tests:
    - `test_plan_names_and_checks`: a templated job with fake values, covering a required value
      missing, an optional value flagged, a clash, and an untemplated document
    - `test_plan_template_missing`
    - `@needs_tesseract test_cli_export_with_template_names`
    - `test_reexport_same_folder_refused`
  - Commit `feat: export named documents with check reasons`

### Task 5: `index.xlsx`

**Files:** Create `src/evrakci/pipeline/index.py`. Test `tests/test_index.py`.

**Interfaces:**
- `write_index(items: Sequence[ExportItem], job: Job, path: Path) -> None`
- The sheet is named `Belgeler`. Columns:
  1. `Dosya`
  2. `Sayfa sayısı`
  3. `Kaynak sayfalar` (positions, comma-separated)
  4. `Şablon`
  5. `PDF/A` (`evet` / `hayır`)
  6. `Kontrol gerekli` (`evet` / `hayır`)
  7. `Kontrol nedenleri` (newline-joined)
  8. then one column per variable name, as the union in order of first appearance
- The header is bold and frozen, columns are auto-width (capped at 60), and rows that need a check
  get a light fill.
- Every value cell is written as **text** (`cell.data_type = "s"`, with `number_format = "@"`),
  so OCR'd text starting with `=` or `+` never becomes a formula.
- [ ] **Steps:**
  - Tests:
    - `test_columns_and_rows`
    - `test_formula_like_values_are_text`: reopen with openpyxl; `cell.data_type == "s"` and the
      value starts with `=`
    - `test_turkish_headers_and_values`
  - Commit `feat: index.xlsx with check reasons`

### Task 6: Retention setting

**Files:** Create `src/evrakci/pipeline/settings.py`; modify `src/evrakci/pipeline/store.py`,
`src/evrakci/cli/main.py`, `src/evrakci/cli/jobs.py`. Test `tests/test_retention.py`.

**Interfaces:**
- `@dataclass class Settings: retention: str = "sakla"` (`"sakla"`, `"disa-aktarinca-sil"`, or a
  digit string)
- `load_settings(path=None) -> Settings` and `save_settings(settings, path=None)` (default
  `data_dir()/"settings.json"`, overridable by `EVRAKCI_AYARLAR`)
- `JobStore.delete_older_than(days: int, now: float | None = None) -> list[str]`: uses
  `job.json`'s mtime
- CLI:
  - `evrakci ayar saklama (sakla | disa-aktarinca-sil | GUN)`
  - `evrakci ayar goster`
  - `is listele` and `is olustur` apply the day limit first and print
    `Saklama süresi doldu, silindi: {id}` to stderr
  - `is disa-aktar` with `disa-aktarinca-sil` deletes the job only after every file and the index
    are written, and prints `İş silindi (saklama ayarı): {id}`
- [ ] **Steps:**
  - Tests:
    - `test_settings_round_trip_and_validation`
    - `test_delete_older_than_uses_mtime`
    - `test_delete_after_export_only_on_success`: a failing export keeps the job
    - `test_default_keeps_everything`
  - Commit `feat: retention setting`

### Task 7: Docs

README (both languages): review and export, `index.xlsx`, and retention.
`docs/architecture.md`. Commit `docs: review, export and retention`.
