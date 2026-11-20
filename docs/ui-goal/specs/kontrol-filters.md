# Spec group A: Kontrol "select by" filters (I-03, I-04, I-06, I-08, I-09)

Status: proposal, nothing built. The owner approves each idea before it is built. Checked at HEAD on 2026-11-20. Idea rows: `docs/ui-goal/ideas-ranking.md`. Evidence: `research/findings-filtering.md`, `findings-selection.md`, `findings-splitting.md`, `findings-page-operations.md`, `findings-review-qc.md`, `inventory-kontrol.md`. D13 is lifted (decisions.md, 2026-11-20): core changes below are named, each with core tests, an old-job-file check and a CLI/window parity check.

**Reconciled with B, C and D (2026-11-20).** Build order, shared pieces, the Kontrol key table and the owner's decisions (O-1 to O-5 are this spec's) are in `specs/README.md`. This spec owns `pipeline/select.py`, the "Sayfaları seç" dialog and the CLI command `is sec`; C adds to them. `value_level` is owned by quick-wins I-17. The I-04 jumps lost the key D to I-21 and are menu-only. Job files stay version 2 for every spec (new fields are additive).

## 0. The shared part: one "Seç…" entry point and one selection model

**Problem.** Today F = "Filtre uygula…" only cuts the selected pages every N pages (`ui/kontrol.py:apply_filter` L300, `ui/kontrol_dialogs.py:FilterDialog` L39). Everything the five ideas add is a different thing: it chooses pages, and does nothing else. If each got its own key and dialog, Kontrol would gain five dialogs and the word "filtre" would mean two things.

**Decision in this spec.**
- F stays exactly as it is (every N pages, K-21 to K-30). Nothing in it changes except the new "Filtreyi kaldır" (I-08).
- New command **"Seç…"** (key **S**, menu Araçlar, context menu, command-bar icon `list-checks`) opens one dialog, `SelectDialog`, next to `FilterDialog` in `ui/kontrol_dialogs.py`. Its result is only a set of page ids that becomes the timeline selection. It never edits the job, so it has no undo step; the user then presses Del, F, T, R, K as today. The word "Filtre" is kept for the cut kind; the new word is "Seç".
- The dialog is a list of criteria (one radio row each, with its live count in the row) and, on the right, the parameters of the chosen row, then "Seçimi değiştir / Seçime ekle / Seçimin içinde ara" and the primary button "Seç". Group C (`qr-saved-filters.md`) adds the row "QR içeriği" to this dialog, and its key Q opens this same dialog with that row chosen: there is no second dialog. Saved filters (C, I-07) are a chip row above the timeline, owned by C; the chips call the same core functions.

**Core: new module `src/evrakci/pipeline/select.py`** (pure, no Qt, no imaging; same functions for window and CLI).
- `Criterion(kind: str, params: dict)` with `to_dict()` / `from_dict()`. Kinds in this group: `belge`, `tek`, `cift`, `bos`, `farkli`, `guven`. Group C stores `Criterion.to_dict()` next to a template and adds kinds (`qr`); a saved filter is one named criterion (kind + params); several turned-on chips are AND-combined with `combine(..., "within")` through C's `select_pages`.
- `evaluate(job, criterion, *, templates=None, selection=()) -> Match`; `Match(page_ids: tuple[str, ...] in job order, documents: int, reasons: dict[str, int])`. `combine(base, match, mode)` with modes `replace`, `add`, `within` (intersection). `count()` is `len(match.page_ids)`. Separators are never part of a match (they cannot be filtered or deleted, K-47).
- Evaluate is a loop over `job.pages` (800 entries): well under 5 ms each; the dialog recomputes all rows on open and only the chosen row while a parameter changes (debounce 80 ms).
- CLI parity: `evrakci is sec <iş> <ölçüt> [--esik X] [--sil]` (this spec owns the command; C adds the ölçüt `qr`, `--kes`, `--sablon` and `--filtre`) prints the same counts and page numbers the dialog shows (and with `--sil` soft-deletes them, same as Del). Test: the same job through `select.evaluate` and through the CLI gives the same page list.

**Keys of the group** (all free on Kontrol, run `shortcut-audit` before building; no Turkish-only letters, no I, no Ctrl+Alt): S, B, Shift+F, Shift+T, Ctrl+Space, Alt+Left, Alt+Right. (D and Shift+D were dropped in the reconcile: D is "Değerlerde aç", quick-wins I-21; the I-04 jumps are menu-only. The Kontrol key table of all four specs is in `specs/README.md`.) B is also "Kutu çiz" on Şablonlar, so `B` needs a page-specific line in `shortcuts.md` at build. Single-letter ones obey Ayarlar "Tek tuşlu kısayollar" like K/M/R and have a menu path. Contract rows are listed per idea.

