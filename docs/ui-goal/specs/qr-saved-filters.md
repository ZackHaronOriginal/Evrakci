# Spec group C: QR content select and saved filters (I-01, I-07)

Status: draft for owner approval. Written 2026-11-20. No code is changed by this file.
D13 is lifted (owner, 2026-11-20): core and CLI changes below are by design, not minimal hooks.

**Reconciled with A, B and D (2026-11-20).** Build order, shared pieces, the Kontrol key table and its decisions O-11 to O-14 are in `specs/README.md` (O-12's keys Shift+K and Ctrl+Shift+F, O-13 and O-14 decided by evidence on 2026-11-20; O-11 and the Q key wait with I-01, which is on hold). A owns `pipeline/select.py` (`Criterion`, `evaluate`, `combine`), the "Sayfaları seç" dialog and the CLI command `is sec`; this file adds the kind `qr`, `select_pages` (AND of saved filters), `--kes`, `--sablon` and `--filtre`. Job files stay version 2 (additive fields only).
Sources: `ideas-ranking.md` rows I-01 and I-07, `research/findings-splitting.md`, `research/findings-filtering.md`, `decisions.md` (D1, D13, "Phase 5 build order and rules"), `shortcut-contract.tsv`, the code cited below.

## Dependency on group A (selection model)

Group A (`specs/kontrol-filters.md`, ideas I-03, I-04, I-06, I-08, I-09) is written in parallel. This group needs from it, expressed in terms of the idea rows:
- **One entry point** that "selects pages by a property" (I-03 blank, I-04 size/orientation, I-06 low confidence, I-09 this document / odd / even). C adds one more property to it (I-01 "QR içeriği") and does not make a second entry.
- **Selection is the only result.** Every such filter ends as a set of page ids in the timeline selection (`KontrolScreen.selected_ids`, `src/evrakci/ui/kontrol.py:248`), with a live count. Cut, delete, rotate, template then act on that selection as today.
- **A filter is a small description**: a kind name plus its settings (for example blank + threshold), evaluated in the core (`pipeline/select.py`, D13 lifted) so the CLI gives the same count. I-07 stores exactly that description. Settled in the reconcile: A defines it as `Criterion(kind, params)` in `pipeline/select.py` (kontrol-filters §0); no owner decision.
- **Not the "every N pages" filter.** `F` / "Filtre uygula…" (`kontrol.py:300`, `kontrol_dialogs.py:39`) keeps its meaning; it is stored in the job (`job.py:FilterApplication`). I-07 chips are different: they only select pages and are stored with a template.

Until A is approved and built, C cannot be built. Build order: A, then C step 1 (QR text, no UI), then C step 2 onward.

---

# I-01: Select and cut by QR content (core change C-1)

## 1. Problem
"Our forms carry a pre-printed number such as KAP-0412 in a QR code, but Evrakçı only reacts to its own separator sheets." Today only text starting with `EVRAKCI-AYIRAC` counts (`separator.py:22`, `analyze.py:_is_separator`), and every other decoded text is thrown away at analysis, so staff cannot jump to or cut at "all QR starting with KAP-". Principle: Less paper handling (no extra separator sheets), The user decides what documents contain (the prefix is typed by the user, nothing is built in).

## 2. Who and when
Staff of chambers that use numbered forms, once per job, in Kontrol after loading. Setup is the same person. Rare for the others; costs them nothing.

## 3. Keyboard flow
1. Ctrl+2 to Kontrol. Press `Q` (action `kontrol.qr_sec`, "QR içeriğine göre seç…", menu Araçlar): it opens A's "Sayfaları seç" dialog with the row "QR içeriği" chosen (S, then the row, reaches the same place).
2. Parameter pane of that row: field "QR metni", mode list "ile başlar / içerir / joker karakterli (* ve ?)", live line "12 sayfa eşleşti, 3 farklı değer". Up/Down changes mode, Enter = "Seç" (A's primary button), Esc = "Vazgeç". A's "Seçimi değiştir / Seçime ekle / Seçimin içinde ara" apply as for every row.
3. The matching pages become the selection; the timeline scrolls to the first one; status line says "12 sayfa seçildi (QR: KAP-*)". Focus returns to the timeline.
4. `K` today cuts only at the current page (K-14). New action `kontrol.kes_secili` ("Seçili sayfaların önünde kes", Shift+K): one undoable step, "Kesim ekle, 12 sayfa". Pages that already cut, deleted pages and the first kept page are skipped and counted in the toast ("2 sayfada zaten kesim var").
5. Ctrl+Z undoes the whole cut step.
Mouse: Araçlar menu, inspector card "Seçim", context menu. Without the dialog: a QR badge on the thumbnail (below) can be clicked to select all pages with the same text.

## 4. Screen sketch (1366x768, 100 %)
```
Kontrol command bar:  [Kes] [Birleştir] [Filtre uygula…] [Ölçüte göre seç…]  <- A's icon button; its dialog gains the row "QR içeriği"
+-------------------------+     Inspector card "Seçim: 12 sayfa (QR: KAP-*)"
| [page thumbnail]        |       Şablon uygula        >
|  ▣ QR · KAP-0412        |       Filtre uygula        >
+-------------------------+       Seçili sayfaların önünde kes
```
- New small badge on a page that has non-separator QR text: qr-code icon + "QR" + the first 12 characters of the text (neutral text colour, never orange; orange stays Kontrol only). Painted in `kontrol_paint.py` beside the existing page decorations; hidden when the thumbnail is too small (zoom slider).
- Cut made this way is an ordinary manual cut (scissors tab, dotted lip, K-13). No new cut kind: fewer shapes to learn.
- Reuses: A's `SelectDialog` (one more criterion row), inspector card `Seçim` (`kontrol_inspector.py:343`), toast. At 150 % text the dialog grows in height only; high contrast uses theme tokens.

## 5. Data and core changes (D13 is lifted; core change C-1, CLI included)
Design: the selection logic lives in the core so the window and `evrakci` give the same pages and the same count.
- `pipeline/analyze.py`: `PageInfo` (line 29) gets `qr_texts: tuple[str, ...] = ()` (A's I-04 adds `width_mm`/`height_mm` the same additive way); `_is_separator(image)` (line 46) becomes `_read_qr_texts(image)` (max 4 codes per page, each cut at 200 characters), and `is_separator` is computed from it with the unchanged `is_separator_payload`. The text was already decoded by `zxingcpp.read_barcodes` and thrown away; no second read.
- `pipeline/job.py`: `job_to_dict` (the `pages` entry) writes `qr_texts`; `job_from_dict` (line 259) reads `p.get("qr_texts", [])`. `JOB_FORMAT_VERSION` stays 2 (additive): older job files open unchanged, with no text.
- In A's `pipeline/select.py` (A owns the module): the `evaluate` kind `qr` (params `mode`, `query`) calls `pages_matching_qr`; `match_qr(text, mode, query)` (modes "starts", "contains", "mask" with `*` and `?`; Turkish case folding moved from `ui/actions.py:fold` into a core helper that `actions.fold` re-uses) and `pages_matching_qr(job, mode, query) -> list[str]` (page ids in job order, separators and deleted pages left out), plus `qr_values(job) -> dict[str, int]` (distinct texts with page counts, for the dialog list).
- `Job.add_cuts(page_ids) -> tuple[list[str], list[str]]` in `job.py`: adds a cut before each page through the existing `add_cut` rules and returns (added, skipped) instead of raising; the window and the CLI both call it. The window wraps it in one undo step via `JobController.run` ("Kesim ekle, N sayfa").
- Old jobs: `JobStore.reread_qr(job, batch_id, progress)` in `pipeline/store.py` re-reads only the QR texts of one batch from its stored PDF (`batch_file`, line 55), without touching cuts or edits. The window offers it as "QR metnini yeniden oku" on the dialog note; the CLI as `evrakci is qr-oku <iş> [parti]`.
- CLI (`cli/jobs.py`, near `cut`/`apply_filter`, lines 177-209): A's `evrakci is sec <iş> qr --baslar|--icerir|--kalip <metin>` (no separate `qr-sec` command) prints the matching pages (positions, `positions_text`) and the count; `--kes` (owned here) also adds the cuts via `add_cuts`. `evrakci is goster` shows the QR text of non-separator QR pages. Existing commands and their output are unchanged.
- No change to `cuts.py`, export or `index.xlsx`. Privacy: the text is only in the local job file.

## 6. Tests
- Core `tests/test_analyze.py` (synthetic QR pages from `tests/fakes.py`): text kept, separator still detected, a non-separator QR is not a separator, 200-character cut. `tests/test_job.py`: round trip; an older job dict without `qr_texts` still loads and behaves as before. New `tests/test_select.py`: modes, mask `KAP-04??`, Turkish folding (dotted/dotless I), separators and deleted pages left out, `add_cuts` added/skipped. `tests/test_store.py`: `reread_qr` fills texts and leaves edits alone. The one failure to catch: detected separators or documents change for an existing job.
- CLI `tests/test_cli_edit.py`: `is sec qr` and `--kes` give the same page list and documents as the window path on the same job; old commands' output identical (golden lines).
- UI `tests/ui/test_kontrol_qr.py` (offscreen): Q opens the select dialog on the QR row; its count line equals the core count, selection set, Shift+K is one undo step, skip toast.
- Shortcuts: registry, `shortcut-audit --check`, key presses for `Q` and `Shift+K`. Screenshots: `states` shot "kontrol-qr-badge".

## 7. Risks and open questions
- Silent-wrong: a stray QR (delivery sticker) selected by "içerir". Mitigation: the dialog lists the distinct values with counts so staff see what matches; the cut is never automatic.
- 800 pages: text compare over a dict, under 5 ms; analysis time unchanged (decode already happens).
- Turkish: mask uses `*` and `?` only (no regex, for non-technical staff). Case and dotted/dotless I folded.
- Scope: separator "keep the page" (I-02) and "split when the value changes" (DocuWare) are not in this spec. A cut here keeps the QR page as first page of the new document.
- Badge shows only on non-separator QR pages; a page with several QR codes shows the first plus "+2".

## Shortcut contract rows it adds
| tab | key | action_id | label | undo |
|---|---|---|---|---|
| kontrol | Q | kontrol.qr_sec | QR içeriğine göre seç… | selection only, Ctrl+Z not needed |
| kontrol | Shift+K | kontrol.kes_secili | Seçili sayfaların önünde kes | yes, one step |
Both single-key (off while typing, off in "Tek tuşlu kısayollar" setting). Q and Shift+K are free on Kontrol (checked against `shortcut-contract.tsv`; Ctrl+Q stays app.cikis). Fill the other columns like the existing `kontrol.kes` row.

## Rules it must meet
AUD-KBD-02 (keyboard only), AUD-A11Y-01 (dialog, badge names), DEC-IDN-01 (badge not orange), HIG-CON-03 (icon + word), DEC-TYP-01 (badge text at least 13 px), AUD-HIT-03, AUD-TXT-01 (150 %), DEC-THM-01, HIG-CTL-05 (button "QR içeriği…" ends with ellipsis), HIG-WIN-19 (undo names the action).

## Performance cost (800 pages)
Analysis: none extra. Job file: about 800 short strings at most. Select: one pass, under 5 ms. Badge paint: only visible rows, text cached per row.

## New Turkish text
| string | where | meaning in English | status |
|---|---|---|---|
| QR içeriğine göre seç… | menu, command bar, palette | Select by QR content | draft |
| QR içeriği | criterion row in A's dialog, badge | QR content | draft |
| QR metni | dialog field | QR text | draft |
| ile başlar | dialog mode | starts with | draft |
| içerir | dialog mode | contains | draft |
| joker karakterli (* ve ?) | dialog mode | pattern (* and ?) | draft (O-20: was "kalıp"; LibreOffice Turkish "Joker Karakterleri") |
| Örnek: KAP-04?? | dialog hint | example mask | draft |
| {n} sayfa eşleşti, {m} farklı değer | dialog live line | n pages matched, m distinct values | draft |
| Sayfaları seç | dialog title (owned by kontrol-filters §0; primary button there is "Seç") | Select pages | draft |
| {n} sayfa seçildi (QR: {text}). | status line; the form of A's "{n} sayfa seçildi ({ölçüt})." | n pages selected | draft |
| Seçili sayfaların önünde kes | menu, button | Cut before the selected pages | draft |
| Kesim ekle, {n} sayfa | undo step, history | Add cuts, n pages | draft |
| {n} sayfada zaten kesim var | toast | n pages already have a cut | draft |
| Bu iş, QR metni kaydedilmeden önce yüklendi | dialog note | This job was loaded before QR text was kept | draft |
| QR metnini yeniden oku | dialog button | Read the QR text again | draft |
| Vazgeç | dialog | Cancel | existing (`kontrol_dialogs.py:28`) |
| Seçim | card title | Selection | existing (`kontrol_inspector.py:348`) |
| QR ayıraç | wording kept for the separator sheet | QR separator | existing (`timeline.py:218`) |
Sector check: Turkish scanner manuals (Canon, Xerox, Brother pages found by search) use "belge ayırma" and "boş sayfa çıkarma" but nothing on QR/barcode separators; "karekod" is the common Turkish word for a QR code, but the app already says "QR ayıraç", so "QR" is kept for consistency. Owner may prefer "karekod" (decision 3).

## Check against the product
- Never silent: Pass (counts, skipped cuts and old-job note are shown; cuts are never automatic).
- No built-in kinds or fields: Pass (the prefix is typed; no "KAP" in code).
- Keyboard: Pass (Q, Shift+K, dialog fully keyboard).
- Colour: Pass (neutral badge, icon + word).
- Layout: Pass (dialog small; badge hidden at small zoom).
- Copy: Pass, wording draft (see sector note).
- Local-first: Pass (no new dependency; `zxingcpp` already used).

## Owner decisions needed
1. Settled in the reconcile (engineering): yes, A's `Criterion` in `pipeline/select.py`.
2. Decided in the reconcile: old jobs get the "QR metnini yeniden oku" command (`JobStore.reread_qr`), on demand.
3. (README O-11) Word "QR" or "karekod" in the UI. Recommended: "QR" (matches "QR ayıraç").
4. O-12, the non-QR part. **Decided by evidence (T3, 2026-11-20; sources in README §6).** Shift+K is its own key and K is unchanged; Ctrl+Shift+F is "Kayıtlı filtreler". Evidence: neither K nor Shift+K has a convention, K-14 (`kontrol.kes`, cut at the current page) is a contract row with tests, so the additive key breaks nothing; Ctrl+Shift+F has no Windows meaning and its only clash is KDE's second full-screen key, while Evrakçı's full screen is F11 (`research/shortcut-conventions.md` §4.2). The QR part (Q) waits with I-01.

## Build steps
1. Core C-1: `PageInfo.qr_texts`, job round trip, old file test. 2. Kind `qr` in A's `pipeline/select.py` (after A step 1) and `Job.add_cuts` with tests. 3. `JobStore.reread_qr` and CLI `is sec qr` / `qr-oku` with tests. 4. QR row in A's dialog and `kontrol.qr_sec` registry action, contract row, key test. 5. `kontrol.kes_secili` (one undo step, skip counts). 6. QR badge in `kontrol_paint.py` and the matrix shot.

---

# I-07: Saved filters as chips, stored with the template (core change C-2)

## 1. Problem
"Every job of the same kind, I set up the same selection again: blank pages over 0.5 %, then the KAP- pages." Staff of repeat jobs rebuild the same filters each time (findings-filtering: Paperless saved views; K-26 remembers only the last N, session only). Principles: Less paper handling, Calm for long sessions.

## 2. Who and when
The person who sets up templates saves filters once; staff in Kontrol use the chips at the start of every job of that kind. Several times a day for repeat jobs.

## 3. Keyboard flow
1. In Kontrol, the template chosen in the inspector (`_template_for_selection`, `kontrol.py:663`) shows its saved filters as a chip row above the timeline.
2. `Ctrl+Shift+F` (action `kontrol.kayitli_filtreler`, "Kayıtlı filtreler", menu Araçlar) puts focus on the chip row. Left/Right move between chips, Space or Enter turns a chip on or off, Esc returns to the timeline.
3. Each turned-on chip narrows the result (AND). The line next to the chips always shows one count: "3 filtre açık: 7 sayfa". The matching pages become the selection (same as in A). Turning every chip off clears only the selection that the chips made.
4. Save: after using any "select by" filter from A or I-01, the result card offers "Kayıtlı filtrelere ekle…" (button, no key; opens a small dialog: name field, Enter saves). Delete a chip: Del on a focused chip, undoable ("Kayıtlı filtre silindi", Geri al).
Mouse: click chip, "×" on hover or focus for delete (also a context menu "Sil", "Yeniden adlandır").

## 4. Screen sketch
```
[ Boş sayfalar > %0,5 ] [ QR: KAP-* ] [ + Kayıtlı filtre ]      3 filtre açık: 7 sayfa
  ▣ on (check + filled)   □ off          (button, only with a selection result)
```
- The chip row is a new small component built only from tokens: radius pill (exempt in DEC-LAY-03), 32 px high (AUD-HIT-03), text at least 13 px, on state = accent fill plus a check icon, off = outline (HIG-CTL-08, not colour alone). Never orange.
- Sits in the strip between the command bar and the timeline; it hides when the chosen template has no saved filters and no selection result (no empty bar). At 150 % text the row wraps to two lines; chips never truncate below 12 characters, then ellipsis plus tooltip with full name.
- Shows "Şablon yok" (existing) wording when no template is chosen: the row then offers nothing to show; see decision 2.

## 5. Data and core changes (D13 is lifted; core change C-2, CLI included)
- `pipeline/templates/model.py`: new frozen dataclass `SavedFilter(name: str, kind: str, params: dict)` (kind + params is A's `Criterion.to_dict()`); `Template.saved_filters: list[SavedFilter]` (after `keywords`, line ~111) with `add_saved_filter`, `remove_saved_filter`, `rename_saved_filter` (name unique, NFC, non-empty, at most 20 filters, Turkish `TemplateError` messages). `template_to_dict` (line 206) writes `"saved_filters"`; `template_from_dict` (line 230) reads `data.get("saved_filters", [])` through the same checks. `TEMPLATE_FORMAT_VERSION` stays 1 (additive): older template files open unchanged; an older app ignores the key and drops it on its next save (release note).
- `template_revision` (line 194) is not changed: saved filters do not change what is read, so existing values are not marked stale (a test pins this).
- `pipeline/select.py` (shared with I-01 and group A): `select_pages(job, criteria, templates=None) -> SelectionResult(page_ids, per_filter_counts, unknown_kinds)` (owned here): runs A's `evaluate` for each criterion and joins them with A's `combine(..., "within")` (AND). Kind "qr" is C's (`pages_matching_qr`); the other kinds are A's predicates registered in the same module (dependency). An unknown kind is reported in `unknown_kinds`, never dropped. Window and CLI call only this function, so both give the same pages and count.
- `TemplateStore.save/export/import_file` (`templates/store.py`) already go through the dict functions, so export and import carry the filters.
- CLI (`cli/templates.py`, `cli/jobs.py`): `evrakci sablon filtre-ekle|filtre-sil|filtreler <şablon>` manage them; A's `evrakci is sec <iş> --sablon <şablon> [--filtre <ad>...]` (this file adds the two options) prints the AND count and the page positions. Existing commands and output are unchanged.
- Nothing is stored in the job, `index.xlsx` or export. In the window, saving is an edit on the template with the undo step "Kayıtlı filtre ekle" (Şablonlar undo stack), plus a toast in Kontrol with Geri al.
- Kind names (for example "blank", "qr") are strings the template never interprets.

## 6. Tests
- Core `tests/test_template_model.py`: round trip with and without `saved_filters`; an older template file (no key) loads; bad entries raise `TemplateError`; duplicate name refused; `template_revision` unchanged by adding a filter. `tests/test_template_store.py`: export/import keeps filters. New `tests/test_select.py`: AND of two kinds, zero result, unknown kind reported. One failure to catch: an older template file refused after the change.
- CLI `tests/test_cli_templates.py` and `test_cli_edit.py`: `filtre-ekle`/`filtreler`/`is sec` work; the page list and count equal the window's `select_pages` on the same job; old commands' output identical.
- UI `tests/ui/test_kontrol_chips.py`: two chips AND with one count; 0 matches says "0 sayfa"; unknown kind disabled; delete and undo; the keyboard path.
- Shortcuts: registry, key press for `Ctrl+Shift+F`, Space on a chip. Screenshots: `states` shot with chips on, wrapped at 150 %.

## 7. Risks and open questions
- Silent-wrong: a saved filter may hide that it matches nothing on a different batch. The count line always shows "0 sayfa" and a chip that matches 0 is marked "0".
- Hard-coding: filters store only kind + user-typed settings; no document kind or variable name is stored. A filter on a variable value is out of scope (needs values, which exist only after reading).
- 800 pages: each active chip is one pass over the page dict, re-evaluated only when a chip changes or the job changes.
- Scope creep: no OR, no "NOT", no sharing outside the template file.
- Which template owns a chip when the selection spans templates: see decision 2.

## Shortcut contract rows it adds
| tab | key | action_id | label | undo |
|---|---|---|---|---|
| kontrol | Ctrl+Shift+F | kontrol.kayitli_filtreler | Kayıtlı filtreler | focus move only |
Chip keys (Left, Right, Space, Enter, Del, Esc) are local to the chip row (`local=True`, like `kontrol.sayfa`). Ctrl+Shift+F is free on Kontrol (no Ctrl+Alt, no Turkish-only letter, not I).

## Rules it must meet
AUD-KBD-01, AUD-KBD-02, AUD-A11Y-01 (each chip: accessible name "Boş sayfalar, açık"), HIG-CTL-08, HIG-CON-03, DEC-IDN-01, DEC-TYP-01, DEC-LAY-03, AUD-HIT-01, AUD-HIT-03, AUD-TXT-01, DEC-FOC-01, HIG-FOC-08 (Tab to the row, arrows inside), AUD-WIN-01, HIG-WIN-19.

## Performance cost (800 pages)
One set intersection per chip change over up to 800 ids: under 5 ms. Template file grows by a few hundred bytes.

## New Turkish text
| string | where | meaning in English | status |
|---|---|---|---|
| Kayıtlı filtreler | menu, row label, palette | Saved filters | draft |
| Kayıtlı filtrelere ekle… | result card button | Add to saved filters | draft |
| Filtrenin adı | save dialog field | Name of the filter | draft |
| Kaydet | save dialog primary | Save | existing (`actions.py:168`, app.kaydet) |
| {n} filtre açık: {m} sayfa | row count line | n filters on: m pages | draft |
| Hiçbir filtre açık değil | row count line | No filter is on | draft |
| Kayıtlı filtre eklendi: {ad} | toast | Saved filter added | draft |
| Kayıtlı filtre silindi | toast, undo step | Saved filter deleted | draft |
| Kayıtlı filtre ekle | undo step name | Add saved filter | draft |
| Tanınmıyor | disabled chip word | Not recognised | draft |
| Bu filtreyi bu sürüm tanımıyor | chip tooltip | This version does not know this filter | draft |
| Sil, Yeniden adlandır | chip context menu | Delete, Rename | existing words ("Yeniden adlandır" is F2 on Yükle) |
| Vazgeç | save dialog | Cancel | existing (`kontrol_dialogs.py:28`) |
| Şablon yok | when no template | No template | existing (inspector value) |
| Geri al | toast action | Undo | existing |
Sector check: "kayıtlı filtre" is the usual Turkish wording for saved views and saved filters in office and mail software; "profil" is used in scanner utilities for saved scan settings. "Kayıtlı filtre" is kept because this is a selection, not scan settings.

## Check against the product
- Never silent: Pass (one count, 0-match chips marked, unknown kinds shown, never dropped).
- No built-in kinds or fields: Pass (kind + user settings only).
- Keyboard: Pass (row focus key, local keys, no mouse needed).
- Colour: Pass with the on-state check icon; verify in high contrast (matrix).
- Layout: Pass (wraps at 150 %, hidden when empty); verify with 8 chips.
- Copy: Pass, draft.
- Local-first: Pass (a field in the local template file; no dependency).

## Owner decisions needed
**Decided by evidence (T3, 2026-11-20; sources in README §6).**
1. O-13: chips are stored with the template only; no per-job list. Evidence: Paperless-ngx keeps saved views as reusable objects managed once and shown on the dashboard or sidebar for every later document, not per upload (Paperless-ngx `docs/usage.md`); this matches "set up once per document kind" (PRODUCT.md, Users).
2. O-14: the row shows the chips of the template in the inspector; with none, "Şablon seçin". Evidence: follows from O-13 (a chip belongs to one template) and from the existing inspector rule `_template_for_selection` (`kontrol.py:663`); one source avoids showing filters whose criteria do not apply to the selected pages.
3. Decided in the reconcile: a chip's params are fixed in v1; changing means delete and save again.
4. Decided in the reconcile: chips only select; actions stay K, T, F (and Shift+K).

## Build steps
1. Core C-2: `SavedFilter`, dict round trip, old file test. 2. `select_pages` AND over A's and C's kinds (after A's kinds are built), with tests. 3. CLI `sablon filtre-*` and `is sec` with parity tests. 4. Chip row component, Kontrol wiring, count line. 5. Save dialog, delete with undo, unknown-kind state. 6. Registry action, contract row, key tests, matrix shot.
