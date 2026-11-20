# Specs: quick wins (group B)

Seven small ideas from `ideas-ranking.md`: I-17, I-19, I-21, I-22, I-23, I-28, I-47. Nothing here is built; the owner approves each spec first. D13 is lifted (owner, 2026-11-20): where the core is the better home, the spec names the function. Examples use invented data. Evidence: `research/findings-review-qc.md`, `findings-template-design.md`, `findings-performance.md`, `inventory-degerler.md` (V-, O-), `inventory-kontrol.md` (K-), `inventory-sablonlar.md` (S-). Code cited at HEAD.

Turkish wording: checked against terms already in the UI (reused where one exists). Sector check: ABBYY's Turkish help calls OCR output "tanınan metin" ([ABBYY Sprint, tr-tr](https://help.abbyy.com/tr-tr/finereader_sprint/12/text_formats)); we keep our own "Okunan" for the same thing. No Turkish page on "revert one field" or "required field empty" was found, so those strings stay "draft". Free keys were taken from `docs/ui-goal/shortcut-contract.tsv` and `audit_shortcuts.py --check` (0 problems). Keys on Kontrol (I-21) must be reserved against group A (A also adds Kontrol keys).

**Reconciled with A, C and D (2026-11-20).** Build order, shared pieces, the key table and the owner's decisions (O-6 to O-10 are this file's) are in `specs/README.md`. This file owns `value_level` (I-17, in `pipeline/templates/values.py`, reused by A's I-06) and `motion.wait_cursor` (I-47, reused by D's I-38). D on Kontrol is I-21's; A's I-04 jumps became menu-only. New single keys whose label differs on another tab (K, R, N, Shift+N) each need a page-specific line in `shortcuts.md` at build, or `audit_shortcuts.py --check` fails.

Shared note: single-letter keys are switched off by Ayarlar > "Tek tuşlu kısayollar" (WCAG 2.1.4); every such command also has a menu item and a button or context-menu entry.

---

## I-17 Show which cell is wrong, not only the row

**1. Problem.** In a row with one Kontrol value and three Emin values, all four texts look the same; only the row's Güven word tells something is wrong (O-01, `degerler_table.py:ValuesDelegate._value` paints only `cell.uncertain`). "Which of the four?" costs a click per cell. Principle: Never silent.
**2. Who and when.** Reviewers, Değerler, every session; a few hundred times per job.
**3. Keyboard flow.** No new key. N / Shift+N already jump to the next value that needs a check (`degerler.sonraki_kontrol`, `degerler.py:next_check` 983); with the mark the eye finds the cell first. Mouse: unchanged. Context menu: unchanged.
**4. Screen sketch** (1366x768, 100 %, table columns shortened):
```
 Belge  Sayfa  Firma             Tutar       Tarih        Güven
 12     34-36   [!] 482I3 Ltd.    1.250,00    03.04.2026   Kontrol %55
 13     37-38   Örnek A.Ş.        980,00      [x] boş      Okunamadı
```
A 16 px icon sits left of the value in a cell that needs a check: `triangle-alert` in `check-text` for Kontrol, `circle-x` in `danger` for Okunamadı (icons and roles from `degerler_model.LEVELS`, same as the Güven column). The word is in the cell tooltip and the spoken text (both exist: `_spoken`, `data()` tooltip role). Reuses the delegate and `icons.paint`; no new component. At 150 % the icon scales with `m.inline_icon(16)`; in high contrast the icon uses the `ink` role like Güven does. Orange only on Kontrol, and the icon always has a word next to it in the row (Güven) and in the tooltip.
**5. Data and core changes.** Core is the better home for "what level is a value": today the rule (`EMIN_AT = 0.90`, flagged = Kontrol or Okunamadı) lives in `ui/degerler_model.py:make_cell` (210) and the CLI prints a different word for the same cell (`cli/jobs.py:455-456` writes `[okunamadı, öneri: ...]` for any flagged value). Change: add `pipeline/templates/values.py:value_level(value: VariableValue | None) -> "emin"|"orta"|"kontrol"|"okunamadi"|"okunmadi"` with `EMIN_AT` (moved from `ui/degerler_model.py:31`; `values.py` has no imports, so `review.py`, `select.py` and the UI can all use it). This spec owns it; kontrol-filters I-06 and `sablon_read.level_of` reuse it. `make_cell` and `is degerler` call it. CLI line for a flagged value with a reading becomes `Firma: 482I3 [kontrol, öneri: 482I3 Ltd.]` and `[okunamadı]` only when nothing was read. Job file: no change. `index.xlsx`: no change (Kontrol reasons already per document, D-46). Older job files open as before (values are unchanged). Offline: yes.
**6. Tests.** Core: new `tests/test_values.py` cases for each level and the 0.90 edge (synthetic `fakes.py`); `tests/test_cli_values.py` updated for the new CLI wording and a test that window level == CLI level for the same job. UI: `tests/ui/test_degerler_table.py` offscreen: a Kontrol cell paints an icon (pixel check left of text), an Emin cell none; tooltip contains "Kontrol". Screenshot: Değerler main shot in the matrix, all three themes plus 150 %. Failure it must catch: the mark on a cell that is not Kontrol, or missing on one that is.
**7. Risks.** Visual noise: only needs-check cells are marked, so a clean job looks the same as today. 800 documents x 4 variables: icon paint only for visible rows. CLI wording change breaks scripts that parse `[okunamadı` (owner decision).