**New Turkish text for the entry point** (all "draft"; words checked against how Windows and Microsoft Office Turkish name the same things: "Tümünü seç", "Seçimi kaldır", "Vazgeç", "Ölçüt", "Tek/Çift sayfalar" in the print dialog):

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Seç… | menu Araçlar, context menu, command bar tooltip | Select by… | draft |
| Sayfaları seç | dialog title and accessible name | Select pages | draft |
| Ölçüt | label above the criteria list | Criterion | draft |
| Seçimi değiştir | radio in dialog | Replace the selection | draft |
| Seçime ekle | radio in dialog | Add to the selection | draft |
| Seçimin içinde ara | radio in dialog | Keep only matches inside the current selection | draft |
| Seç | primary button | Select | draft |
| Hiç yok | grey count in a row with no match | None | draft |
| {n} sayfa seçildi. / {n} sayfa seçildi ({ölçüt}). | status line / toast after Seç; the second form names the criterion (C uses it as "(QR: KAP-*)") | n pages selected | draft |
| Eşleşen sayfa yok. | status line when nothing matches | No page matches | draft |
| Vazgeç | cancel button | Cancel | existing |
| sayfa seçili | status bar item | pages selected | existing |

---

## I-09 Select this document, odd or even pages, Ctrl+Space

**1. Problem.** Filter and template need a selection; staff drag a rubber band over 20 to 60 thumbnails, and on a duplex pile cannot pick "all fronts". The inventory (K-41) did not know if Ctrl+Space works. I tested it offscreen on this tree: Ctrl+Space on a focused page selects nothing, and a plain arrow replaces the selection (Qt ExtendedSelection), so a keyboard-only user cannot pick scattered pages at all. Principle: Less paper handling; Calm for long sessions.

**2. Who and when.** Office staff in Kontrol, several times per document-heavy job.

