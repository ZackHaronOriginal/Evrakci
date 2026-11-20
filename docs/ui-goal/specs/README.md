# Phase 5 specs: how the four fit together

Four specs were written at the same time by four agents, so they overlapped. This page makes them
agree. It was checked on 2026-11-20. Nothing is built yet: each spec waits for the owner's yes
(decisions.md, "Owner answers: Phase 5 build order and rules").

| Letter | File | Ideas |
|---|---|---|
| A | `kontrol-filters.md` | I-09, I-03, I-04, I-06, I-08 (choose pages in Kontrol) |
| B | `quick-wins.md` | I-17, I-19, I-21, I-22, I-23, I-28, I-47 (small fixes) |
| C | `qr-saved-filters.md` | I-01, I-07 (QR content, saved filters) |
| D | `disa-aktar.md` | I-35, I-38, I-39, I-40 (Dışa Aktar) |

A few words used below:
- **Core**: the part of Evrakçı that does the actual work on the files (`src/evrakci/pipeline/`).
  The window and the command line both use it, so they always agree.
- **CLI** (command line): the `evrakci` command typed in a terminal. It must give the same result
  as the window.
- **Job file**: the file where Evrakçı saves a job (pages, cuts, values) so it can be opened again.

---

## 1. Build order

Smallest and safest first. Each step is built and tested on its own. A step marked "needs" waits
for the step it names.

**Stage 1: window only, no core change**
1. B I-47 keep the window responsive: background work with a loading view (shared `run_background` helper and loading card). *Needed by step 17.*
2. B I-21 carry the document between Kontrol and Değerler (also fixes bug B-012).
3. B I-19 every section's reading in the value card.

**Stage 2: small core changes for Değerler and Şablonlar**
4. B I-17 mark the wrong cell. Adds the shared `value_level`. *Needed by step 11.*
5. B I-23 "Okunana dön".
6. B I-22 warn on an empty required value.
7. B I-28 weakest examples first.

**Stage 3: choosing pages in Kontrol (A)**
8. A I-08 remove filter / template, restore a blank page (needs nothing new from A).
9. A §0 + I-09 the "Seç…" dialog, `pipeline/select.py`, this document / odd / even, Ctrl+Space.
   *Needed by steps 10-12 and 18-19.*
10. A I-03 blank pages (needs 9).
11. A I-06 pages that need a check (needs 4 and 9).
12. A I-04 page size and orientation (needs 9). First new job-file field; sets the pattern C reuses.

**Stage 4: Dışa Aktar (D)**: does not depend on A or C, so it can be built in parallel with stage 3.
13. D I-40 step 1: bug B-003 (PDF/A failure counted as Kontrol), only after O-18.
14. D I-35 "Belge no", job name and export time in index.xlsx.
15. D I-40 "Kontrol gerekenler" sheet (needs 13, 14).
16. D I-39 rename preview with the scan file name.
17. D I-38 print preview (needs 1).

**Stage 5: QR content and saved filters (C)**: last because it changes page analysis and the
template file.
18. C I-01 select and cut by QR content (needs 9; build after 12 so the old-job pattern exists).
19. C I-07 saved filters as chips (needs 9-12 and 18).

## 2. Shared pieces and their owner

One spec owns each shared piece; the others point to it.