**Shortcut contract rows it adds:** none (existing N / Shift+N rows get an extra feedback sentence).
**Rules it must meet:** DEC-IDN-01 (orange only for Kontrol), HIG-CON-03 (not colour alone), DEC-CON-03 (icon 3:1), DEC-ICO-01 (16 px), AUD-TXT-01, DEC-THM-01.
**Performance cost (800 pages):** none measurable: paint-time only for rows on screen; level lookup is a comparison per cell.

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Kontrol | cell tooltip, spoken text | Check | existing |
| Okunamadı | cell tooltip | Not readable | existing |
| Bu değere bakın: okuma emin değil. | tooltip, first line of a Kontrol cell | Please look at this value: the reading is not sure | draft |

**Owner decisions needed.**
1. (README O-6) In-cell word: icon only, word in tooltip and in the row's Güven (recommended), or icon + word "Kontrol" inside the cell where it fits (wider columns, more noise).
2. (README O-7) CLI wording `[okunamadı…]` -> `[kontrol…]` for a flagged value with a reading (recommended: yes, one vocabulary).
**Build steps.** (1) `value_level` + core tests; (2) `make_cell` uses it; (3) CLI uses it + test update; (4) delegate icon + tooltip; (5) UI test and matrix shot.

---

## I-19 Show every section's reading next to the suggestion

