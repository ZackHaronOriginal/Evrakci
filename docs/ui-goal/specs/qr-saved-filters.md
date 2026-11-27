# Spec group C: saved filters (I-07)

Status: draft for owner approval. Written 2026-11-20, revised the same day. No code is changed by this file.
D13 is lifted (owner, 2026-11-20): core and CLI changes below are by design, not minimal hooks.

**I-01 (select and cut by QR content) is dropped by the owner (2026-11-20):** QR codes are only Evrakçı separator sheets; the offices' own forms carry none. So this group is saved filters only. Decisions O-11 and the Q key are gone, and the multi-cut key Shift+K existed only for I-01 and is gone too. The filename `qr-saved-filters.md` is kept so links stay valid.

**Reconciled with A, B and D (2026-11-20).** Build order, shared pieces and the Kontrol key table are in `specs/README.md` (O-12 is now only Ctrl+Shift+F, O-13 and O-14 decided by evidence). A owns `pipeline/select.py` (`Criterion`, `evaluate`, `combine`), the "Sayfaları seç" dialog and the CLI command `is sec`; this file adds `select_pages` (AND of saved filters) and the options `--sablon` and `--filtre`. Job files are not touched by this group.
Sources: `ideas-ranking.md` row I-07, `research/findings-filtering.md`, `decisions.md` (D1, D13, "Phase 5 build order and rules"), `shortcut-contract.tsv`, the code cited below.

## Dependency on group A (selection model)

Group A (`specs/kontrol-filters.md`, ideas I-03, I-04, I-06, I-08, I-09) is written in parallel. This group needs from it, expressed in terms of the idea rows:
- **One entry point** that "selects pages by a property" (I-03 blank, I-04 size/orientation, I-06 low confidence, I-09 this document / odd / even). C adds no property and no second entry.
- **Selection is the only result.** Every such filter ends as a set of page ids in the timeline selection (`KontrolScreen.selected_ids`, `src/evrakci/ui/kontrol.py:248`), with a live count. Cut, delete, rotate, template then act on that selection as today.
- **A filter is a small description**: a kind name plus its settings (for example blank + threshold), evaluated in the core (`pipeline/select.py`, D13 lifted) so the CLI gives the same count. I-07 stores exactly that description. A defines it as `Criterion(kind, params)` in `pipeline/select.py` (kontrol-filters §0); no owner decision.
- **Not the "every N pages" filter.** `F` / "Filtre uygula…" (`kontrol.py:300`, `kontrol_dialogs.py:39`) keeps its meaning; it is stored in the job (`job.py:FilterApplication`). I-07 chips are different: they only select pages and are stored with a template.

Until A is approved and built, C cannot be built. Build order: A, then C.

---

# I-07: Saved filters as chips, stored with the template (core change C)

## 1. Problem
"Every job of the same kind, I set up the same selection again: blank pages over 0.5 %, then the pages that need a check." Staff of repeat jobs rebuild the same filters each time (findings-filtering: Paperless saved views; K-26 remembers only the last N, session only). Principles: Less paper handling, Calm for long sessions.

## 2. Who and when
The person who sets up templates saves filters once; staff in Kontrol use the chips at the start of every job of that kind. Several times a day for repeat jobs.

## 3. Keyboard flow
1. In Kontrol, the template chosen in the inspector (`_template_for_selection`, `kontrol.py:663`) shows its saved filters as a chip row above the timeline.
2. `Ctrl+Shift+F` (action `kontrol.kayitli_filtreler`, "Kayıtlı filtreler", menu Araçlar) puts focus on the chip row. Left/Right move between chips, Space or Enter turns a chip on or off, Esc returns to the timeline.
3. Each turned-on chip narrows the result (AND). The line next to the chips always shows one count: "3 filtre açık: 7 sayfa". The matching pages become the selection (same as in A). Turning every chip off clears only the selection that the chips made.
4. Save: after using any "select by" filter from A, the result card offers "Kayıtlı filtrelere ekle…" (button, no key; opens a small dialog: name field, Enter saves). Delete a chip: Del on a focused chip, undoable ("Kayıtlı filtre silindi", Geri al).
Mouse: click chip, "×" on hover or focus for delete (also a context menu "Sil", "Yeniden adlandır").

## 4. Screen sketch
```
[ Boş sayfalar > %0,5 ] [ Tek sayfalar ] [ + Kayıtlı filtre ]      3 filtre açık: 7 sayfa
  ▣ on (check + filled)   □ off          (button, only with a selection result)
```
- The chip row is a new small component built only from tokens: radius pill (exempt in DEC-LAY-03), 32 px high (AUD-HIT-03), text at least 13 px, on state = accent fill plus a check icon, off = outline (HIG-CTL-08, not colour alone). Never orange.
- Sits in the strip between the command bar and the timeline; it hides when the chosen template has no saved filters and no selection result (no empty bar). At 150 % text the row wraps to two lines; chips never truncate below 12 characters, then ellipsis plus tooltip with full name.
- Shows "Şablon yok" (existing) wording when no template is chosen: the row then offers nothing to show; see decision 2.

## 5. Data and core changes (D13 is lifted; core change C, CLI included)
- `pipeline/templates/model.py`: new frozen dataclass `SavedFilter(name: str, kind: str, params: dict)` (kind + params is A's `Criterion.to_dict()`); `Template.saved_filters: list[SavedFilter]` (after `keywords`, line ~111) with `add_saved_filter`, `remove_saved_filter`, `rename_saved_filter` (name unique, NFC, non-empty, at most 20 filters, Turkish `TemplateError` messages). `template_to_dict` (line 206) writes `"saved_filters"`; `template_from_dict` (line 230) reads `data.get("saved_filters", [])` through the same checks. `TEMPLATE_FORMAT_VERSION` stays 1 (additive): older template files open unchanged; an older app ignores the key and drops it on its next save (release note).
- `template_revision` (line 194) is not changed: saved filters do not change what is read, so existing values are not marked stale (a test pins this).
- `pipeline/select.py` (owned by group A; this file adds one function): `select_pages(job, criteria, templates=None) -> SelectionResult(page_ids, per_filter_counts, unknown_kinds)` (owned here): runs A's `evaluate` for each criterion and joins them with A's `combine(..., "within")` (AND). All kinds are A's predicates registered in the same module (dependency). An unknown kind is reported in `unknown_kinds`, never dropped. Window and CLI call only this function, so both give the same pages and count.
- `TemplateStore.save/export/import_file` (`templates/store.py`) already go through the dict functions, so export and import carry the filters.
- CLI (`cli/templates.py`, `cli/jobs.py`): `evrakci sablon filtre-ekle|filtre-sil|filtreler <şablon>` manage them; A's `evrakci is sec <iş> --sablon <şablon> [--filtre <ad>...]` (this file adds the two options `--sablon` and `--filtre`) prints the AND count and the page positions. Existing commands and output are unchanged.
- Nothing is stored in the job, `index.xlsx` or export. In the window, saving is an edit on the template with the undo step "Kayıtlı filtre ekle" (Şablonlar undo stack), plus a toast in Kontrol with Geri al.
- Kind names (for example "bos", "tek") are strings the template never interprets.

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
4. Decided in the reconcile: chips only select; actions stay K, T, F.

## Build steps
1. Core change C: `SavedFilter`, dict round trip, old file test. 2. `select_pages` AND over A's kinds (after A's kinds are built), with tests. 3. CLI `sablon filtre-*` and `is sec` with parity tests. 4. Chip row component, Kontrol wiring, count line. 5. Save dialog, delete with undo, unknown-kind state. 6. Registry action, contract row, key tests, matrix shot.