| Shared piece | Owner | Used by | What was settled |
|---|---|---|---|
| `pipeline/select.py`: `Criterion(kind, params)`, `evaluate`, `combine`, `Match` | A §0 | C I-01 (kind `qr`), C I-07 (`select_pages`) | C first had its own `select.py` design and a `select_pages(job, filters)` with "settings"; now C adds a kind and `select_pages` on top of A's `evaluate`/`combine`. A saved filter = one named criterion (A had said "a list of criteria"). |
| "Sayfaları seç" dialog (`SelectDialog`), entry "Seç…" (S), status line "{n} sayfa seçildi." | A §0 | C I-01 | C first had its own QR dialog with "Sayfaları seç" as its button and a "Sayfaları seç ▾" command-bar menu. Now Q opens A's dialog on the "QR içeriği" row; one dialog, title "Sayfaları seç", button "Seç", status "{n} sayfa seçildi ({ölçüt})." |
| CLI `evrakci is sec <iş> <ölçüt>` | A §0 | C (`qr`, `--kes`, `--sablon`, `--filtre`) | C had a separate `is qr-sec` and a second `is sec` with another shape; now one command. A's form gained the missing `<iş>` argument. |
| `value_level` + `EMIN_AT = 0.90` in `pipeline/templates/values.py` | B I-17 | A I-06, `ui/sablon_read.level_of` | A put it in `values.py` with 4 levels, B in `review.py` with 5. Now one function, in `values.py` (it has no imports, so the select module and the UI can use it), with all 5 levels including "okunmadı". |
| Job file format | this page | A I-04, C I-01, D I-35 | A and C kept version 2; D wanted version 3. Version 3 would stop older Evrakçı versions opening the job. **Plan: stays version 2.** Every new field (`width_mm`/`height_mm`, `qr_texts`, `last_export`) is added with a default, so old files open in the new app and new files open in older apps. |
| Re-reading old jobs | A I-04 `fill_page_sizes` (automatic, no rendering), C I-01 `reread_qr` (on demand, renders) | each other | Kept as two helpers because their cost differs; both use `JobStore.batch_file`; one shared old-job test fixture, made by whichever is built first (I-04). |
| `run_background` + `LoadingCard` (`ui/workers.py`, `ui/loading.py`) | B I-47 | D I-38 | Replaces the dropped `motion.wait_cursor`: D's 800-row preview is built through it (or shows its own "Önizleme hazırlanıyor…" band) instead of a busy cursor. |
| `ExportItem` fields `sources`, `name_note`, `pdfa_note` | D (C1) | D I-39, I-40 | `pdfa_note` (from the B-003 fix) was missing from D's shared list. |
| Kontrol keys | this page (table below) | A, B, C | D was proposed twice; see section 3. |
| Saved-filter chips | C I-07 | A | A first put the chips inside its dialog; they are a row above the timeline (C), using A's core. |

## 3. Keys

Checked against `shortcut-contract.tsv` and the Turkish keyboard rules (no Ç Ş Ğ İ Ö Ü, no I, no
Ctrl+Alt). `audit_shortcuts.py --check` today: 0 problems (nothing new is wired yet).

| Tab | Key | Command | Spec |
|---|---|---|---|
| Kontrol | S | Seç… (Sayfaları seç) | A |
| Kontrol | B | Bu belgeyi seç | A |
| Kontrol | Ctrl+Space | Sayfayı seçime ekle / çıkar (local) | A |
| Kontrol | Alt+Left / Alt+Right | Seçimi bozmadan git (local) | A |
| Kontrol | Shift+F / Shift+T | Filtreyi kaldır / Şablonu kaldır | A |
| Kontrol | D | Değerlerde aç | B I-21 |
| Kontrol | Q | QR içeriğine göre seç… | C |
| Kontrol | Shift+K | Seçili sayfaların önünde kes | C |
| Kontrol | Ctrl+Shift+F | Kayıtlı filtreler | C |
| Değerler | K / R | Kontrol'de aç / Okunana dön | B |
| Değerler | Alt+1 … Alt+4 | pick a reading (editor only, local) | B I-19 |
| Şablonlar | N / Shift+N / Ctrl+L | next / previous weak example, list | B I-28 |
| Dışa Aktar | Ctrl+Shift+A / Ctrl+Shift+C | Adları karşılaştır / Ad listesini kopyala | D I-39 |
| Dışa Aktar | Ctrl+Shift+R | Kontrol listesini kaydet… (only if O-19 is yes) | D I-40 |
| Dışa Aktar | Ctrl+P | changes to "open print preview" (only if O-16 is yes) | D I-38 |

Settled conflict: **D on Kontrol** was "Değerlerde aç" (B I-21) and "Sonraki farklı sayfa" (A I-04,
with Shift+D). D stays with "Değerlerde aç", because it pairs with K on Değerler (each key is the
first letter of the tab it goes to). "Sonraki / Önceki farklı sayfa" are now in the Git menu and the
command palette without a key. All other proposed keys were free and used once.