**1. Problem.** Enter accepts "one best reading" (V-57); the card shows one reading and one suggestion though all section readings are stored with their confidence (O-16, `ValueCard` `degerler_side.py:455`). With a wrong anchor, Enter rests on it (automation bias, [PMC5356416](https://pmc.ncbi.nlm.nih.gov/articles/PMC5356416)). Principle: The user decides what documents contain.
**2. Who and when.** Reviewers, Değerler, on every Kontrol value that has two or more readings.
**3. Keyboard flow.** No new key: N lands on a Kontrol value, the side card already shows the list, Enter accepts the suggestion, F2 types. To take another reading instead of the suggestion: F2 opens the editor, whose start text is the suggestion (`Cell.edit_text`); a reading can be picked with Alt+1 .. Alt+4 inside the editor (owner decision 2). Mouse: click a reading row in the card to put it into the editor. Context menu: none.
**4. Screen sketch** (side card 240-320 px wide, new block between "Öneri" and the level line):
```
 Okunan      482I3
 Öneri       48213
 Tüm okumalar
   Bölüm 1    482I3     %41
   Varyant 2  48213     %55   Öneri
 Kontrol %55  1 karakter belirsiz
```
Reuses `ValueCard` (inside the card, same `_caption` and `MarkedText` widgets, one row per reading, uncertain characters marked as today). The row that equals the suggestion carries the existing word "Öneri" (icon + word, no colour alone). Shown only when the value has 2+ readings, so the card does not grow for simple values; at 150 % the side `CardScroll` scrolls above the pinned buttons as it does now. Text >= 13 px.
**5. Data and core changes.** None. `VariableValue.readings` (`pipeline/templates/values.py`: `SectionReading(section, text, confidence, problem)`) is already in the job file. `section_name` (`degerler_model.py:72`) gives "Bölüm 1" / "Varyant N". Picking a reading stores through the existing `controller.set_value` (undo "Değeri düzelt").
**6. Tests.** UI: `tests/ui/test_degerler.py`: a value with two readings lists both, marks the suggestion, hides the block for a single reading; picking one stores that text and is one undo step. Shortcut: if Alt+N is added, registry row plus key-press test. Shot: Değerler with a Kontrol value (states). Failure to catch: the list shows a reading that is not the stored one.
**7. Risks.** Card height on 1366x768 at 150 %: cap at 4 rows with "+N daha" (owner decision 3). Over-trust is lowered, not removed: the list must not make Enter slower. Readings with `problem` set show their problem word (existing text from the core).

**Shortcut contract rows it adds:** only if decision 2 is yes: `degerler Alt+1..Alt+4 degerler.okuma_sec` (local, editor open). Not Ctrl+Alt.
**Rules it must meet:** AUD-HIT-03 (rows 32 px if clickable), AUD-KBD-02, AUD-TXT-01, HIG-CON-03, AUD-WIN-02.
**Performance cost (800 pages):** none: built for the one selected value.

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Tüm okumalar | caption in the value card | All readings | draft |
| Bölüm 1 / Varyant 2 | reading rows | Section 1 / Variant 2 | existing |
| Öneri | tag on the matching row | Suggestion | existing |
| +{n} daha | row cap | n more | draft |

**Owner decisions needed.**
1. Decided in the reconcile: always shown for 2+ readings.
2. (README O-8) Alt+1..4 / click picks a reading: yes (recommended, one undo step) or list is read-only.
3. Decided in the reconcile (layout): cap at 4 rows.
**Build steps.** (1) list widget in `ValueCard`, read-only; (2) cap and 150 % check; (3) click-to-pick; (4) Alt+N keys and tests.

---

## I-21 Carry the document between Değerler and Kontrol

**1. Problem.** "Değerlerde aç" in Kontrol drops the document number (`main_window.py:1205`, `lambda _n: self.show_tab("degerler")`; ledger B-012, open); from Değerler there is no way back. Finding the document again among 400 means typing Ctrl+G. Principle: Calm for long sessions.
**2. Who and when.** Staff who find a wrong cut while reading values, or a wrong value while checking a cut; several times per job.
**3. Keyboard flow.** In Kontrol: `D` = "Değerlerde aç" (existing action `kontrol.degerlerde_ac`, gets the key; free on Kontrol). In Değerler: `K` = "Kontrol'de aç" (new action `degerler.kontrolde_ac`, menu Araçlar next to `degerler.oku`; free on Değerler). Result: the other tab is shown with that document selected and focus on its main view. Mouse: the existing inspector button "Değerlerde aç"; new button "Kontrol'de aç" in the Değerler side panel under the three actions only if room (owner decision 2), else menu and context menu entry.
**4. Screen sketch.** No new region: a menu item and a key; optional secondary button. Reuses the command-bar menu and `registry.action` context menu (`CONTEXT` in `degerler.py:337`).
**5. Data and core changes.** None in the core. `KontrolScreen.open_values(int)` already carries the number; change the connection to call `DegerlerScreen.select_value(number, first_key)` (`degerler.py:941`, exists) after `show_tab`; add `DegerlerScreen.open_in_kontrol` emitting a new `open_kontrol(int)` signal handled by `KontrolScreen.go_to_document(number)` (`kontrol.py:461`, exists). Edge cases: a document without a template is not a row in Değerler (status text says so, no tab switch); the "Kontrol gerekenler" view hides a clean document: switch to "Tümü" and say so. Fixes B-012 as step 1.
**6. Tests.** UI: flip the strict xfail `tests/ui/test_ledger_c.py::test_b012_values_button_in_kontrol_selects_that_document`; new test the other way; test for no-template and filtered-out cases. Shortcut: registry rows for both keys, key-press test in each tab, `audit_shortcuts.py --check` clean. Failure to catch: the wrong document selected after the switch (number off by one between "belge N" and row index).
**7. Risks.** Silent wrong target is the risk, so the status line names it ("Belge 12 seçildi"). Focus must land in the main view, not stay on the old tab's button. Key `D`: reserved for this command in the reconcile (A's I-04 jumps are menu-only; no C key uses D). `K` is "Kes" on Kontrol, so `K` needs a page-specific line in `shortcuts.md`.

**Shortcut contract rows it adds:** `kontrol D kontrol.degerlerde_ac`; `degerler K degerler.kontrolde_ac` (both single-key, off with the Tek tuşlu setting).
**Rules it must meet:** AUD-KBD-02, DEC-FOC-01, HIG-FOC-02 (focus moves only because of the user's key), HIG-WIN-12 (key shown in the menu).
**Performance cost (800 pages):** one row lookup; `model.row_of` is a dict or scan of 800 rows, negligible.

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Değerlerde aç | Kontrol menu, button | Open in Değerler | existing |
| Kontrol'de aç | Değerler menu, context menu | Open in Kontrol | draft |
| Bu belgenin şablonu yok; Değerler'de görünmez. | status line | This document has no template; it is not in Değerler | draft |
| Belge {n} seçildi. | status line | Document n selected | draft |
| Tümü | view name after the switch | All | existing |

**Owner decisions needed.**
1. (README O-10, with R and the Şablonlar keys) Keys D (Kontrol) and K (Değerler): yes (recommended) or menu only.
2. Decided in the reconcile: no button in the Değerler side panel (full at 150 %); menu, context menu and key.
**Build steps.** (1) fix B-012 with the existing `select_value`; (2) reverse direction + signal; (3) edge cases and status; (4) keys, registry rows, tests.

---

## I-22 Show "Zorunlu" and warn on an empty required value

**1. Problem.** Clearing a cell and pressing Enter stores an empty, İncelendi, Emin value and says nothing (`degerler.py:_apply_edit` 1224 -> `review.set_value`, no check); `Cell.required` is set but never shown (O-11, O-12). The file name then fails at export. Principle: Never silent.
**2. Who and when.** Staff who clear a wrong value meaning to type another one; Değerler, once per mistake, found only in Dışa Aktar's Ön kontrol today.
**3. Keyboard flow.** No new key. F2, clear, Enter: the value is stored as Kontrol with the reason, the toast says so, N finds it again. Mouse: the same in the editor.
**4. Screen sketch.** Header text carries the mark: `Firma *` (accessible name "Firma, zorunlu"); the value card meta reads "Belge 3, sayfa 5 · zorunlu"; the reason line (`Cell.why`, `degerler_model.py:172`) gets a new case; toast uses `_toast` (`degerler.py:1192`) with kind `kontrol`. Reuses the table header, `ValueCard`, toast. "*" matches the template legend "* zorunlu" in `sablon_nav.py:416`. 150 %: the header may elide; the tooltip says "zorunlu".
**5. Data and core changes.** Core is the better home, so the CLI warns the same way. `pipeline/review.py:set_value(job, document, key, text, required=False) -> bool`: when `required` and the cleaned text is empty, store the value as flagged and unreviewed with the old reading kept as suggestion (the state `revert_value` makes) and return False; otherwise store as today and return True. `ui/controller.py:set_value` (108) passes `required` and returns the flag; `_apply_edit` passes `cell.required`; `cli/jobs.py:fix_value` (line 463) passes `template.variable(...).required` and prints the same sentence as the toast. Job file: no new field (flagged + empty already exists). `index.xlsx`: the document gets the existing "zorunlu değer eksik" check at export (`export.py` plan_export). Older job files: unchanged; an old empty edited required value stays stored and Dışa Aktar still reports it.
**6. Tests.** Core: `tests/test_review.py`: required + empty -> flagged, returns False, readings kept, can be undone by `revert_value`; not required + empty -> stored as before; whitespace-only counts as empty. CLI: `tests/test_cli_values.py` prints the sentence and exit code stays 0. UI: `tests/ui/test_degerler.py`: clearing a required cell shows Kontrol and the toast; the window and CLI give the same stored value for the same job. Old job: `tests/test_job.py` fixture without the field still loads. Shot: header with "*". Failure to catch: an empty required value left İncelendi.
**7. Risks.** A person who really means "empty" for a required variable cannot make it Emin; they use the template (Zorunlu off) or leave it Kontrol (owner decision 1). No false alarm for non-required variables.

**Shortcut contract rows it adds:** none.
**Rules it must meet:** HIG-CON-03, DEC-IDN-01, AUD-A11Y-01, AUD-TXT-01 (header elision), HIG-WIN-17 (no alert dialog for an undoable action: toast, not a message box).
**Performance cost (800 pages):** none (checked only on an edit).

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Zorunlu | tooltip of header mark, card meta ("zorunlu") | Required | existing |
| Zorunlu değer boş: dosya adı için bir değer yazın. | reason line under the value | Required value is empty: type a value for the file name | draft |
| Zorunlu değer boş bırakılamaz; Kontrol'e alındı. | toast, CLI line | A required value cannot stay empty; it is now Kontrol | draft |

**Owner decisions needed.**
1. (README O-9) Empty required value: store as Kontrol with the reason (recommended) or refuse the edit and keep the editor open.
2. Decided in the reconcile: "*" in the header (matches Şablonlar' "* zorunlu" legend).
**Build steps.** (1) core `set_value(required=)` + core tests; (2) controller and `_apply_edit`; (3) CLI + test; (4) header mark, card meta, reason line, toast; (5) UI tests and shot.

---

## I-23 "Okunana dön": put a value back to what the machine read

**1. Problem.** After a wrong correction the only way back is Ctrl+Z, which undoes the newest step, not that value (V-65, O-10). The core can (`review.py:revert_value` 49) and the CLI has `--geri-al`; the window has no command. Principle: The user decides what documents contain.
**2. Who and when.** Reviewers, Değerler, after typing over a value and then doubting it; a few times per job.
**3. Keyboard flow.** `R` on a value that was corrected or confirmed (action `degerler.okunana_don`, menu Düzen after "Elle yaz", context menu, command palette). Free on Değerler. Result: value waits for a check again with the old reading as the suggestion (Kontrol), selection stays, status says what happened; Ctrl+Z undoes the revert (undo name "Okunana dön"). Mouse: context menu entry.
**4. Screen sketch.** No new region. Menu and context menu item with its key (registry). Disabled with a reason when the value was never machine-read.
**5. Data and core changes.** `revert_value` exists and is kept. Add `review.can_revert(value) -> bool` (True when `value.edited` and it has readings or a suggestion) so window and CLI refuse the same case: today the revert of a hand-typed value with no reading silently becomes an empty Okunamadı. `fix_value` (`cli/jobs.py:480`) raises "{ad} için okunan değer yok." when `can_revert` is False. Window: `controller.run("Okunana dön", lambda job: revert_value(job, row.document, key))` then `refresh()`. Job file: no change. Old job files: values already carry `readings`; those saved before readings existed have none and show the disabled reason.
**6. Tests.** Core: `can_revert` true/false cases; `revert_value` after `set_value` and after `accept_suggestion` restores suggestion and flags. CLI: `--geri-al` on a value with no reading exits with the new message. UI: key `R` on a corrected value gives Kontrol with the suggestion, one undo step restores the correction; disabled state and status text; registry row and key-press test; window and CLI leave the same stored value for the same start. Failure to catch: a revert that drops the machine reading (suggestion lost).
**7. Risks.** A stray R reverts a correction: it is one step away from Ctrl+Z, and the status line names the value. Sample (Örnek) view: the command is disabled there (the sample has its own error rule, V-69).

**Shortcut contract rows it adds:** `degerler R degerler.okunana_don` (single-key, off with the Tek tuşlu setting; menu entry stays). R is "Sağa döndür" on Kontrol: add a page-specific line in `shortcuts.md`.
**Rules it must meet:** HIG-WIN-19 (undo names the action), HIG-CTL-09 (unavailable shown dimmed, with reason), AUD-KBD-02, DEC-IDN-01.
**Performance cost (800 pages):** none.

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Okunana dön | menu, context menu, undo name | Back to what was read | draft |
| Okunana dönüldü: {değişken}. Kontrol'e alındı. | status line | Reverted; now Kontrol | draft |
| Bu değer elle yazıldı; okunmuş bir değer yok. | disabled reason, CLI error | Typed by hand; there is no machine reading | draft |
| Okunan | root word | Read | existing |

**Owner decisions needed.**
1. (README O-10) Key R or menu only (recommended: R).
2. Wording: left to the Turkish terms check (`research/turkish-terms.md`) and the owner's string review; draft "Okunana dön".
**Build steps.** (1) `can_revert` + core tests; (2) action, menu, handler; (3) CLI message + test; (4) enabled state, status, UI tests.

---

## I-28 Weakest examples first, after "Bütün örneklerde dene"

**1. Problem.** After Ctrl+T the picker marks examples "· N kontrol" and the status says "N okuma kontrol bekliyor", but nothing orders them or jumps to the worst one (S-58, O-10; `sablon.py:_mark_example_checks` 662). With 60 examples the template maker scrolls the picker. Principle: Less paper handling (fewer wasted looks).
**2. Who and when.** The person who sets up a template; Şablonlar, after each try-all.
**3. Keyboard flow.** After Ctrl+T finishes: `N` / `Shift+N` = next / previous weak example in weakest-first order (actions `sablonlar.sonraki_zayif`, `sablonlar.onceki_zayif`); `Ctrl+L` opens "Zayıf örnekler" (list, Up/Down, Enter opens that example, Esc closes). Same N pair as Değerler and Kontrol. Mouse: click the status item "N okuma kontrol bekliyor" to open the list.
**4. Screen sketch** (popup under the example picker, max 8 rows, then scroll):
```
 Zayıf örnekler
 Belge 14  3 kontrol  en düşük %38
 Belge 7   2 kontrol  en düşük %52
 Belge 22  1 kontrol  en düşük %61
```
Reuses the QMenu-style popup of the job switcher and the triangle-alert icon + word "kontrol" already used in the picker (`_mark_example_checks`). 150 %: rows wrap-free, the popup grows to fit; high contrast: icon + word, no colour.
**5. Data and core changes.** Core is a fit: add `pipeline/templates/read.py:weakest_examples(results, limit=None) -> list[ExampleWeakness]` (`number`, `flagged`, `lowest_confidence`), sorted by flagged count then lowest confidence, uses `flagged_count` logic (today `ui/sablon_read.py:flagged_count` 104, which moves to core, UI imports it). No CLI command reads many examples today (`sablon test` reads one file), so no CLI change; the function is ready if a CLI "dene" is added later. Results stay in memory (O-10); they are not saved in the job file.
**6. Tests.** Core: `tests/test_template_read.py`: ordering, ties, examples with no flagged reads omitted, variable with no box not counted. UI: `tests/ui/test_sablon*.py`: after a fake try-all the list is in order, N jumps in that order and wraps with a status line, list Enter opens the example. Shortcut: registry rows, key-press test, audit clean. Shot: popup open. Failure to catch: an example with a variable that has no box counted as weak (false orange).
**6b.** Without a try-all result the keys are disabled with the status "Önce Ctrl+T ile örnekleri deneyin."
**7. Risks.** Results are dropped when the template or job changes (existing behaviour), so the list must empty then. Ctrl+L is free on every tab today; keep it Şablonlar-only.

**Shortcut contract rows it adds:** `sablonlar N sablonlar.sonraki_zayif`, `sablonlar Shift+N sablonlar.onceki_zayif`, `sablonlar Ctrl+L sablonlar.zayif_ornekler`. N / Shift+N are "Sonraki/Önceki kontrol" on Kontrol and Değerler, so the labels differ: add page-specific lines for `N` and `Shift+N` in `shortcuts.md`.
**Rules it must meet:** DEC-IDN-01, HIG-CON-03, AUD-KBD-02, AUD-HIT-03, HIG-WIN-12.
**Performance cost (800 pages):** one sort of up to 800 small tuples after a try-all: negligible next to the read.

| String | Where | Meaning in English | Status |
|---|---|---|---|
| Zayıf örnekler | popup title, menu | Weak examples | draft |
| Belge {n}  {k} kontrol  en düşük %{p} | list row | Document n, k checks, lowest p % | draft |
| Sonraki zayıf örnek / Önceki zayıf örnek | menu, palette | Next / previous weak example | draft |
| Önce Ctrl+T ile örnekleri deneyin. | disabled reason | Try the examples with Ctrl+T first | draft |
| Zayıf örnek yok: hiçbir okuma kontrol gerektirmiyor. | empty list | No weak example: no read needs a check | draft |
| kontrol | row word | check | existing |

**Owner decisions needed.**
1. (README O-10) Keys: N / Shift+N and Ctrl+L (recommended) or the list only.
2. Decided in the reconcile (engineering): `flagged_count` moves into the core.
**Build steps.** (1) core `weakest_examples` + tests; (2) list popup; (3) N / Shift+N and status; (4) registry rows, key tests, shot.

---

## I-47 Keep the window responsive: background work with a loading view

**Owner's direction (2026-11-20):** no busy-cursor approach; the window thread is never blocked; long work runs in a background job and the person sees a loading view with progress (and cancel where the work can stop). This replaces the earlier "busy cursor" idea. Source for the timing: response time over 0.1 s needs no cue, over 1 s the person must see that work is going on, over 10 s they need progress and a way out ([NN/g](https://www.nngroup.com/articles/response-times-3-important-limits/)); the loading view therefore appears after 300 ms, not 1 s.

**1. Problem.** Nothing in `src/evrakci/ui/` tells a person that a long job open or a first read is running unless the work already has its own progress card (Yükle, Değerler, Dışa Aktar). `MainWindow.busy()` / `motion.busy_cursor` exist and nothing calls them, and `busy_cursor` needs the event loop so it cannot cover a blocking call. Principle: Never silent; the window must not look frozen.

**Inventory (measured 2026-11-20 on the synthetic 800-page job, offscreen Qt, this machine; `perf-profile` skill, scratch scripts in the run folder).** Ordinary office PCs are slower; read each number as a floor.

| Where the window thread works | ms (800 pages unless said) | Verdict |
|---|---|---|
| `JobStore.load` (`yukle.py:open_job` 336, `main_window.py` 1157, 1183 start-up "last job", `list_jobs` for the job list) | 0.4 (52 KB job.json); `list_jobs` 24 for 200 jobs x 120 pages | fast on a local disk; the call is a plain file read, so a network or sleeping disk stalls it for as long as the share does: move to a worker |
| `yukle.open_job` through `_job_opened` (`JobController`, `ThumbnailService`, `KontrolScreen` build, Değerler and Dışa Aktar refresh) | 86 | widgets, must stay on the window thread; grows with pages (about 0.1 ms per page), over 300 ms near 3000 pages |
| first events after the open (Kontrol first paint) | 40; `perf_kontrol` first paint 84 fake, 80 real pdfium | fine (existing bound under 1000 ms) |
| `show_tab` Değerler / Dışa Aktar / Kontrol | 26 / 92 / 52 | fine |
| `controller._changed` (save on every edit, `JobStore.save`) and Ctrl+S | 8 / 0.6 | local disk fine; on a network folder every edit waits for the write: write-behind (step 5) |
| OCR engine probe `engine.available()` (`degerler.py:1418` `read_values`, `sablon_read.py:125`) | 288 on the first call, 0.001 after | worst block found: pressing "Oku" freezes the window for about 0.3 s on this machine, more on a PC with a slow disk or a virus scanner: probe in the worker |
| `scan_profile` (Yükle side panel, `yukle.py:645`) | 105 first call (pdfium start), 0.2 after | below 300; move to the existing worker only if it grows with a real scan (not measured with a real scan) |
| page renders for the loupe, Şablon canvas and the Değerler crop (`kontrol._render_page`, `sablon._render`, `degerler._render_page`), per page | 17 at 150 dpi, 25 at 200 dpi (synthetic text PDF) | below 300; real scans at 300 dpi are heavier and not measured; they take `PDFIUM_LOCK`, so they wait up to one analysed page (about 11 ms) |
| `template_store.list` 50 templates / `save` | 1.5 / 0.2 | fine; same network caveat as the job file |
| `ThumbnailService._delete_job` holds `PDFIUM_LOCK` and calls `JobStore.delete` | not measured (delete is refused while work runs) | folder removal on a network drive is the risk; worker, step 4 |
| File dialogs (`QFileDialog` in Yükle, Ayarlar, Dışa Aktar) | not measurable | native dialogs run their own loop; the window repaints, a slow share stalls the dialog only; cannot be threaded, left as is |

**Already in a worker (reuse, do not rewrite):** page analysis and batch copy (`yukle._begin`, `Task`), value reads in Değerler and Şablonlar live reads (`degerler.read_values`, `sablon_live.LiveReads`), export (`disa_aktar`, `export_job` with progress and cancel), thumbnails (`ThumbnailService` own 2-thread pool), Değerler side renders (`degerler_side._Render`). The shared pattern is `ui/workers.py`: `Task(work)` with `progress(done, total)` that raises `Cancelled` after `cancel()`, signals `progress`, `done`, `failed`, `cancelled`, started on `QThreadPool.globalInstance()`. Progress card: `yukle_parts.ProgressCard`; "İptal et" is Ctrl+. (`yukle.iptal`, `degerler.durdur`, `disa_aktar.durdur`).

**2. Who and when.** Everyone, most on older PCs or when the job folder is on a network drive: opening a job (Yükle list, Enter, recent-jobs menu, start-up "last job"), the first "Oku", saving after an edit, deleting a job.
**3. Keyboard flow.** No new key. While the loading view shows, Ctrl+. (İptal et) cancels when the work can stop; Esc does not cancel (existing rule). Focus moves to the loading card's "İptal et" button when it appears and returns to where it was (the job row, the "Oku" button) when it closes. The screen reader announces the title once (live region, like `ProgressCard`).
**4. Screen sketch.** The loading view is the existing progress card shown alone, centred in the area the work will fill (the tab body), not a modal dialog and not over the title bar or tabs, so the window can still be moved, resized, minimised.

```
┌ tab body ───────────────────────────────────────────────┐
│                                                         │
│        ┌──────────────────────────────────────┐         │
│        │ [icon] İş açılıyor     Kasim-raporlari│         │
│        │ ▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░  (6 px bar)    │         │
│        │ %42   Yaklaşık 3 sn kaldı             │         │
│        │ İptal ederseniz hiçbir şey değişmez.  │         │
│        │                          [İptal et]   │         │
│        └──────────────────────────────────────┘         │
└─────────────────────────────────────────────────────────┘
```

Fluent 2 (DESIGN.md direction A): no ProgressRing exists in the app; the 6 px `ProgressBar` of `ProgressCard` is used (determinate when the work reports counts, otherwise the indeterminate bar with the slide animation; reduced motion shows a static half-filled bar and the words). Colours from tokens (`track`, accent). The previous screen stays under the card, dimmed to the disabled colour, so the layout does not jump when the real screen arrives. No spinner on a cold start under 300 ms: the card appears only after `LOADING_SHOW_MS = 300` and, once shown, stays at least `LOADING_MIN_MS = 400` so it never flashes.
**5. Data and core changes.** UI only, except that the core functions stay as they are (D13 lifted: no core change is needed; the worker calls `JobStore.load`, `template_store.list`, `engine.available()`, `JobStore.save`, `JobStore.delete` as they are; each is already free of Qt).

Design:
- `ui/workers.py` gains `run_background(owner, work, *, title, name="", on_done, on_failed=None, cancellable=True, show_after_ms=LOADING_SHOW_MS)`. It makes a `Task`, connects its signals with `Qt.QueuedConnection` to the owner (the signals are already emitted from the worker and received on the window thread), starts a one-shot timer for the loading view, and returns a handle with `cancel()`, `running`. At most one loading job per window at a time (a second request while one runs is refused with the existing "Bir iş sürüyor; bitince açın." line); thumbnails and Değerler side renders are not loading jobs.
- `ui/loading.py` (new, small): `LoadingCard` = `ProgressCard` moved here from `yukle_parts.py` (Yükle keeps importing it; one component, restyled once) plus `show_loading(title, name)`, `show_progress(done, total)`, `close()`. `MainWindow` owns one instance over the tab body.
- Job open becomes: window thread asks `run_background(work=lambda p: (store.load(id), template_store.list(...), store.batch_files(job)))`; `on_done` builds `JobController`, `ThumbnailService`, `KontrolScreen` (all widget work stays on the window thread) and swaps screens. The old job stays open and usable until `on_done` runs; a failure or cancel leaves it exactly as it was.
- The first-read OCR probe moves into the worker of `read_values` / `read_examples` (`engine.available()` is called in `work` and its text comes back as the failed reason, as the screens show it today); `default_engine()` is also warmed once in a worker after start-up so the first "Oku" has the answer cached.
- Delete job runs `JobStore.delete` inside the worker, under `PDFIUM_LOCK` (as `_delete_job` does now), and the job list updates in `on_done`.

Thread-safety rules (go into the module docstring and are tested):
1. A worker function receives plain data only (paths, ids, dicts, `Job` copies); it never touches a `QWidget`, `QPixmap`, `QAction`, the model or the controller. Results travel back as signals and are applied on the window thread. `QImage` and `PIL.Image` may be made in a worker; `QPixmap` only on the window thread.
2. Every PDFium call, in any thread, runs under `PDFIUM_LOCK` and holds it for one page at a time (as `analyze_pdf` does), so the window thread never waits longer than one page.
3. The worker reports progress with `progress(done, total)` at most about 10 times a second (the window thread throttles with `REPORT_EVERY` as `yukle._progress` does) and checks for cancel at the same place.
4. A worker never starts another `Task` and never calls `processEvents`.
5. Nothing is written to a job file from two threads: one writer (step 5's saver, else the window thread).
6. A result that arrives after the owner is closed or the job was switched is dropped (check the job id and a run number in `on_done`).

What is disabled while the loading view shows: opening or creating another job, Ctrl+O / Ctrl+N, the job switcher, "Dışa aktar" (Ctrl+E), the read buttons, and tab switches that would show the job that is still loading (the tabs stay for the old job; the Yükle tab stays for the job list). Each disabled command gets the existing reason "Bir iş sürüyor; bitince açın." (tooltip and status). Window close during a loading job: the loading job is cancelled first, then the existing close path runs. Undo, Ctrl+S and editing in the old job keep working.

**6. Tests.** `tests/ui/test_workers.py` (new, fake slow work with `threading.Event`, no sleeps over 0.3 s): (a) the window keeps processing events: a `QTimer` counter ticks every 20 ms while a patched `JobStore.load` blocks for 1.5 s; at least 50 ticks, and none of them more than 100 ms apart (measures the longest gap between ticks, the real "window not blocked" check); (b) loading view absent for work under 300 ms, visible after 300 ms, hidden at least 400 ms after it appeared (use a monkeypatched clock); (c) cancel with Ctrl+. and the button: old job still open, no new controller, nothing saved, status says "İptal edildi; hiçbir şey değişmedi."; (d) error: `JobFileError` and `OSError` surface as the Turkish error line and toast, loading view closes, old job intact; (e) a second open while loading is refused with the reason; (f) closing the window during a load: no crash, no signal into a dead widget; (g) result arrives for a switched job: dropped; (h) a source-level check that no module-level worker function used with `run_background` imports or names `QWidget` (cheap guard for rule 1) and a runtime guard `assert_window_thread()` called in `LoadingCard` methods, tested by calling them from a thread (must raise); (i) `engine.available()` is not called on the window thread (patch it to record `threading.current_thread()`). Existing tests that open a job synchronously (`yukle.open_job` then reads state) get a `qtbot.waitUntil(lambda: window.controller() is not None)`; a test-only `run_background(..., inline=True)` is not allowed because it would hide the very bug. Perf: `perf-profile` 800-page runs before/after (fake and `--real`) must not be slower; new case in `perf_kontrol.py` or the test (a): longest event-loop gap during open under 100 ms. Failure to catch: a loading view that stays after an error or cancel; a result applied to the wrong job.
**7. Risks.** Two sources of truth while loading (old job open, new job coming): all UI that reads `controller()` keeps the old one until the swap, so the swap is one function and tested for a half-built state. Background write-behind (step 5) can lose the last edits on a crash or power cut: it flushes on close, on Ctrl+S, before export and before a job switch, shows "Kaydediliyor…" while the queue is not empty, and "Kaydedilemedi" with the retry exactly as today; if the owner prefers no write-behind, the step is dropped and saves stay synchronous. Cancel is only offered where the work can stop (open, delete of many files cannot); non-cancellable work shows no "İptal et" and no "iptal" note. Qt `QThreadPool.globalInstance()` is shared with reads and exports, whose own screens already refuse a second job; the loading job is single so it cannot starve them.

**Shortcut contract rows it adds:** none. It reuses `yukle.iptal` (Ctrl+.): the row's "when" column adds "a job is opening"; and `app.yeni_is`, `app.dosya_ekle`, `app.disa_aktar` get the disabled reason above while a loading job runs.
**Rules it must meet:** HIG-CTL-07 (show activity for actions that do not finish instantly), HIG-MOT-03 (the person is never made to wait for motion; cancel), DEC-MOT-02 (no animation added except the standard bar; reduced motion honoured), Never silent, Keyboard-first (cancel by key).
**Performance cost (800 pages):** one timer and one signal per progress step (about 10 per second); the open itself does the same work, only the disk part moves off the window thread; the window-thread part stays about 86 ms. Cache and thumbnails unchanged.

| String | Where | Meaning in English | Status |
|---|---|---|---|
| İş açılıyor | loading card title (job open) | Opening the job | draft |
| Kaydediliyor… | status item while queued saves are written (step 5) | Saving… | draft |
| Okuma motoru denetleniyor | loading card title, first "Oku" before the engine answers | Checking the reading engine | draft |
| İş siliniyor | loading card title (delete job) | Deleting the job | draft |
| İş açılamadı: {neden} | error line and toast | Could not open the job: {reason} | draft |
| İptal edildi; hiçbir şey değişmedi. | status after cancel | Cancelled; nothing changed | existing (`yukle.py:984`) |
| Bir iş sürüyor; bitince açın. | disabled reason | A job is running; open it when it finishes | existing (`yukle.py:226`) |
| İptal ediliyor… | card title while cancelling | Cancelling… | existing |
| İptal ederseniz hiçbir şey değişmez. | card note | If you cancel, nothing changes | existing |
| İptal et | card button | Cancel | existing |
| Yaklaşık {n} sn kaldı | card line | About {n} s left | existing |

Turkish wording: "açılıyor", "siliniyor", "denetleniyor" are the present-progressive forms the app already uses ("Dosyalar inceleniyor", "İptal ediliyor…", "Önizleme hazırlanıyor…" in `research/turkish-terms.md`); the sector check for the new three is left to the run that settles Turkish wording (T3).

**Owner decisions needed.**
1. Write-behind saving (step 5): after an edit the job file is written by a background saver so a slow network folder never stalls typing. Options: (a) yes, with "Kaydediliyor…" and a flush on close, Ctrl+S, export and job switch, (b) no, keep saving on the window thread (a slow share can then freeze each edit). Recommended: (a) only if the owner's jobs live on network folders; if they are on a local disk (0.6 ms measured) choose (b). This is the one choice the measurement cannot make: it depends where the owner's staff keep jobs.
2. Decided in the reconcile and by the owner's direction (engineering): the wait cursor is dropped; `motion.wait_cursor` is not built; D's I-38 print preview uses this loading card (or the preview's own "Önizleme hazırlanıyor…" band) instead. Loading card appears after 300 ms; one shared helper.

**Build steps.** (1) `loading.py` (move `ProgressCard`, assertion helper) + `run_background` + tests (a), (b), (h); (2) job open and start-up "last job" and job list in a worker, swap function, tests (c)-(g); (3) OCR probe in the worker and the start-up warm-up, test (i); (4) delete job in a worker; (5) write-behind saver, only if the owner chooses (a); (6) disabled reasons and contract-row text; (7) re-run `perf-profile` (fake and `--real`), screenshot matrix for the loading card at 100 % and 150 %, themes light, dark, hc.

---

## Check against the product (all seven)

| Check | I-17 | I-19 | I-21 | I-22 | I-23 | I-28 | I-47 |
|---|---|---|---|---|---|---|---|
| Never silent | Pass | Pass | Pass (status names the target) | Pass (empty required is Kontrol, in index.xlsx) | Pass | Pass | Pass |
| No built-in kinds or fields | Pass | Pass | Pass | Pass | Pass | Pass | N/A |
| Keyboard (key, focus, order) | Pass | Needs owner yes (Alt+N) | Pass | Pass | Pass | Pass | N/A |
| Colour (orange = Kontrol, icon + word) | Needs owner yes (word only in tooltip and Güven) | Pass | N/A | Pass | Pass | Pass | N/A |
| Layout 1366x768, 100 % and 150 % | Pass | Needs change if over 4 rows (cap) | Pass | Pass | Pass | Pass | N/A |
| Copy (Turkish, project words) | Pass | Pass | Pass | Pass | Pass | Pass | N/A |
| Local-first, no new dependency | Pass | Pass | Pass | Pass | Pass | Pass | Pass |

**Core changes in this file:** `templates/values.value_level` (I-17, shared with A's I-06), `review.set_value(required=)` (I-22), `review.can_revert` (I-23), `templates/read.py:weakest_examples` (I-28); CLI wording changes in `is degerler` (I-17), `is deger` (I-22, I-23). No job-file field is added; older job files open unchanged.
