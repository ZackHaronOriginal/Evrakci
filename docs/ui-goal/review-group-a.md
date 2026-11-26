# Review: group A (Kontrol filters: A §0 + I-09, I-08, I-03, I-06, I-04)

Commits reviewed: I-08 `685f3a9`, `07719fb` (merge `bb7bedf`); A §0 + I-09 `8babcf0`, `c273c6b`,
`7107fa1` (merge `022c123`); I-03 `4ba2f18`, `5cfd867`, `9f17713`, `c3658e2` (merge `040b68d`);
I-06 `55afa7d`, `ac1d473`, `ac8ea04` (merge `36fd83f`); I-04 `3124cd8`, fix `ad93aac`, `5627f63`
(merge `152be91`). Group A files only. Checked against `specs/kontrol-filters.md` (all sections),
`specs/README.md` §1 and §6, `decisions.md` (2026-11-20), PRODUCT.md and DESIGN.md. Cross-step
review (Opus). Severity as in `bugs.md`.

No S1 or S2 found. Checked and agreeing:
- **Core.** `pipeline/select.py` is pure (no Qt, no imaging). It has the six kinds `belge`,
  `tek`, `cift`, `bos`, `guven` and `farkli`, plus `combine` with replace / add / within.
  Separators and deleted pages never match. Odd / even is counted from each document's first
  page (O-1). `Job.remove_filter` only rewrites `filters`.
- **Window == CLI.** The window and `is sec` use the same `evaluate` for every kind. The CLI's
  `farkli` reads missing sizes in memory and writes nothing. The default reasons (Orta off), the
  0,3 % limit and the 3 % tolerance are the same on both sides. `filtre-kaldir` gives the same
  `job_to_dict` as Shift+F (test).
- **Job files.** `JOB_FORMAT_VERSION` stays 2. `width_mm` / `height_mm` are additive (one
  decimal). An old dict, or a damaged size, reads as 0.0. An older program reads its own keys
  unchanged (`test_job_format.py`). An undo carries the sizes that were read (`carry_page_sizes`).
- **Window thread.** Old-job sizes are read in a worker (`read_sizes`, PDFium lock per page),
  with no render. Late results for a closed or deleted window are dropped (`5627f63`). Measured
  here on 800 pages: `farkli` 4.4 ms (O(n·40)), `belge` / `tek` / `bos` about 0.5 ms each.
  `select_row_set` builds one merged `QItemSelection`. Odd marks are computed once per model
  rebuild.
- **Keys and paths.** `audit_shortcuts.py --check --contract`: 0 problems. `--paths --check`:
  361 rows, 0 problems. B is page-specific next to Şablonlar' Kutu çiz. Every new key has a
  menu path (Düzen, Araçlar, Görünüm, Git) and the context menu.
- **Accessibility and colour.** The criteria radios, the reason boxes ("Kontrol, 4 değer"), the
  spin box, the combo and the page radios all have accessible names. Page text adds "farklı
  boyut" / "yatay" / "dikey". The I-04 mark is icon plus word in `text-2`, or WindowText in high
  contrast, never orange. Orange appears only on the Kontrol reason word (`check-text`, which is
  `sys-text` in high contrast).
- **Tests.** The changed assertions follow approved string changes (`07719fb`, NBSP `5cfd867`),
  a documented extra divergent key (B, 18 to 19), and the removal of `fill_page_sizes` (its
  "saved" check moved to the UI test `test_kontrol_farkli.py:438/497`). One check was relaxed:
  see R-A-6.