At build time: B, K, R, N and Shift+N have a different label on another tab, so each needs a
page-specific line in `shortcuts.md`, or the audit fails. The "Tek tuşlu kısayollar" list in
`shortcuts.md` gains S, D, Q.

## 4. Core changes in total

21 core changes (one more if O-19 is yes) and 12 command-line changes. The job file version stays 2
and the template file version stays 1; every new field is optional.

- **A (5 core, 2 CLI):** `pipeline/select.py` (kinds belge, tek, cift, bos, farkli, guven;
  `value_page`); page width and height in `PageInfo` and `analyze_pdf`, `read_page_sizes`; the two
  fields in the job file; `JobStore.fill_page_sizes`; `Job.remove_filter`. CLI: `is sec`,
  `is filtre-kaldir`.
- **B (4 core, 2 CLI):** `values.value_level`; `review.set_value(required=)`; `review.can_revert`;
  `templates/read.weakest_examples` (with `flagged_count` moved in). CLI: new wording in
  `is degerler`; `is deger` messages.
- **C (7 core, 5 CLI):** `PageInfo.qr_texts` and `_read_qr_texts`; `qr_texts` in the job file;
  kind `qr` with `match_qr`, `qr_values` and a core Turkish case-fold helper; `Job.add_cuts`;
  `JobStore.reread_qr`; `SavedFilter` in the template file; `select_pages`. CLI: `is sec qr`,
  `--kes`, `is qr-oku`, `is sec --sablon/--filtre`, `sablon filtre-ekle/filtre-sil/filtreler`
  (plus QR text in `is goster`).
- **D (5 core, 3 CLI; +1 with O-19):** `ExportItem.sources/name_note/pdfa_note` (and the B-003
  fix); notes made in `plan_export`; `plan_names`; `write_index` ("Belge no", sheets `Özet` and
  `Kontrol gerekenler`); `Job.last_export`. CLI: name note per file, `--onizle`, a last line naming
  the check list. Optional: `write_check_report` and `--kontrol-listesi`.

index.xlsx changes only through D: one new column and two new sheets.

## 5. Decisions for the owner

19 choices (the four specs listed 42; 23 were duplicates or engineering details that are now
decided in the specs, see section 6). Each says what changes for you, the options, and a
recommendation.

### A: choosing pages in Kontrol

- **O-1 "Odd / even pages": counted how?** Picking every front or every back of a two-sided scan.
  Options: (a) count from the start of each document, (b) count by the page number in the whole
  job. **Recommended: (a)**, because the backs of a two-sided scan follow each document.
- **O-2 Click on a document's tab selects the whole document?** Today that click only moves to the
  document. Options: (a) keep it as it is, (b) the click selects all its pages. **Recommended: (a)**:
  the B key and the right-click menu do it, and a click staff already know does not change.
- **O-3 "Looks different" marks shown from the start?** A sideways page or a smaller page gets a
  small mark with a word ("Yatay", "Farklı boyut"). Options: (a) on by default, one click off in
  Görünüm, (b) off until you ask. **Recommended: (a)**: an odd page should never hide.
- **O-4 A switch to drop all blank pages at once?** Options: (a) no switch; you select the blank
  pages (with a count) and press Del, which can be undone, (b) also add a setting that removes blank
  pages for the whole job. "Boş sayfayı geri getir" then appears only for jobs where blank pages were
  dropped from the command line. **Recommended: (a)**: what is removed stays visible and undoable.
- **O-5 New keys in Kontrol for choosing pages:** S (open "Seç…"), B (this document), Ctrl+Space
  (add or remove one page), Alt+Left / Alt+Right (move without losing the selection), Shift+F /
  Shift+T (remove filter / template). Options: (a) these keys, (b) menu only. **Recommended: (a)**:
  without Ctrl+Space and Alt+arrows, scattered pages cannot be picked by keyboard at all. All
  one-letter keys switch off with "Tek tuşlu kısayollar".

### B: quick wins

- **O-6 How to mark the value that needs a check, inside the Değerler table.** Options: (a) an icon
  in the cell; the word is in the tooltip and in the row's Güven column, (b) icon plus the word
  "Kontrol" in the cell (wider columns, busier table). **Recommended: (a)**: a clean job looks the
  same as today.
