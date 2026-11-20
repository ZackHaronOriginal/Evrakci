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

## I-47 Busy cursor for any window-thread block over 1 second

**1. Problem.** Opening a big job or the first paint of Kontrol can hold the window for seconds with no cue (A-65). `MainWindow.busy()` / `motion.busy_cursor` exist and nothing calls them. Worse, `busy_cursor` starts a timer that needs the event loop, so around a fully blocking call it never fires ([NN/g](https://www.nngroup.com/articles/response-times-3-important-limits/): over 1 s show that work is going on). Principle: Never silent (the window must not look frozen).
**2. Who and when.** Everyone on older PCs, Yükle -> Kontrol, when opening a 400-800 page job.
**3. Keyboard flow.** None; no key is needed. The cursor shows for the work started by Enter in the job list or Ctrl+O/N.
**4. Screen sketch.** None: the mouse pointer turns to the wait cursor; the status line keeps its text. No new component.
**5. Data and core changes.** UI only, no core. Step 1 is measuring which blocks really pass 1 s at 800 pages (use the `perf-profile` skill; candidates: `JobStore.load` in `yukle.py:open_job` 336, `KontrolScreen` construction in `main_window.py:_job_opened` 1196, first paint). Then add `motion.wait_cursor(expected_long: bool)`: sets the override cursor at once and calls `QApplication.processEvents()` once so the cursor is drawn before the blocking call, restores it in `finally`, and does nothing for small jobs (page count under a measured limit) to avoid flicker. Wrap only the blocks the measurement names. Longer work stays a worker with progress (D-38 pattern).
**6. Tests.** `tests/ui/test_motion.py`: cursor set before the call and restored after, also when the block raises; nested use leaves no leaked override cursor; not set for the small case. Perf: `perf-profile` before/after on the synthetic 800-page job must show no slower open. Failure to catch: a wait cursor that stays after an error.
**7. Risks.** `processEvents()` can let a click in before the block: guard re-entry (the job switcher is already disabled by `can_switch`). A cursor alone is a weak cue beyond 10 s: if a block measures over 10 s it needs a worker and progress, which is a separate idea to raise with the owner.

**Shortcut contract rows it adds:** none.
**Rules it must meet:** HIG-CTL-07 (show activity for actions that do not finish instantly), HIG-MOT-03, DEC-MOT-02 (no animation added).
**Performance cost (800 pages):** one `processEvents()` call (< 5 ms); no extra work otherwise.

| String | Where | Meaning in English | Status |
|---|---|---|---|
| (none) | | | |

**Owner decisions needed.**
1. Decided in the reconcile (engineering): only above a measured page count. `motion.wait_cursor` is shared: disa-aktar I-38 uses it for the 800-row print preview.
**Build steps.** (1) measure with `perf-profile`, list the blocks over 1 s; (2) `wait_cursor` + tests; (3) wrap the named blocks; (4) re-run perf.

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