| ID | Sev | File:line | Finding / failure scenario | Suggested fix | Action |
|---|---|---|---|---|---|
| R-A-1 | S3 | src/evrakci/ui/kontrol.py:699 | "Kontrol gerekenler" with "Seçimle kesiştir" (or "Seçime ekle"). The status line is `guven_text(match)`, so it gives the documents and reasons of the whole match, not of what was selected. Example: 3 pages selected inside 1 document, and the line says "9 belge seçildi: Kontrol 4, …". The dialog row count (intersection) and the status line then disagree (Never silent: the count must be true). | Compute the reasons and documents from the final `ids`. For example, `guven_match` over the findings with the pages limited to `ids`. Or, in the within / add modes, use the general "{n} sayfa seçildi." with the final count. Add a UI test for within mode. | fix now |
| R-A-2 | S3 | src/evrakci/ui/kontrol.py:701 | "Boş sayfalar" with "Seçime ekle": the toast says "{len(ids)} boş sayfa seçildi. Silmek için Del." but `ids` is the union, so it also counts the non-blank pages that were selected before. Example: 5 pages selected plus 3 blanks gives "8 boş sayfa seçildi". Del would then delete pages that are not blank. | Use the "{n} boş sayfa" form only in replace / within mode (n = blank pages in `ids`). In add mode use "{n} sayfa seçildi.". Add a test. | fix now |
| R-A-3 | S3 | src/evrakci/cli/jobs.py:208-214 | `is filtre-kaldir İŞ 1-4` on pages with no filter saves the job and prints "Filtre kaldırıldı, 4 sayfa." It also counts the whole range, not the filtered pages. In the same case the window says "Bu sayfalarda filtre yok." and changes nothing. The two outputs disagree, and the CLI claims a change it did not make. | Count the pages of the range that have a filter (as `KontrolScreen._filtered` does). With none, print "Bu sayfalarda filtre yok." (approved) and do not save. Otherwise print that count. Extend `test_remove_filter_range_and_errors`. | fix now |
| R-A-4 | S3 | src/evrakci/ui/main_window.py:1398-1401 | The quiet size fill of an old job takes the window's single loading slot, with `cancellable=False`. While it runs, Yeni iş, Dosya ekle, Değerleri oku, Eksikleri oku and Dene are off with "Bir iş sürüyor; bitince açın." (`_sync_loading`), and opening another job or exporting is refused. The card waits 1.5 s, so for that time only the status line says why. On a slow or network folder with many batches this can take seconds and cannot be stopped. The spec asked only for "off the UI thread with a status line". | Run the fill outside the loading slot (its own `Background` that does not count as `loading()`), or make it cancellable and let a user-started load cancel it. Measure with `perf-profile` on a network path. | ledger |
| R-A-5 | S4 | src/evrakci/cli/jobs.py:738; jobs.py:249,256 and ui/kontrol_dialogs.py:431; ui/kontrol_dialogs.py:339 | User-visible text that is in no I-0x table: the CLI help " (varsayılan: Orta hariç hepsi)"; the count suffix of "Boyutu bilinmiyor ({n})" (the table has "Boyutu bilinmiyor" only); and "{n} silinmiş" in the blank count (only in the I-03 sketch, not in its table). | Add the three to the I-03 / I-04 / I-06 tables for the owner's copy review, or drop the extra parts. | ledger |
| R-A-6 | S4 | src/evrakci/ui/actions.py:235,287 (check relaxed in actions.py `_validate_menus` and tests/ui/test_actions.py:263, commit `7107fa1`) | "Bu belgeyi seç" (Düzen) and the Alt+Left "Seçimi bozmadan git" (Git) have no access key. The I-09 table has "Bu belgeyi &seç". The menu check that required a letter on every item now accepts items without one, so a future item can lose its letter silently. | Give both a free letter, or keep the exemption as an explicit list of ids in the validator and the test (not a blanket `None` skip). Note the table change. | ledger |
| R-A-7 | S4 | src/evrakci/ui/actions.py:285-288 | The Git menu lists "Seçimi bozmadan git" twice (Alt+Right and Alt+Left). A screen reader and a mouse user can tell them apart only by the shortcut column, and the two items have the same accessible name. | Ask the owner for direction words, for example "Seçimi bozmadan git (sağa / sola)" (a new string, so it goes to the table), or one item with the direction in the tooltip. | ledger |
| R-A-8 | S4 | src/evrakci/ui/kontrol_dialogs.py:484-491 | `count()` says "how many pages Seç would select … in the chosen mode", but in add mode it shows the match count, not the union. The row count and the toast after Seç differ (for example 212 against 222). | Say "how many pages match" in the docstring (the row is the criterion's count), or show the union in add mode. Keep the toast true either way (R-A-2). | fix now |
| R-A-9 | S4 | src/evrakci/pipeline/select.py:7-9, 170 | The module says pages the job leaves out never match, but `bos` walks every page. With "Boş sayfaları at" on, the dropped blank pages are counted and selected (they are drawn, so Del works on them). The documentation and the behaviour differ. The behaviour is the useful one. | Correct the docstring (dropped blank pages match `bos`, and this is intended), and add a core test with `drop_empty` on. | fix now |
| R-A-10 | S4 | tests/test_cli_select_bos.py, tests/test_cli_select_guven.py, tests/ui/test_kontrol_bos.py, tests/ui/test_kontrol_guven.py | Window == CLI for `bos` and `guven` is shown only in two steps (window to core, CLI to core). Unlike `belge` / `tek` / `cift` (test_kontrol_select.py:181) and `farkli` (test_kontrol_farkli.py:396), no test sends one job through both sides. A template-source difference (window `templates()` against CLI `_job_templates`) would not show. | Add one UI test per kind: the dialog's Seç rows against the CLI's `sayfa …` line on the same store. | fix now |
| R-A-11 | S4 | src/evrakci/ui/kontrol_dialogs.py:203 | The I-09 spec (§4) says the two columns stack at 150 % text. `ac1d473` keeps two columns, and the test shows the dialog fits 1366x768 at 150 %. The spec text is now out of date. | Update the spec sketch note (fit verified by `test_dialog_fits_1366x768_at_150_percent_for_every_criterion`). | ledger |
| R-A-12 | S4 | src/evrakci/ui/kontrol.py:368-371; ui/kontrol_actions.py `_dimmed` | Spec I-08 §4 says entries are dimmed when they would do nothing (HIG-CTL-09). Only the context-menu copies are dimmed. In the menu bar, Araçlar "Filtreyi kaldır", "Şablonu kaldır" and "Boş sayfayı geri getir" stay enabled and answer in words. This is not silent, but it differs from the spec. | Owner choice: dim them in the menu bar too (`aboutToShow`), keeping the key's spoken answer, or write the deviation into the spec. | ledger |

Counts: S1 0, S2 0, S3 4, S4 8.

Suite (`QT_QPA_PLATFORM=offscreen python -m pytest -q -p no:cacheprovider -o faulthandler_timeout=600`):
2944 passed, 4 skipped, 205 xfailed, 1 warning (DeprecationWarning, QDragEnterEvent) in 701 s, exit 0. `ruff check src tests`: All checks passed.