- **O-7 One word for "needs a check" on the command line too.** Today `is degerler` prints
  "[okunamadı]" even when something was read. Options: (a) print "[kontrol, öneri: …]" when
  something was read and "[okunamadı]" only when nothing was, (b) keep today's text.
  **Recommended: (a)**: one vocabulary everywhere. Only matters if someone has a script that reads
  this text.
- **O-8 Pick another reading instead of the suggestion.** The value card lists every reading.
  Options: (a) click a reading or press Alt+1 … Alt+4 in the editor to take it (one undo step),
  (b) the list is for reading only. **Recommended: (a)**: fewer keystrokes, still undoable.
- **O-9 When you clear a required value and press Enter.** Options: (a) it is saved as "Kontrol"
  with the reason, and a short note says so, (b) it is refused and the editor stays open.
  **Recommended: (a)**: nothing is lost and N finds it again.
- **O-10 New keys from the quick wins:** D in Kontrol "Değerlerde aç", K in Değerler "Kontrol'de
  aç", R in Değerler "Okunana dön", N / Shift+N / Ctrl+L in Şablonlar for the weakest examples.
  D was also wanted for "Sonraki farklı sayfa" (O-3's pages); that command then has no key (menu
  only). Options: (a) these keys, (b) menu only. **Recommended: (a)**: D and K are the first letter
  of the tab you go to, and N already means "next one to check".
- **O-22 Save edits in the background (B I-47 step 5).** A background saver keeps a slow network
  folder from stalling each edit. Options: (a) yes, with "Kaydediliyor…" and a flush on close,
  Ctrl+S, export and job switch, (b) no, saving stays on the window thread (0.6 ms measured on a
  local disk). **Recommended: (a) only if jobs live on network folders, else (b)**; depends on where
  staff keep jobs, which no measurement here can tell.

### C: QR content and saved filters

- **O-11 Call it "QR" or "karekod" on screen?** "Karekod" is the common Turkish word. Options:
  (a) "QR", (b) "karekod". **Recommended: (a)**: the app already says "QR ayıraç". (The Turkish
  terms check in `research/turkish-terms.md` may add evidence.)
- **O-12 Cutting in front of many selected pages at once.** Options: (a) a new key Shift+K; K keeps
  cutting at one page, (b) K cuts in front of every selected page when several are selected.
  Also adds Q (select by QR content) and Ctrl+Shift+F (go to the saved filters).
  **Recommended: (a)**: K does what staff know.
- **O-13 Where saved filters are kept, and the new chip row.** Saved filters appear as small
  buttons ("chips") in a new row between the command bar and the pages; this row is new in the
  approved Kontrol layout and is only shown when there is something in it. Options: (a) kept with
  the template, so every job of that kind has them, (b) also a separate list per job.
  **Recommended: (a)**: set up once, used on every job of that kind.
- **O-14 Which template's saved filters show** when the selected pages have mixed templates or
  none. Options: (a) those of the template shown in the side panel; with none, the row offers
  "Şablon seçin", (b) all templates' filters together. **Recommended: (a)**: one clear source.

### D: Dışa Aktar

- **O-15 Where the new "Belge no" column goes in index.xlsx.** Options: (a) first column, (b) after
  the fixed columns, before the variables. **Recommended: (a)**: it is the key to the file name.
  Anyone with Excel macros on the sheet must update them either way.
- **O-16 Ctrl+P opens a print preview first.** Options: (a) Ctrl+P shows the preview, Enter then
  prints, (b) Ctrl+P prints as today; the preview gets another way in. **Recommended: (a)**: no
  wasted paper; one extra key press.
- **O-17 What "old name" means in the rename preview.** A document has no earlier name of its own.
  Options: (a) the scan file it came from ("Kaynak"), (b) the numbered name (`belge_007`), (c) no
  old name. **Recommended: (a)**: it ties each new file to the paper batch.
- **O-18 A PDF/A failure: "Bilgi" or "Kontrol"?** Today the list says Bilgi but the result card and
  index.xlsx say Kontrol (bug B-003). Options: (a) Bilgi everywhere; the PDF/A column still says
  "hayır", (b) Kontrol everywhere. **Recommended: (a)**: the document itself is fine; only the
  archive format check failed.
