# Spec group D: Dışa Aktar (I-35, I-38, I-39, I-40)

Status: proposal, waits for the owner's approval (decisions.md, "Owner answers: Phase 5 build order and rules"). D13 is lifted (owner, 2026-11-20): the core may change where the feature is better for it. All examples use invented data. Turkish strings are `draft`: wording follows Windows/Office Turkish terms as remembered ("Baskı önizleme", "Alt bilgi", "Panoya kopyala", "Özet"); I did not check them on the web in this run, so the owner or a Turkish reader should confirm.

**Reconciled with A, B and C (2026-11-20).** Build order, shared pieces and its decisions O-15 to O-19 (all decided by evidence on 2026-11-20, README §6) are in `specs/README.md`. Changes here: the job format stays version 2 for all four specs (C5 is additive, old D-1 is no longer an owner question); dates use one Turkish format, "20.11.2026 14:32", in the sheet and on paper (old D-4 decided); the preview is built off the window thread with `run_background` and its loading card from quick-wins I-47 (no busy cursor); `pdfa_note` (I-40, B-003) is listed with the other `ExportItem` fields.

## Shared core changes (one set, used by all four ideas)

| # | Where | Change | Why |
|---|---|---|---|
| C1 | `pipeline/export.py:21` `ExportItem` | new fields `sources: list[str]` (scan file names of the document's pages, in order, no repeats), `name_note: str` ("" or why the written name differs from the pattern) and `pdfa_note: str` (I-40, B-003: the PDF/A note kept out of `checks`) | I-39 old name and conflict flag; the same text in window, CLI and sheet |
| C2 | `pipeline/export.py` `plan_export` | fills both fields; the "Ad çakışması" and "Geçersiz karakter silindi" logic moves here from `ui/disa_aktar_model.py:110` `_name_change` | one source of truth (the window and the CLI must show the same notes) |
| C3 | `pipeline/exporting.py:61-76` | the "fit names to the folder path" loop becomes `plan_names(job, templates, out_dir) -> list[ExportItem]` (plan_export + fit_names + unique_names + notes); `export_job` calls it | the preview must equal what is written; today the window cannot know "dosya adı kısaltıldı" before export |
| C4 | `pipeline/index.py:39` `write_index` | new columns and two sheets (see I-35, I-40); signature gains `exported_at: datetime | None = None` | one writer for window and CLI |
| C5 | `pipeline/job.py:16` | `JOB_FORMAT_VERSION` stays 2 (one plan for A, C and D: every new job field is additive and read with a default, so older app versions still open newer files). New `Job.last_export: LastExport | None` (`at` ISO text, `folder`, `documents`, `needing_check`); `job_from_dict` (line 259) reads it with `.get`, missing means None. An older app that saves the job drops the field; the print then says "plan" again, never something wrong | I-35 time and I-38 "record, not plan" survive a restart |
| C6 | `cli/jobs.py:258` `export`, `:619` parser | per-file line gets ` [ad: <not>]` when `name_note` is set; new flag `--onizle` (dry run: prints Kaynak, new name, note; writes nothing) | same output as the window list |

Tests for the set (`tests/test_export.py`, `tests/test_exporting.py`, `tests/test_index.py`, new `tests/test_job_format.py`): (a) `plan_names` equals the names `export_job` writes, with a long folder path and a name clash; (b) a version 1 and a version 2 job file without the field open with `last_export=None`; a job with it round-trips and is still written as version 2; (c) the CLI `--onizle` lines equal the window's list rows for the same job (`tests/ui/test_disa_aktar.py`); (d) old `index.xlsx` assertions in `tests/test_index.py:33` are updated for the new first column.

---

## I-35 "Belge no", job name and export time in index.xlsx; document number in the printed list

### 1. Problem
"Sheet rows cannot be tied to numbered file names": a document that fell back to `belge_007.pdf` is row 7 only by counting (Obs. 10). With 300 rows staff count by hand. Serves Never silent.

### 2. Who and when
Staff and supervisors after Dışa Aktar, reconciling the sheet with the folder or the paper list. Every export.

### 3. Keyboard flow
No new key. Ctrl+E exports; "index.xlsx'i aç" (existing action `disa_aktar.index_ac`) opens it. Print: Ctrl+P (see I-38).

### 4. Screen sketch
`Belgeler` sheet, new first column, then the old ones unchanged:

| Belge no | Dosya | Sayfa sayısı | Kaynak sayfalar | Şablon | PDF/A | Kontrol gerekli | Kontrol nedenleri | variables... |
|---|---|---|---|---|---|---|---|---|
| 1 | 101_Örnek.pdf | 2 | 1, 2 | Deneme | evet | hayır | | |
| 7 | belge_007.pdf | 1 | 14 | | evet | evet | değerler okunmadı | |

New second sheet `Özet`: İş adı | Örnek iş; Dışa aktarma zamanı | 20.11.2026 14:32; Belge sayısı | 8; Sayfa sayısı | 21; Kontrol gerekli | 2. Printed list gets a "No" column before "Dosya adı" (same `FileRow.number`). Existing look otherwise.

### 5. Data and core changes
C4: `write_index` inserts "Belge no" (`item.number`, text) first; `_FIXED` (`index.py:16`) gains it; a variable named "Belge no" gets the "(değişken)" mark like the other fixed names. `Özet` sheet from `job.name`, `exported_at` (default `datetime.now()`, plain text "DD.MM.YYYY HH:MM" (same format as the printed footer), through `_set_text`, never a formula). `export_job` (`exporting.py:138`, `:147`) passes one time to both write paths; with C5 the same time is stored in `job.last_export`. Printed list: `index_html` (`disa_aktar.py:1154`) adds the column. CLI prints nothing new. No undo step (no job edit).

### 6. Tests
Core: `tests/test_index.py::test_columns_and_rows` expects the new first column and values; new test: `Özet` holds job name, time (injected `exported_at`), counts equal the list; a variable called "Belge no" is marked. UI: `tests/ui/test_disa_aktar.py` printed HTML has a "No" header and number 7 for `belge_007`. Failure caught: a row that cannot be tied to its file.

### 7. Risks and open questions
Column order changes for people with macros on the sheet (decision D-2). Time is the PC clock, local time, no zone. Row count equals the list count, so never silent.

**Shortcut contract rows it adds:** none.
**Rules it must meet:** AUD-TXT-01 (printed table is not UI, N/A), DEC-IDN-01 (no orange in the sheet except the existing yellow fill for Kontrol rows).
**Performance cost (800 pages, up to 800 documents):** one extra cell per row and one small sheet: under 10 ms. Printed column: none.

**New Turkish text**

| string | where | meaning in English | status |
|---|---|---|---|
| Belge no | index.xlsx column | document number | draft |
| No | printed list column | no. | draft |
| Özet | index.xlsx sheet name | summary | draft |
| İş adı | Özet sheet | job name | draft |
| Dışa aktarma zamanı | Özet sheet | export time | draft |
| Belge sayısı | Özet sheet | number of documents | draft |
| Sayfa sayısı, Kontrol gerekli | Özet sheet | pages, needs check | existing (`index.py:17,21`) |

**Check against the product:** Never silent: Pass. No built-in kinds: Pass. Keyboard: Pass (no new action). Colour: Pass. Layout: Pass (print only). Copy: Pass. Local-first: Pass.

**Owner decisions needed**
- D-1 Decided in the reconcile: store the export in the job file (C5), additive, format stays 2, so nothing is lost for older app versions.
- D-2 (O-15) **Decided by evidence (T3, 2026-11-20; sources in README §6).** "Belge no" is the first column. Evidence: Excel's VLOOKUP needs the key in the first column ("The value you want to look up must be in the first column of the range", Microsoft); the number is the key to the file name. Release note: macros that read index.xlsx by column position must be updated.

**Build steps:** (1) C5 job field (format stays 2) and old-file tests; (2) C4 column and `Özet` sheet; (3) pass one time from `export_job`; (4) printed "No" column; (5) update `test_index.py` and the UI print test.

---

## I-38 Print: repeated header row, footer with date and job name, print preview

### 1. Problem
"A 100-row list loses its header on page 2, has no date, and I see it only on paper" (printing findings 1 and 2). Wasted paper and unmatchable sheets. Serves Never silent and Less paper handling.

### 2. Who and when
Staff filing the printed list, once per export (Dışa Aktar, before or after writing).

### 3. Keyboard flow
Ctrl+P (existing `disa_aktar.yazdir`, `actions.py:181`) now opens "Baskı önizleme" instead of the system dialog. Inside: PgDn / PgUp next / previous page, Ctrl++ / Ctrl+- zoom, Ctrl+0 fit, Enter = "Yazdır…" (opens the system print dialog, then prints), Esc = Kapat; focus returns to the file list. Menu Dosya > "Dizini yazdır…" and palette stay. Mouse: the dialog buttons.

### 4. Screen sketch (dialog, 1366x768, 100 %)
```
Baskı önizleme                                           [x]
[<] Sayfa 1 / 3 [>]   [-] 100 % [+] [Sığdır]        [Yazdır…] [Kapat]
 +------------------------------------------------------+
 | Örnek iş            Dışa aktarma planı, henüz yazılmadı
 | 8 belge, 21 sayfa
 | Durum | No | Dosya adı | Sayfalar | Şablon | Not   <- repeats on every page
 | ...
 | Örnek iş · 20.11.2026 14:32 · Sayfa 1 / 3
 +------------------------------------------------------+
```
A modal `QDialog` (radius 8) holding a `QPrintPreviewWidget`, with our own Turkish buttons: `QPrintPreviewDialog` is not used because Qt's own dialog strings are English (only standard buttons are translated, `app.py:49`, bug B-067). Dialog is at most 1000 x 700 and fits 1366x768; at 150 % the toolbar wraps below the title and the page area scrolls. High contrast: page is white paper by nature, chrome follows the theme.

### 5. Data and core changes
No core change. `index_html` uses `<thead>` (Qt repeats it on every page, per Qt's HTML subset). Footer and page numbers: paint pages ourselves in the `paintRequested` slot (`QTextDocument.drawContents` per page plus a footer line), the same slot serves preview and the printer. After a written export the second line reads "Dışa aktarıldı: <time>" (time from C5 `job.last_export`, or the in-memory export time without C5); before writing it says "Dışa aktarma planı, henüz yazılmadı", so paper is never mistaken for a record. All rows print (existing D-53). Undo: none.

### 6. Tests
UI (`tests/ui/test_disa_aktar.py`, offscreen): print to a `QPrinter` with `PdfFormat` and a 60-row job: PDF has 2+ pages, every page has the header words and the footer "Sayfa n / m" (text read with pypdfium2, already a dependency); Ctrl+P opens the dialog (key-press test); Enter prints, Esc closes and focus is on the list; button names are Turkish. Screenshot: add the dialog to the `states` shots. Failure caught: header missing on page 2, or Ctrl+P raising like B-047.

### 7. Risks and open questions
Not tried on real printers (Obs. 15). Page break inside a row is possible with Qt tables. Wide lists (200 rows) take time to lay out. Turkish characters in the printer font.

**Shortcut contract rows it adds:** none new; row `disa_aktar` Ctrl+P `disa_aktar.yazdir` changes "what happens" to "the print preview opens; Yazdır… prints", with the refusal text "Yazdırılacak bir dizin yok." (already PROPOSED in the contract).
**Rules it must meet:** AUD-KBD-02, AUD-A11Y-01 (every dialog button named), AUD-HIT-02, AUD-TXT-01, AUD-WIN-01, DEC-FOC-01, DEC-LAY-03, DEC-THM-01, HIG-WIN-09 (ellipsis), HIG-WIN-16 (Esc closes).
**Performance cost:** the HTML for 800 rows is built in a worker with `run_background` (quick-wins I-47; build I-47 first): the row data and HTML string are plain data, and the `QTextDocument` and the preview widget are made on the window thread in `on_done` (I-47 rule 1). Layout estimate under 2 s, not measured; the first build step measures it. While it runs the loading card shows "Önizleme hazırlanıyor…" after 300 ms, with "İptal et" (Ctrl+.), and the window stays usable. Preview renders 3 to 20 pages, lazily.

**New Turkish text**

| string | where | meaning in English | status |
|---|---|---|---|
| Baskı önizleme | dialog title | print preview | draft |
| Yazdır… | dialog button | print | draft (existing word "Yazdır", `rehber.py:260`) |
| Kapat | dialog button | close | existing (Ayarlar) |
| Sayfa {n} / {m} | footer, dialog | page n of m | draft |
| Önceki sayfa, Sonraki sayfa | dialog buttons (tooltips) | previous, next page | draft |
| Sığdır | dialog button | fit | existing (`app.sigdir`) |
| Dışa aktarma planı, henüz yazılmadı | printed sub title | export plan, not yet written | draft |
| Dışa aktarıldı: {zaman} | printed sub title | exported at | draft |
| Önizleme hazırlanıyor… | loading card title (I-47) | preparing preview | draft |

**Check against the product:** Never silent: Pass (plan vs record is printed). No built-in kinds: Pass. Keyboard: Pass. Colour: Pass (no orange; Kontrol still icon + word in the table). Layout: Pass. Copy: Pass. Local-first: Pass (no new dependency).

**Owner decisions needed**
- D-3 (O-16) **Decided by evidence (T3, 2026-11-20; sources in README §6).** Ctrl+P opens the preview; Enter ("Yazdır…") prints. Evidence: Office prints and previews from one place, "File and then Print (or pressing CTRL+P)" (Microsoft, "Printing and print preview"); Ctrl+P stays Print in every source and the preview gets no second key such as Ctrl+Shift+P, which GNOME uses for Print Preview and the app uses for the palette (`research/shortcut-conventions.md` §5 rank 2).
- D-4 Decided in the reconcile: "20.11.2026 14:32" (Turkish order) on paper and in the `Özet` sheet.

**Build steps:** (1) `<thead>` plus "No" column and test the PDF header on page 2; (2) own page painter with footer and "Sayfa n / m"; (3) preview dialog with Turkish buttons; (4) Ctrl+P wiring and key tests; (5) plan/record subtitle; (6) measure 800 rows.

---

## I-39 Bulk rename preview: source, new name, conflict flag; copy the list

### 1. Problem
"I only see wrong names after the files are written." The list shows the new name (`disa_aktar_table.py:53` headers: Durum, Yazılacak dosya adı, Sayfalar, Şablon) but not which scan it came from, and the "path too long" shortening is known only at export (`exporting.py:62`). Serves Never silent.

### 2. Who and when
Everyone exporting; before pressing Ctrl+E, at the pre-flight, in a long session.

### 3. Keyboard flow
In the list: "Adları karşılaştır" (menu Görünüm and the command palette, no key; T3: Ctrl+Shift+A is GNOME's Deselect All, `research/shortcut-conventions.md` §5 rank 1) toggles the Kaynak column; Ctrl+Shift+C copies the whole list (Kaynak, Yazılacak dosya adı, Not) as tab-separated text, ready for Excel; Ctrl+C keeps copying only the selected names (existing `copy_names`, `disa_aktar.py:886`). The filter button "Adı değişenler" (Tab to it, Space) shows only rows whose name differs from the pattern. The existing "Adları göster" jump (`show_changed_names`, `:865`) stays. Menus: Görünüm for the toggle, Düzen for copy.

### 4. Screen sketch (list card, side panel open, 1366x768)
```
Dosya adları  kontrol gerekenler üstte    [Adı değişenler 2] [Yalnızca kontrol gerekenler 3]
Durum        | Kaynak            | Yazılacak dosya adı     | Sayfalar | Şablon
Kontrol      | tarama_02.pdf     | belge_007.pdf           | 14       |
 Sicil no eksik
Bilgi        | tarama_01.pdf     | 101_Örnek (2).pdf       | 3–4      | Deneme
 Ad çakışması, (2) eklendi
```
Reuses `FilesTable` and `PartsButton` (the existing filter button). The Kaynak column sits before the name; at 100 % the widths are 252 / 150 / rest / 104 / 148, so the Şablon column scrolls into view at 150 % exactly as today. When a document spans scans the cell reads "tarama_01.pdf +1". Status keeps icon + word; orange only on Kontrol.

### 5. Data and core changes
C1-C3: `ExportItem.sources` (from `job.batches` file names, using the batch id parsed from each page id, `job.py:24`; O(pages), no `position_of`), `name_note`, and `plan_names` so the shortening and its note appear before export. `file_rows` (`disa_aktar_model.py:126`) reads `item.name_note` instead of `_name_change`; `FileRow` gains `source`. `FilesModel.HEADERS` gains an optional column (`disa_aktar_table.py:53`). The window calls `plan_names` with the chosen folder (it changes when the folder changes; without a folder the unfitted names show, with the existing hint). Clipboard text built in `DisaAktarScreen.copy_list`. CLI: `--onizle` prints the same rows (C6). Header state: the new column width is saved like the others (`_save_header`, `disa_aktar.py:390`). No undo step.

### 6. Tests
Core: `plan_names` marks a name cut by a long folder path, a clash suffix and a removed character, with `name_note` text; `sources` for a document spanning two batches. UI: toggling adds the column; Ctrl+Shift+C puts N+1 lines on the clipboard; the filter shows exactly the rows with a note; the list equals `--onizle` output and equals the files written (`test_p6_read_vs_export.py` style). Failure caught: preview says one name and export writes another.

### 7. Risks and open questions
"Old name" is the scan file, because a document has no earlier name (decision D-5). A name shortened by path length depends on the folder, so it changes as the folder is typed (live, cheap). Duplicate scan names in two batches are shown as is.

**Shortcut contract rows it adds:** `disa_aktar` (no key) `disa_aktar.adlari_karsilastir` "Adları karşılaştır" (checkable, Görünüm, palette); `disa_aktar` Ctrl+Shift+C `disa_aktar.liste_kopyala` "Ad listesini kopyala" (Düzen); no clash on this tab in the contract, confirm with the audit script at build.
**Rules it must meet:** AUD-KBD-01/02, AUD-A11Y-01 (column and buttons named), AUD-TXT-01, AUD-HIT-03, DEC-IDN-01 (orange only Kontrol), HIG-CON-03 (no meaning by colour alone), HIG-WIN-12 (key shown in the menu).
**Performance cost:** `plan_names` on 800 documents: string work only, under 50 ms (not measured); `sources` removes the existing O(n²) `position_of` use for the new column only. Column adds no per-row widget (delegate paints).

**New Turkish text**

| string | where | meaning in English | status |
|---|---|---|---|
| Adları karşılaştır | action, menu Görünüm, tooltip | compare names (show source) | draft |
| Kaynak | list column header | source scan | draft |
| Ad listesini kopyala | action, menu Düzen | copy the name list | draft |
| Ad listesi panoya kopyalandı | toast | name list copied to clipboard | draft |
| Adı değişenler | filter button | names that changed | draft |
| {dosya} +{n} | Kaynak cell | file and n more | draft |
| Ad çakışması, (2) eklendi / Geçersiz karakter silindi | Durum reason | name clash / invalid character removed | existing (`disa_aktar_model.py:114`) |
| Dosya adı kısaltıldı (klasör yolu uzun) | Durum reason | name shortened | existing (core check text) |
| Yazılacak dosya adı | clipboard header | file name to write | existing |

**Check against the product:** Never silent: Pass (shortening now visible before writing). No built-in kinds: Pass. Keyboard: Pass (two keys, filter by Tab). Colour: Pass. Layout: Needs check at 150 % (Şablon scrolls as today). Copy: Pass. Local-first: Pass.

**Owner decisions needed**
- D-5 (O-17) **Decided by evidence (T3, 2026-11-20; sources in README §6).** The "old name" is the scan file (Kaynak). Evidence: Windows' bulk renamer shows the name the file has on disk next to the new one (PowerRename preview columns "Original" and "Renamed", with a toggle to show only renamed files, like "Adı değişenler"); a document's only name on disk before export is its scan file, while `belge_NNN` is never a file the user saw.
- D-6 Decided in the reconcile: toggle, default off (keeps the list narrow). Wording note for the Turkish terms check: list column "Kaynak" (scan file) sits next to the sheet's "Kaynak sayfalar" (page numbers).

**Build steps:** (1) C1-C2 `sources` and `name_note` with core tests; (2) C3 `plan_names` and `export_job` switch with equality test; (3) `file_rows` uses core notes; (4) Kaynak column and toggle; (5) "Adı değişenler" filter; (6) copy list and key; (7) CLI `--onizle`.

---

## I-40 "Kontrol gerekenler" report (problems only)

### 1. Problem
"The supervisor wants only the documents that need a check, without opening the app or scrolling 300 rows." Today the sheet has one mixed list with a yellow fill. Serves Never silent.

### 2. Who and when
Supervisors and staff handing over a finished export; after every export with checks.

### 3. Keyboard flow
No new key: Ctrl+E exports, "index.xlsx'i aç" opens the file; the report is its second sheet. No separate save before exporting (O-19 decided: sheet only).

### 4. Screen sketch
Sheet `Kontrol gerekenler` (after `Belgeler` and `Özet`; order: Belgeler, Kontrol gerekenler, Özet):

| Belge no | Dosya | Kaynak sayfalar | Kontrol nedenleri |
|---|---|---|---|
| 7 | belge_007.pdf | 14 | değerler okunmadı |
| 12 | belge_012.pdf | 22, 23 | zorunlu değer eksik: Sicil no |

With no check: one row, "Kontrol gerektiren belge yok." (the sheet is always there, so a missing sheet never means "unchecked"). The outcome card and "index.xlsx'i aç" button are unchanged; the done toast adds nothing.

### 5. Data and core changes
C4: `write_index` writes the second sheet from `item.checks`, so it is the same list as the "Kontrol gerekli" column and `ExportResult.needing_check` (`exporting.py:41`). The window's Kontrol count must match it: this depends on bug B-003 (PDF/A failure is in `item.checks`, so it counts as Kontrol in the sheet and card but shows as Bilgi in the list). Recommended fix inside this build: keep the PDF/A note out of `checks` (`ExportItem.pdfa_note`), so list, card, `may_delete_after_export` and both sheets agree; the PDF/A column keeps "hayır". CLI: the last line adds "Kontrol listesi: index.xlsx, sayfa 'Kontrol gerekenler'." when needing_check > 0. No `write_check_report` (O-19).

### 6. Tests
Core: `tests/test_index.py`: sheet exists, rows equal the flagged items in order, the "no check" row, formula-like values stay text; `test_exporting.py`: `needing_check` equals the sheet rows, with a PDF/A-failed file (B-003 test `test_b003_pdfa_failure_is_one_rule_in_list_and_outcome_count` must pass); CLI: the output line and sheet appear. UI: list Kontrol count equals sheet rows. Failure caught: a flagged document missing from the report, or counted differently on screen.

### 7. Risks and open questions
B-003 is decided (O-18: Bilgi); it must be fixed first, otherwise report and list disagree. Reasons are the core's Turkish check texts, shown as they are. A document approved in Kontrol (İncelendi) with an open check still counts as Kontrol here (B-034, Enter with open check); the report says so by listing it, never hides it.

**Shortcut contract rows it adds:** none.
**Rules it must meet:** DEC-IDN-01 (yellow check fill stays; Kontrol is also a word), AUD-KBD-02, AUD-A11Y-01.
**Performance cost:** at most 800 rows more in one sheet: under 20 ms.

**New Turkish text**

| string | where | meaning in English | status |
|---|---|---|---|
| Kontrol gerekenler | sheet name | needs check | existing (`degerler_model.py:47` view name; lower case in `disa_aktar.py:189-190`) |
| Belge no, Dosya, Kaynak sayfalar, Kontrol nedenleri | sheet header | document no., file, source pages, reasons | existing (`index.py:16-23`) except Belge no (I-35) |
| Kontrol gerektiren belge yok. | sheet row, status line | no document needs a check | draft |
| Kontrol listesi: index.xlsx, sayfa 'Kontrol gerekenler'. | CLI line | where the report is | draft |

**Check against the product:** Never silent: Pass once B-003 is settled (Needs change before). No built-in kinds: Pass. Keyboard: Pass. Colour: Pass. Layout: N/A. Copy: Pass ("Kontrol", not "Şüpheli"). Local-first: Pass.

**Owner decisions needed**
**Decided by evidence (T3, 2026-11-20; sources in README §6).**
- D-7 (O-18) A PDF/A failure is Bilgi everywhere; the PDF/A column still says "hayır"; fixed in this build (small core change above). Evidence: OCRmyPDF, the sector's open OCR-to-PDF/A tool, treats it as a usable result, exit code 10 "A valid PDF was created, PDF/A conversion failed. The file will be available."; D1 keeps orange and "Kontrol" for documents a person must check, and the column keeps it visible (Never silent).
- D-8 (O-19) No separate save before exporting; the list is the "Kontrol gerekenler" sheet. Evidence: before export the same list is already on screen in the existing "Yalnızca kontrol gerekenler" filter of Dışa Aktar (`disa_aktar.py:190`) and in Değerler, so PRODUCT.md's "visible where the user works, and in index.xlsx" is met without a second file; it can be added later without a format change.

**Build steps:** (1) fix B-003 (O-18 decided) with its test; (2) `Kontrol gerekenler` sheet and tests; (3) CLI line; (4) UI count test.

---

## Order and dependencies
I-35 first (C4, C5, the new column), then I-40 (needs C4 and the B-003 decision), then I-39 (C1-C3, C6), then I-38 (UI only; uses C5 for the written time). Each idea can be built and tested alone after C4. Across specs: I-38 uses `run_background` and the loading card from quick-wins I-47; nothing here depends on A or C. Full order: `specs/README.md`.