**3. Keyboard flow.**
- **B** = "Bu belgeyi seç": selects every page of the current document (not separators, not deleted pages). Registry `kontrol.belgeyi_sec`, menu Düzen, context menu.
- **Ctrl+Space** = "Sayfayı seçime ekle / çıkar": toggles the focused page, keeps the others. Registry `kontrol.sayfa_sec`, local key (like Shift+arrows), menu Düzen.
- **Alt+Left / Alt+Right** = "Seçimi bozmadan git": move the focus ring one page without touching the selection (Ctrl+arrows are document jumps, so Qt's own way is taken). Registry `kontrol.git_secimsiz`, local.
- **S**, then "Tek sayfalar" or "Çift sayfalar", then Seç: odd or even pages counted from the first page of each document (1st, 3rd, 5th ...), because that is what duplex backs follow. With "Seçimin içinde ara" the odd/even is counted inside the current selection's documents only.
- Mouse: context menu "Bu belgeyi seç"; click on the document's guide tab also selects the document (see decision 2).

**4. Screen sketch** (1366x768, 100 %). No new region. The dialog:
```
+ Sayfaları seç ---------------------------------------+
| Ölçüt                         | Tek sayfalar          |
| (o) Bu belge            (3)   | Her belgenin 1., 3., 5. |
| ( ) Tek sayfalar       (212)  | ... sayfaları          |
| ( ) Çift sayfalar      (208)  |                        |
| ( ) Boş sayfalar        (14)  | (o) Seçimi değiştir    |
| ( ) Farklı ...           (5)  | ( ) Seçime ekle        |
| ( ) Kontrol gerekenler  (9)   | ( ) Seçimin içinde ara |
|                       [Vazgeç] [Seç]                    |
+----------------------------------------------------------+
```
Reuses `QDialog` with the `FilterDialog` margins (s6), `QRadioButton`, `kind="group-label"`, primary button. At 150 % text the two columns stack (list above, parameters below); the dialog never scrolls the window. High contrast: standard radios and the D11 ring. Counts are tabular numbers.

**5. Data and core.** No job-file field. Core: `select.evaluate` kinds `belge` (param `number`), `tek`, `cift` (param `within: bool`). UI: `KontrolScreen.select_document()`, `toggle_current()`, `move_focus(step)` (new, `ui/kontrol.py`); `TimelineView.keyPressEvent` handles Ctrl+Space and Alt+arrows (`ui/timeline.py`). Selection survives edits already (K-38).

**6. Tests.** Core `tests/test_select.py`: `belge`, odd/even with a QR cut and a deleted page in the middle (separators and deleted pages are skipped, counting restarts per document). UI `tests/ui/test_kontrol_a.py`: key press Ctrl+Space toggles twice and leaves other pages selected; Alt+Right moves focus and keeps a 3-page selection; B on document 2 selects exactly its pages. Registry: shortcut-audit table, contract rows. Screenshot: the matrix Kontrol shot with the dialog open (`states` shot). The one failure it must catch: Ctrl+Space silently doing nothing (today).

**7. Risks.** Alt+Left/Right is also "back" in some Windows apps; nothing else uses it on Kontrol. Ctrl+Space toggles the input method on some East-Asian IME setups; Turkish Q is not affected, and the menu item stays. Odd/even by document may surprise someone who thinks "odd page numbers in the job": the dialog hint says which. No colour is used.

**Shortcut contract rows it adds:** `kontrol B kontrol.belgeyi_sec`, `kontrol Ctrl+Space kontrol.sayfa_sec`, `kontrol Alt+Left` and `Alt+Right kontrol.git_secimsiz` (with precondition, effect, feedback, undo "n/a: selection only", test columns), `kontrol S kontrol.sec`. Registry and `docs/ui-goal/shortcuts.md` updated together.

**Rules it must meet.** AUD-KBD-01, AUD-KBD-02 (everything by keyboard), AUD-A11Y-01 (accessible names on radios and counts), DEC-FOC-01, HIG-WIN-09 ("Seç…" ends with an ellipsis), HIG-WIN-12 (key shown in the menu), HIG-CTL-03 (primary "Seç" answers Enter), HIG-WIN-16 (Esc cancels), AUD-TXT-01 (150 %), AUD-WIN-01.

**Performance cost (800 pages).** Counting: under 5 ms. Setting a selection of up to 800 rows uses one `QItemSelection` of merged ranges (as `TimelineView.select_rows` does), one repaint. None on scroll.

**New Turkish text.**

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Bu belgeyi &seç | menu, context menu (B) | Select this document | draft |
| Bu belge | criterion row | This document | draft |
| Tek sayfalar | criterion row | Odd pages | draft |
| Çift sayfalar | criterion row | Even pages | draft |
| Her belgenin 1., 3., 5. ... sayfaları | hint under "Tek sayfalar" | Pages 1, 3, 5 ... of every document | draft |
| Her belgenin 2., 4., 6. ... sayfaları | hint under "Çift sayfalar" | Pages 2, 4, 6 ... of every document | draft |
| Sayfayı seçime ekle / çıkar | menu Düzen (Ctrl+Space) | Add the page to / remove it from the selection | draft |
| Seçimi bozmadan git | menu Git (Alt+arrows), tooltip | Move without changing the selection | draft |
| Önce bir sayfa seçin. | status when no current page | Select a page first | existing |
| Bu belgede seçilecek sayfa yok. | status when all pages are deleted | No page to select in this document | draft |

**Owner decisions needed.**
1. (README O-1) Odd/even counted from each document's start (recommended: duplex fronts and backs follow the document) or by job page number.
2. (README O-2) Should a click on a document's guide tab select the whole document? Recommended: no, keep it as it is (it moves focus); B and the context menu are enough and avoid changing a click the staff know.
3. ~~Alt+Left/Right~~ Merged into README O-5 (the Kontrol keys of this spec).

**Build steps.** (1) `select.py` with `belge`, `tek`, `cift` and tests. (2) `Ctrl+Space` and Alt+arrows in `TimelineView` with key-press tests. (3) Registry ids, contract rows, `shortcuts.md`. (4) `SelectDialog` shell with these three rows and the entry key S. (5) CLI `is sec`.

---

## I-03 Blank pages with a threshold and a live count

**1. Problem.** On a duplex pile every second page is blank; blank backs stay in the documents unless the CLI is used (K-20, B-006). "Is it blank" is judged by one fixed number (`EMPTY_INK_RATIO = 0.003`, `pipeline/analyze.py:16`) the user cannot see. Principle: Less paper handling; Never silent.

**2. Who and when.** Staff after import, before Filtre/Şablon; the same day as I-09.

**3. Keyboard flow.** S, Down to "Boş sayfalar", Tab to "En çok mürekkep oranı" (spin box, steps of 0,1, range 0,1 to 5,0 %, default 0,3), the live count under it ("14 sayfa boş") follows each key; Enter selects them (replacing the selection). Del then deletes them (undoable, names the count, K-43). Registry: only `kontrol.sec`. No new key.

**4. Screen sketch.** Parameter pane of the dialog:
```
Boş sayfalar
En çok mürekkep oranı  [ 0,3 ] %
Bu orandan az mürekkepli sayfalar boş sayılır.
14 sayfa boş   (en boş 0,0 %, en dolu 0,29 %)
```
Reuses spin box, secondary caption, `QLabel[state="orta"]`-free plain text. The extreme values show how close the next page is, so staff can tell if the limit is right. Blank pages already deleted are counted apart ("2 silinmiş").

**5. Data and core.** No job-file field: `PageInfo.ink_ratio` is stored since analysis. Core: `select.evaluate(kind="bos", params={"ink": 0.003})`; `analyze.EMPTY_INK_RATIO` stays the default. The CLI `evrakci is sec bos --esik 0,3` prints the same list (parity test). The global "drop empty pages" switch (B-006) stays out; see decision.

**6. Tests.** Core: pages built with `fakes.empty_page` and `text_page`: threshold 0.003 selects the empty ones, 0.0005 selects fewer, QR pages never. UI: dialog count equals the number selected after Seç. Screenshot: the dialog in the `states` shot. Failure it must catch: a page with a speckle of dust counted as non-blank without the user seeing the limit.

**7. Risks.** A pale but real page (a stamp only) can fall under the limit: the result is only a selection plus an undoable Del, never a drop. Ink ratio uses a 100 dpi render with a 6 % edge margin (`analyze.py:_ink_ratio`), so a dark scanner border is ignored. Tell staff in the hint, not more.

**Shortcut contract rows it adds:** none beyond S (listed in I-09).

**Rules it must meet.** AUD-KBD-02, DEC-CON-02 (hint text 4.5:1), AUD-HIT-03 (spin box 32 px), HIG-CTL-11 (spin box width fits "0,3"), HIG-CTL-10 (label visible, not a placeholder), AUD-TXT-01.

**Performance cost (800 pages).** Evaluate is 800 comparisons, under 1 ms; recomputed per key press with 80 ms debounce. No render, no thumbnails touched.

**New Turkish text.**

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Boş sayfalar | criterion row | Blank pages | draft |
| En çok mürekkep oranı | spin box label | Highest ink share | draft |
| Bu orandan az mürekkepli sayfalar boş sayılır. | hint | Pages with less ink than this count as blank | draft |
| {n} sayfa boş | live count | n pages are blank | draft |
| en boş {a} %, en dolu {b} % | live count detail | emptiest and fullest blank page | draft |
| {n} boş sayfa seçildi. Silmek için Del. | status after Seç | n blank pages selected; press Del to delete | draft |
| Boş | caption of a dropped page | Blank | existing |

**Owner decisions needed.**
1. Decided in the reconcile (not the owner's): keep 0,3 %, the value the CLI and the guide use; the user changes it in the dialog.
2. (README O-4) Add a switch for the global "drop blank pages" (B-006)? Recommended: no. Selecting then Del is visible and undoable; a hidden global switch would hide pages again.

**Build steps.** (1) `select` kind `bos` with tests. (2) Criterion row and live count in `SelectDialog`. (3) Status line text and `is sec bos`. (4) Screenshot.

---

## I-04 Page size or orientation, "looks different" mark, jump

**1. Problem.** In 400 pages a sideways page or an A5 insert hides; it shows only when exported. The app does not know a page's size at all (`PageInfo` has `ink_ratio`, `is_separator` only, `analyze.py:29`). Principle: Never silent.

**2. Who and when.** Reviewers of mixed piles, in Kontrol after import.

**3. Keyboard flow.** "Sonraki farklı sayfa" / "Önceki farklı sayfa" in menu Git and the command palette, no key (reconcile: D is I-21's "Değerlerde aç"; see README O-10) (wrap round, toast "Farklı sayfa yok." when none, like N). To pick them: S, "Farklı boyut veya yön", choose Boyut and/or Yön, Seç; then R fixes sideways pages (R rotates by 90 and the mark goes away, because orientation is judged after the job's rotations). Registry `kontrol.sonraki_farkli`, `kontrol.onceki_farkli` (menu Git), and the checkable `kontrol.farkli_isaretle` (menu Görünüm, no key) to turn marks on or off.

**4. Screen sketch.** A marked tile (caption line under the sheet, same place as "Silinecek"):
```
[ sheet ]      [ sheet ]
 72             73  [ruler] Farklı boyut
```
Mark = a 14 px Lucide icon (`ruler` for size, `rectangle-horizontal` for Yatay) plus the word, caption weight 600, colour `text-2`/`text` only, **not orange** and not any cut colour (Rider Means Kontrol Rule, Position Before Colour Rule). Painted by a new helper in `ui/kontrol_paint.py` (`paint_odd_mark`) called from `TimelineDelegate._caption` (`ui/timeline.py:413`). At 150 % text the caption wraps to two short lines; high contrast uses WindowText. The accessible text of the page adds ", farklı boyut" or ", yatay" (`TimelineModel.describe`, `timeline.py:214`).

**5. Data and core (needs a core change).**
- `PageInfo` gets `width_mm: float = 0.0`, `height_mm: float = 0.0` (page as displayed, before the job's own rotation; 0.0 = unknown). `analyze_pdf` reads `page.get_size()` inside the existing per-page lock before rendering: no extra render, near-zero cost.
- Job file: `job_to_dict` writes `width_mm` and `height_mm` (one decimal) per page; `job_from_dict` reads them with a default of 0.0. `JOB_FORMAT_VERSION` stays 2, so an older program still opens a newer file (it ignores the keys) and a newer program opens old files.
- Old jobs: `analyze.read_page_sizes(path) -> list[tuple[float, float]]` (no rendering) and `JobStore.fill_page_sizes(job)`, called once when a job with unknown sizes is opened; it is housekeeping, not an undo step; it saves the job. Pages still 0.0 (file gone) are shown as "Boyutu bilinmiyor" in the dialog, never marked. C's `JobStore.reread_qr` (I-01) is the other old-job helper: it renders, so it runs only on demand; `fill_page_sizes` does not render and runs on open. Both use `JobStore.batch_file`; whichever is built first adds the shared old-job test fixture.
- `select.evaluate(kind="farkli", params={"by": ["boyut","yon"], "reference": "is"|"belge"})`. Size differs when either side is more than 3 % off the reference (A4 scanner jitter); reference = the most frequent size or orientation among non-deleted, non-separator pages of the job (or of each document). Pure core function, `select.different_pages(job, ...)`.
- No `index.xlsx` change (marks are a view aid; export is unchanged).

**6. Tests.** Core: `tests/test_analyze.py` size from a real two-page PDF (A4 and A5, one landscape) via `fakes.make_pdf`; `tests/test_job.py` round trip plus loading a stored old dict without the keys; `tests/test_select.py` A4 jitter does not mark, user rotation fixes orientation; `tests/test_store.py` `fill_page_sizes`. CLI/window parity: `is sec farkli` and the dialog give the same list. UI: "Sonraki farklı sayfa" wraps and toasts; caption text and accessible name; matrix shot with a marked tile in light, dark, high contrast at 150 %. Failure it must catch: a sideways page unmarked after R fixed it, or marked after user rotation.

**7. Risks.** A mixed job (A4 and A5 forms by design) marks half the pages: so the mark is switchable and the reference can be the document. The user decides what is normal (nothing built-in about document kinds): the reference is the job's own majority. Perf: marks computed once per model rebuild, O(n). Scope creep: no auto-rotate, no auto-crop.

**Shortcut contract rows it adds:** none (the jumps are menu-only after the reconcile).

**Rules it must meet.** DEC-IDN-01 (orange only kontrol), HIG-CON-03 (icon plus word, not colour), DEC-TYP-01 (caption at least 13 px), DEC-ICO-01 (icon 16 or scaled), DEC-THM-01 (three themes), AUD-TXT-01, AUD-KBD-02, HIG-CTL-08 (checkable item clearly on or off).

**Performance cost (800 pages).** Import: no extra render. Open of an old job: `read_page_sizes` opens each batch PDF once, about 1 ms per page (to be measured with `perf-profile`), 0.8 s for 800 pages, off the UI thread with a status line "Sayfa boyutları okunuyor". Paint: one extra icon per marked tile only.

**New Turkish text.** (Windows and Word name page orientation "Yön: Dikey / Yatay", size "Boyut")

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Farklı boyut veya yön | criterion row | Different size or orientation | draft |
| Boyut | checkbox in parameters | Size | draft |
| Yön | checkbox in parameters | Orientation | draft |
| Karşılaştır: Bütün iş / Her belge | combo label and items | Compare with: whole job / each document | draft |
| Farklı boyut | caption mark | Different size | draft |
| Yatay | caption mark | Landscape | draft |
| Dikey | caption mark (job mostly landscape) | Portrait | draft |
| {n} sayfa farklı görünüyor | live count | n pages look different | draft |
| Boyutu bilinmiyor | note in dialog | Size unknown | draft |
| Sayfa boyutları okunuyor | status line when filling an old job | Reading page sizes | draft |
| Sonraki farklı sayfa | menu Git | Next different page | draft |
| Önceki farklı sayfa | menu Git | Previous different page | draft |
| Farklı sayfa yok. | toast / status | No different page | draft |
| Farklı görünenleri işaretle | menu Görünüm, checkable | Mark pages that look different | draft |

**Owner decisions needed.**
1. (README O-3) Marks on by default (recommended: yes, Never silent; one click off in Görünüm) or off until the user opens "Seç…".
2. Decided in the reconcile (the dialog offers both): reference = whole job by default.
3. Decided in the reconcile (engineering): tolerance 3 %.

**Build steps.** (1) `PageInfo` fields, `analyze_pdf`, dict round trip, old-file test. (2) `read_page_sizes` and `fill_page_sizes` on open. (3) `select` kind `farkli`. (4) Mark painting and accessible text. (5) Git menu items and the Görünüm switch. (6) Dialog row and CLI.

---

## I-06 Low-confidence pages and values, with reasons and counts

**1. Problem.** After Değerler reads, staff go through 100 documents one by one with N, without knowing how many have trouble or why (rider "Kontrol" shows one orange mark, the reasons are only in the inspector, K-54, K-55). Principle: Never silent.

**2. Who and when.** Reviewers in Kontrol after "Değerleri oku". Needs read values; without them the row is disabled with the reason.

**3. Keyboard flow.** S, Down to "Kontrol gerekenler", Space on the reason boxes (all checked by default except Orta), Tab to "Sayfalar" (two radios), Seç. The selection then shows the pages; N / Shift+N keep jumping through documents. Reasons and counts are listed in the pane and repeated in the status line afterwards. Registry: `kontrol.sec` only.

**4. Screen sketch.** Parameter pane:
```
Kontrol gerekenler
[x] [!] Kontrol      4 değer
[x] [x] Okunamadı    3 değer
[ ] [-] Orta        12 değer
[x] [ ] Okunmadı     2 belge
[x]     Eksik sayfa  1 belge
Sayfalar: (o) Değerin sayfası ( ) Belgenin bütün sayfaları
9 belge, 11 sayfa
```
Every reason keeps its existing icon plus word (`degerler_model.LEVELS`: `triangle-alert` Kontrol, `circle-x` Okunamadı, `signal-medium` Orta, `clock` Okunmadı); only the Kontrol word uses the orange-family `check-text` colour it already has in Değerler; no second Kontrol colour, no new orange. Reuses checkbox rows in the dialog; at 150 % the counts move under the words.

**5. Data and core.**
- Core: uses `value_level` in `pipeline/templates/values.py`, which quick-wins I-17 adds and owns (`value_level(value: VariableValue | None)` -> `emin` / `orta` / `kontrol` / `okunamadi` / `okunmadi`, with `EMIN_AT = 0.90`; `make_cell` (`ui/degerler_model.py` L210) switches to it there). I-06 is built after I-17. This spec only switches `ui/sablon_read.py:level_of` (L35) to it where the meaning is the same, with a parity test.
- `select.evaluate(kind="guven", params={"levels": [...], "checks": [...], "pages": "deger"|"belge"})` uses `value_level`, `export.plan_export` checks (core, already the source of the rider) and a core copy of `Row.page_of` (`select.value_page(...)`; `degerler_model.Row.page_of` calls it). Match carries `reasons` with counts.
- No job-file field. The CLI `is sec guven` prints the same reasons and counts.

**6. Tests.** Core: `tests/test_select.py` documents with one flagged, one unread, one short filter group (`eksik sayfa`); reasons add up; `value_page` picks the page the box is on; `tests/test_template_read.py`/`test_degerler_model.py` parity of `value_level`. UI: dialog counts equal the selection; row disabled with no values. Screenshot: dialog with the five reasons. Failure it must catch: a document with an unread or flagged value that the selection misses, or a count that differs from the Değerler table.

**7. Risks.** Confidence is a ranking aid, not truth (findings-review-qc): the pane shows counts, not "X % wrong"; Emin values are never hidden by selecting. No new threshold: it follows the template and the 0.90 constant. Selecting by value page may select a page that is also the document's last page; fine. A document approved with Enter (İncelendi) is still listed if its check is open (B-034 is the separate question of what İncelendi means).

**Shortcut contract rows it adds:** none beyond S.

**Rules it must meet.** HIG-CON-03 (icon, word, never colour alone), DEC-IDN-01, DEC-CON-01/02, AUD-KBD-02, AUD-A11Y-01 (each count readable: "Kontrol, 4 değer"), AUD-TXT-01.

**Performance cost (800 pages, about 200 documents).** `plan_export` is already run after every job change (`kontrol.py:_job_changed` L706); the dialog calls `build_rows` once on open (about 200 rows times the template's variables) and caches it until the job changes, tens of milliseconds. Not on scroll.

**New Turkish text.**

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Kontrol gerekenler | criterion row | Those that need a check | existing |
| Kontrol, Okunamadı, Orta, Okunmadı | reason checkboxes | check, unreadable, medium, not read | existing |
| Eksik sayfa, Karışık şablon | reason checkboxes | missing page, mixed template | existing |
| {n} değer | count beside a reason | n values | draft |
| {n} belge | count beside a reason | n documents | draft |
| Sayfalar | label of the two radios | Pages | draft |
| Değerin sayfası | radio | The page the value is read from | draft |
| Belgenin bütün sayfaları | radio | All pages of the document | draft |
| {d} belge, {p} sayfa | live count | d documents, p pages | draft |
| Değerler henüz okunmadı | disabled reason | Values have not been read yet | existing |
| {d} belge seçildi: Kontrol {a}, Okunamadı {b} | status line after Seç | d documents selected with the reasons | draft |

**Owner decisions needed.**
1. Decided in the reconcile (a radio the user flips): default "Değerin sayfası".
2. Decided in the reconcile (a check box the user flips): Orta off by default.

**Build steps.** (1) (after I-17 has added `value_level`) switch `level_of` to it, with a parity test. (2) `select` kind `guven` and `value_page`. (3) Dialog row with reasons and counts. (4) Status text. (5) `is sec guven`.

---

## I-08 Remove filter (K-28), restore an emptied page (K-20), remove a template (K-52)

**1. Problem.** A wrong N cannot be taken back except by Geri al (K-28); an empty page dropped through the CLI cannot be restored in the window (K-20); "Şablonu kaldır" exists in core and CLI (`Job.remove_template`, `job.py:109`; `cli/jobs.py:325`) but not in Kontrol (K-52). Principle: The user decides; Never silent.

**2. Who and when.** Anyone using F or T, mid-session.

**3. Keyboard flow.** **Shift+F** = "Filtreyi kaldır" on the selected pages (pairs with F); **Shift+T** = "Şablonu kaldır" (pairs with T); "Boş sayfayı geri getir" has no key (rare, menu and context menu only, shown only when the job has `drop_empty` on). Registry: `kontrol.filtre_kaldir`, `kontrol.sablon_kaldir`, `kontrol.bos_geri_getir`; menu Araçlar, context menu after their partners. Each is one undo step ("Filtreyi kaldır", "Şablonu kaldır", "Boş sayfayı geri getir") with a toast and "Geri al" like Del. Nothing selected: "Önce sayfaları seçin." (existing). Selected pages without a filter or template: "Bu sayfalarda filtre yok." instead of a silent no-op. The inspector rows "Filtre uygula" / "Şablon uygula" in the selection card show "Her N sayfa" or "Şablon yok"; after removal they show "Filtre yok".

**4. Screen sketch.** No new region: three menu entries and the toast. Context menu order: Şablon uygula ›, Şablonu kaldır, Filtre uygula…, Filtreyi kaldır. Entries disabled (dimmed, still listed) when they would do nothing.

**5. Data and core.**
- `Job.remove_filter(page_ids)` (new, `pipeline/job.py` next to `apply_filter`): rewrites `job.filters` so each application loses these pages and applications left empty are dropped. No new file field and no new format; an older program opens the result. The split for those pages becomes "everything between two cuts" (`cuts._split`, L126 "later filters overwrite earlier ones" stays).
- `Job.remove_template` exists; it appends a `NO_TEMPLATE` application, so `values` for those documents become "okunmadı"-free again: confirm in the test that the Kontrol rider "değerler okunmadı" (K-56) disappears.
- `JobController.remove_filter`, `remove_template`, `restore_empty` (`ui/controller.py`, one `_edit` each, `Job.restore_empty` exists at `job.py:187`).
- CLI: `evrakci is filtre-kaldir ARALIK` (new, `cli/jobs.py`, next to `filtre`), reusing `Job.remove_filter`; `sablon-kaldir` and `sayfa --bos-geri-al` exist. Parity test: CLI and controller give identical `job_to_dict`.

**6. Tests.** Core `tests/test_job.py`: remove filter on part of a filter range splits it correctly, on all pages removes the application; `tests/test_cuts.py`: documents after removal. `tests/test_cli_edit.py`: `filtre-kaldir`. UI `tests/ui/test_kontrol_a.py`: F then Shift+F restores the previous documents, Ctrl+Z brings the filter back, status message when nothing to remove. Failure it must catch: Shift+F with no filter doing nothing without a word, and undo not restoring the filter.

**7. Risks.** Removing a filter from the middle of a range leaves two partial ranges whose short groups get "Eksik sayfa" (visible, never silent). Shift+T could be taken for "reverse of T"; its label says "Şablonu kaldır". Wrong keys cost an undo step only.

**Shortcut contract rows it adds:** `kontrol Shift+F kontrol.filtre_kaldir`, `kontrol Shift+T kontrol.sablon_kaldir`; `kontrol.bos_geri_getir` has no key.

**Rules it must meet.** AUD-KBD-02, HIG-WIN-19 (undo names the step), HIG-WIN-17 (no alert, undoable), HIG-CTL-09 (unavailable items dimmed), HIG-WIN-12, DEC-MOT-02 (no motion on repeat).

**Performance cost (800 pages).** One snapshot edit like every other edit (job dict before and after, about 1 to 2 ms per 800 pages); same recompute of documents as F.

**New Turkish text.**

| String | Where | Meaning in English | Status |
|---|---|---|---|
| &Filtreyi kaldır | menu Araçlar, context menu | Remove the filter | draft |
| Şablonu &kaldır | menu Araçlar, context menu | Remove the template | draft |
| Boş sayfayı geri &getir | menu Araçlar, context menu | Bring the blank page back | draft |
| Filtre kaldırıldı, {n} sayfa. | toast | Filter removed, n pages | draft |
| Şablon kaldırıldı, {n} sayfa. | toast | Template removed, n pages | draft |
| Boş sayfa geri getirildi. | toast | Blank page restored | draft |
| Bu sayfalarda filtre yok. | status line | No filter on these pages | draft |
| Bu sayfalarda şablon yok. | status line | No template on these pages | draft |
| Atılmış boş sayfa yok. | status line | No dropped blank page | draft |
| Filtre yok | inspector row value | No filter | draft |
| Filtreyi kaldır (undo name), Şablonu kaldır, Boş sayfayı geri getir | undo stack | undo step names | draft |
| Şablon yok | inspector row value | No template | existing |
| Önce sayfaları seçin. | status line | Select pages first | existing |

**Owner decisions needed.**
1. (README O-5, with the other Kontrol keys) Keys Shift+F and Shift+T (recommended) or menu-only.
2. (README O-4) Restore-blank only appears when the job has `drop_empty` on (set in the CLI): fine (recommended), or add the global switch (see I-03 decision 2).

**Build steps.** (1) `Job.remove_filter` with tests. (2) Controller methods with undo names. (3) Menu, context menu, registry, contract rows. (4) Messages and inspector rows. (5) CLI `filtre-kaldir`.

---

## Check against the product (whole group)

- Never silent: Pass. Every selection says how many, reasons are counted, marks have icon and word; nothing changes a job without an undo step. `index.xlsx` unchanged.
- No built-in document kinds or fields: Pass. Criteria use the job's own pages and the user's template variables; nothing names a document type.
- Keyboard: Pass after the build. Every action has a key or a menu path; Ctrl+Space and Alt+arrows fix a real gap (tested today: Ctrl+Space selects nothing).
- Colour: Pass. Orange stays Kontrol only (riders, existing Kontrol word); I-04's mark is neutral with icon and word; text at least 13 px.
- Layout: Pass. One dialog; no new region; 1366x768 at 100 % and 150 % stacked.
- Copy: Pass, needs owner review of the "draft" strings. Words are "Seç", "Ölçüt", "Tek/Çift sayfalar", "Dikey/Yatay"; "Kontrol", "Emin/Orta/Okunamadı/Okunmadı", "İncelendi" untouched. I did not look the sector wording up online in this run; the words follow Windows and Office Turkish as I know them.
- Local-first: Pass. No network, no new dependency.

## Owner decisions, summary

Before the reconcile: 12. After: 5, numbered O-1 to O-5 in `specs/README.md` (odd/even basis, guide-tab click, marks on by default, blank-page switch, the Kontrol keys). The other 7 were decided in the reconcile and are marked above.
