# Review: group C (I-07 saved filters)

Range `git diff 50f8021 f590a5f`, group C files only (commits f774048, ee89cf3, 079af66; the
group A fix merge afb323f, B-102 `store.save_dict` and the docs commits are not reviewed here).
Cross-step review (Opus). Severity as in `bugs.md`.

No S1 or S2 found. Checked and agreeing: `SavedFilter(name, kind, params)` and
`Template.saved_filters` with add / remove / rename (NFC, trimmed, unique by casefold, at most
20, Turkish `TemplateError` texts as approved in Q-29); `TEMPLATE_FORMAT_VERSION` stays 1, a file
without the key loads (test), `template_revision` is unchanged by a filter (test); export and
import keep the filters (test); template writes stay atomic (`_write`, mkstemp + os.replace);
nothing is written to the job, `index.xlsx` or the export (no change in `job.py`, the chips only
call `select_pages` and set the selection); `select_pages` is the single AND path for the chips,
the count line, the per-chip "0" and `is sec --sablon`, an unknown kind or settings that raise
are reported (`unknown_kinds`, `unknown_at`), never dropped; the window and CLI parity test
compares the page positions and the count line; undo of a filter step on a template that is not
open only patches `saved_filters` of the file as it is now (test), a failed apply says so.
Strings: every window string is in the spec table or existing ("Kaydet", "Vazgeç", "Sil",
"Yeniden adlandır", "Şablon yok", "Geri al", "Eşleşen sayfa yok."), the error and CLI texts are
the ones Q-29 approved as built, Ctrl+Shift+F with nothing to focus says "Kayıtlı filtre yok"
(Q-29), the two usage errors are the Q-30 texts (Q-30 is still open in OWNER-QUEUE; built with
those texts, as the queue says). O-12 key Ctrl+Shift+F, O-13 (template only), O-21 ("filtre",
"Kayıtlı filtreler") met. Shortcuts: the action is in Araçlar, the command bar's Diğer komutlar
and the palette; chip keys are local (ShortcutOverride accepted only for the seven local keys,
test). `audit_shortcuts.py --check --contract docs/ui-goal/shortcut-contract.tsv`: 0 problems,
exit 0; `--paths --check`: 362 rows, 0 problems, exit 0. Look against `fluent-reference`
tokens.md: 32 px high (Button / TextBox min height 32), pill radius (Circular), padding 12 (M),
gaps 6 (SNudge) and 8 (S), icon 16 (system icon), close target 24, text body-medium 15 px; on =
accent fill + check (text-on-accent 7.6:1 light, 8.7:1 dark, 14.4:1 HC), off = outline + empty
ring, inert = disabled text + the word "Tanınmıyor" in text-2. No orange (accent is the cabinet
green; error text uses `danger`). Window thread: one count pass per chip only after a job or
template change (idle timer), under 1 ms per kind on 800 pages measured here; the template write
is a few hundred bytes on the window thread, as the spec and a timing test say.