- **O-19 Save the "needs a check" list before exporting?** The list is always a sheet in index.xlsx
  after export. Options: (a) only that sheet, (b) also a command (Ctrl+Shift+R) to save it on its
  own before exporting. **Recommended: (a)** for now: the supervisor reads the finished export.

### Wording (from `research/turkish-terms.md`)

- **O-20 Four new words, changed to what Turkish software uses?** "Seç…" → "Ölçüte göre seç…",
  "Seçimin içinde ara" → "Seçimle kesiştir", "kalıp (* ve ?)" → "joker karakterli (* ve ?)",
  "Atılmış boş sayfa" → "Silinen boş sayfa". Options: (a) take all four, (b) keep the drafts.
  **Recommended: (a)**: they match LibreOffice and other Turkish tools.
- **O-21 Existing words that other software says differently** (no change unless you want one):
  "filtre" (LibreOffice and GIMP: "süzgeç"), "Kayıtlı filtreler" (Paperless: "kaydedilmiş"),
  "Yön" (LibreOffice: "Yönelim"). Options: (a) keep the app's words, (b) change. **Recommended:
  (a)**: staff already know "filtre", and the app should not change words it already uses.

## 6. Decided in the reconcile (the owner may still object)

Not real owner choices (engineering, or a default the user can change on the spot), so they were
decided and written into the specs:
- A: Alt+arrows folded into O-5; blank limit stays 0,3 % (as CLI and guide); "different" pages
  compared with the whole job by default (the dialog offers "each document"); 3 % size tolerance;
  I-06 selects the value's page and leaves Orta off by default (both changeable in the dialog).
- B: readings list always shown for 2+ readings, at most 4 rows; no extra button in the Değerler
  side panel; "*" marks required columns (as in Şablonlar); "Okunana dön" wording goes to the
  Turkish terms check; `flagged_count` moves to the core; busy cursor only above a measured job size.
- C: A's criterion model is the shared core (was C decision 1); old jobs get "QR metnini yeniden
  oku" (was 2); a chip's settings are fixed in v1 (was 3); chips only select (was 4).
- D: export time is kept in the job file, format stays 2 (was D-1); dates read "20.11.2026 14:32"
  on paper and in the sheet (was D-4; the sheet had ISO); the scan-file column is off by default
  behind a toggle (was D-6).

## 7. Already decided by the owner (do not ask again)

From decisions.md, 2026-11-20:
- Build first: Kontrol filters (I-03, I-04, I-06, I-08, I-09); quick wins (I-17, I-19, I-21, I-22,
  I-23, I-28, I-47); QR content and saved filters (I-01, I-07); Dışa Aktar (I-35, I-38, I-39,
  I-40). I-50 to I-55 are later.
- New Turkish text is written by the run after checking how Turkish software words the same thing,
  and listed in each spec.
- Each spec needs the owner's approval before it is built.
- D13 is lifted: features may change the core and the CLI, with core tests, a check that older job
  files still open, a check that window and CLI give the same output, and an agent review.

Earlier decisions these specs keep: one status vocabulary (Emin / Orta / Kontrol / Okunamadı;
İncelendi / İncelenmedi), N / Shift+N "Sonraki / Önceki kontrol", U, Enter = "Belgeyi onayla",
undoable delete, orange only for Kontrol (D1), invert selection (key I) deferred.

## 8. Checks against code and decisions

- Code citations spot-checked: A 12 (4 wrong line numbers fixed), B 21 (2 fixed), C 17 (4 fixed),
  D 16 (2 fixed: `export.py:21`, and "Kontrol gerekenler" lives in `degerler_model.py:47`).
- Nothing silently reopens a decision after the fixes. Points that touch earlier decisions are now
  explicit owner choices: the new chip row in the approved Kontrol layout (O-13), the Ctrl+P change
  (O-16), the CLI wording (O-7). D's job format 3 would have stopped older app versions opening
  jobs; it is removed. A's new "Seç…" icon in the Kontrol command bar follows direction A's rule
  (icon button with tooltip) and is part of approving spec A.
- Wording left to the Turkish terms check: list column "Kaynak" (scan file, D I-39) sits next to the
  sheet column "Kaynak sayfalar" (page numbers).