| ID | Sev | File:line | Finding | Suggested fix | Action |
|---|---|---|---|---|---|
| R-C-1 | S3 | src/evrakci/ui/kontrol.py:700-701, src/evrakci/ui/kontrol_saved.py:215-236 | "Kayıtlı filtrelere ekle…" is offered after any Seç, also in the modes "add" and "within" and for "Bu belge". Only the criterion is stored, so the chip later selects something else than the user saw when saving. Example: Tek sayfalar "within" a selection of document 2 is saved as `tek {"within": true}`; on the next job the chip selects the odd pages of every document. "Bu belge" stores `{"number": N}`, the current document of this job, so the chip picks document N in every later job. Spec §7 says a filter keeps only the kind and settings the user typed. | Remember the result only when `dialog.mode() == "replace"` and the kind is not `belge`. Add a UI test for both cases. | fix now |
| R-C-2 | S3 | src/evrakci/ui/main_window.py:1032-1039, src/evrakci/ui/kontrol_saved.py:243-257 | The chip steps are on the Şablonlar stack, and Kontrol's Ctrl+Z uses the job stack. Example: Del on a chip, then Ctrl+Z on Kontrol: the job's last edit (say a cut) is undone and the chip stays deleted. Once the toast is gone, the only way back is Ctrl+Z on Şablonlar. There it changes a template that may not be on screen (the step sits on the stack of whatever template is open, the B-055 pattern), and opening another template clears it. The contract says "a chip's Del is undoable". Tests only call `sablon.undo_stack.undo()`. | Spec gap, owner decides. Options: on Kontrol, Ctrl+Z takes the newest step across the job stack and the template steps made from Kontrol; or Kontrol keeps its own stack for template steps. Add a key test either way. | ledger |
| R-C-3 | S3 | src/evrakci/cli/jobs.py:251-270 (compare 300-302) | `is sec <iş> --sablon <ş>` with a saved `farkli` filter never reads the missing page sizes of an older job. The `is sec farkli` path does read them (`apply_page_sizes(..., store.read_sizes(...))`), and the window fills them when it opens the job. If the job was never opened in the window, the CLI counts those pages as "bilinmiyor" and does not select them, so the CLI and the window give different pages. | In `select_saved`, call `apply_page_sizes(job, store.read_sizes(store.size_requests(job)))` when any chosen filter or `extra` is `farkli`. Add a parity test on a job without sizes. | fix now |
| R-C-4 | S4 | docs/ui-goal/shortcut-contract.tsv:106, docs/ui-goal/shortcuts.md:131 | Both still say Ctrl+Shift+F without a row gives "Hiçbir filtre açık değil". The code (079af66, Q-29) says "Kayıtlı filtre yok", and the test pins that. | Replace the text in both rows. | fix now |
| R-C-5 | S4 | src/evrakci/cli/jobs.py:266-268, tests/test_cli_select.py:171-176 | `is sec --sablon` on a template with no saved filters prints "Hiçbir filtre açık değil" (exit 0). There is nothing to turn on. The window says "Kayıtlı filtre yok" for the same case (Q-29). | Print "Kayıtlı filtre yok", which is approved text, and update the test. | fix now |
| R-C-6 | S4 | tests/test_cli_select.py:138-139 | The Q-30 text "--sil, --sablon ile birlikte kullanılamaz." is checked only through "usage:". Any argparse error, for example an unrecognised `--sil`, would pass. | Assert the Q-30 text in `err`. | fix now |
| R-C-7 | S4 | src/evrakci/ui/kontrol_chips.py:288 | The off chip's outline uses `stroke`. In light mode that is 1.25:1 on the work layer (1.08:1 on base); in dark mode 1.38:1. Fluent's Stroke1 is about 1.5:1, and its "Stroke accessible" for edges is 3:1. The state still reads through the ring and the check (HIG-CTL-08 met), but the "outline" the spec names is almost invisible in light mode. HC is fine (21:1). | A look row for Fluent (Q-02): Stroke1-level or stroke-accessible for the chip edge. Check in the matrix. | ledger |
| R-C-8 | S4 | src/evrakci/ui/kontrol_chips.py:416-417, src/evrakci/ui/kontrol_saved.py:155-193 | When a chip is turned on, a screen reader hears only "<ad>, açık". The count line "2 filtre açık: 7 sayfa" changes silently, and its accessible name is the row's own "Kayıtlı filtreler". Only 0 matches gets a status line. | Emit the count text on the status line after each toggle (as A does for "6 sayfa seçildi."), or give the label its own name and send a name-change event. | ledger |
| R-C-9 | S4 | src/evrakci/pipeline/templates/model.py:346-350 | `template_from_dict` runs the add checks on load. A file with 21 filters, or with two names that are equal by casefold (hand-edited, or from a later version with a higher limit), refuses the whole template. It then drops out of Şablonlar, Kontrol and reading ("Şablon dosyası okunamadı"). This follows the spec ("the same checks"), but it costs more than the filters. | Owner and engineering: load the template and report the extra or duplicate filters as unusable chips, or keep it as it is. | ledger |
| R-C-10 | S4 | src/evrakci/ui/kontrol.py:979, src/evrakci/ui/kontrol_saved.py:124,210 | `_selection_changed` now calls `self.templates()` on every selection change, also when nothing is selected. That call is `MainWindow.template_map`, which reads and parses every template file on the window thread. The chips add more reads (`_chips_recount` then `_chips_sync`, Ctrl+Shift+F, `showEvent`). It is small on a local disk, but it is file I/O per click. | Cache the template map and drop it on a Şablonlar save or stack move and on a Kontrol filter edit. Measure with 30 templates. | ledger |
| R-C-11 | S4 | docs/ui-goal/specs/qr-saved-filters.md §5, §6 | Two spec items are not done. (a) The `states` screenshot with chips on, wrapped at 150 % (only the clipping test `test_the_row_clips_nothing_at_1366x768_in_both_text_sizes` exists). (b) The release note that an older app drops `saved_filters` on its next save. | Add the matrix shot and the release-note line at release. | ledger |
| R-C-12 | S4 | docs/ui-goal/specs/README.md:173, docs/ui-goal/specs/qr-saved-filters.md "Owner decisions" 2 | O-14 says the row shows "Şablon seçin" when there is no template. Spec §4 and the string table say "Şablon yok" (existing), and that is what is built. | Align O-14 to "Şablon yok". This is a docs change only. | ledger |
| R-C-13 | S4 | src/evrakci/ui/main_window.py:1284-1292 | Undo and redo of a filter step on a template that is not open replace the file's whole `saved_filters` list with the snapshot. A filter added in between, for example with `sablon filtre-ekle`, is lost without a word. | Undo and redo the one named filter: remove or add it, and report a clash. Or keep it and note it in the docstring. | ledger |

Counts: S1 0, S2 0, S3 3, S4 10.

Suite (`QT_QPA_PLATFORM=offscreen python -m pytest -q -p no:cacheprovider -o faulthandler_timeout=600`):
1 failed, 3011 passed, 4 skipped, 205 xfailed, 1 warning in 711 s on 61ff0ed. The failure was
`tests/test_packaging_linux.py::test_documented_window_packages_match_everywhere`, a CI workflow
test outside group C. It was fixed by edbdd65 (CI only); `tests/test_packaging_linux.py` on edbdd65:
25 passed. `ruff check src tests`: All checks passed.
