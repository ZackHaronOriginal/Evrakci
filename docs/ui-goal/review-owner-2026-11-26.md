# Review: everything built from the owner's answers of 2026-11-26

Range `git diff 3f38411 HEAD`, src, tests and tools only (HEAD 8f78e91). Group C itself (I-07,
f774048..f590a5f) was reviewed in `review-group-c.md`; only its review fixes (0f4c6ab) are
checked here. Cross-step review (Opus), read-only. Severity as in `bugs.md`.

Checked and agreeing:
- **B-005 retention.** `delete_older_than` skips a job with `last_export is None`. The window
  start (`app.py`) and the CLI (`apply_retention`) call the same function. Tests are in
  test_retention.py and test_ledger_b.py (`test_b005_*`); the xfail is removed.
- **Q-12 / B-056.** The cell shows the suggestion with "← okunan …" beside it, or on a second
  line when it does not fit. Enter / "Öneriyle onayla" store the suggestion and Shift+Enter /
  "Okunanla onayla" the read. Each is one undo step, and the toast is "{değer} kaydedildi
  (öneri/okunan)." A newer confirmation replaces only its own kind of toast. A value without a
  differing read keeps the single "Onayla". Shift+Enter does nothing there (test).
- **B-057.** Inter-SemiBold is found in the package and in the frozen `lib/` (freeze_setup.py
  line 45). There is a fallback, and Ç/İ draw (test). The text fits the A4 page (probe: ink at
  x 393..846 of 1240).
- **Q-03.** `enforced: true` is set exactly on DEC-TYP-01..03, DEC-CON-01/02, AUD-HIT-01..03,
  AUD-A11Y-01 and DEC-FOC-01. DEC-CON-03 and the HIG rows stay report-only. CI runs
  `--enforce`, and stale known-fails are reported.
- **Kontrol gerekenler.** The window and CLI use the same `plan_names(..., check_subfolder)`.
  The path limit counts the subfolder, clashes are checked per folder, and a cut name moves into
  the subfolder. index.xlsx and the check sheet carry `item.relative`. Old PDFs in an existing
  subfolder block the export, in both the pre-flight and the writer. The setting defaults to on,
  and an older file loads with it on. The parity test and the 800-document timing test exist.
- **Delete warning.** It is a bilgi row, shown only when "delete after export" is set, the text
  layer is on and nothing needs a check. That matches `may_delete_after_export`.
- **Yükle Q7.**
  - Repeated file: a warning toast with Geri al. The add stays.
  - Multi-add: broken files are counted and prepared in the worker. The good files are kept, and
    every failure is listed. All broken: nothing changes.
  - Close after a failed save: each attempt retries and asks one non-blocking WindowModal
    Yes/No. Only Yes lets the edits go (`_discard_ok`). A hung write cannot hold the close.
- **Q-16.** Line-edit action buttons and the clear button are control-height click areas (24
  wide), and the clear button's tooltip is "Temizle". `word_role` lifts the quiet and green words
  to `text`. The status-bar labels use `text`. The Değerler side scroll is NoFocus. The
  Reader/PageCanvas window-scroll exemption is in place. Toasts sit at the bottom left
  (`TOAST_MARGIN - SHADOW_ROOM`, test at 100/150 %). A fresh window starts in its work area,
  with no ring on the title tabs.
- **Q-23 / Q-25 / Q-26 / Q-27.** "Okuma seç" (Alt+1..4, with a real hit button as its mouse
  path). The CLI `--geri-al` on an uncorrected value gives the approved sentence (test). "Baskı
  önizleme hazırlanamadı." The subtitle compares `LastExport.state` with `job_state()`.
- **D-1 / D-3.** "N belge okundu; M belge okunamadı." and "; N tanesi Kontrol'dü". D-2 (an empty
  required value is refused) was already in place and now has a test.
- **Q-08 / Q-09.** Ctrl+G is routed on Şablonlar and Dışa Aktar. Yükle and Rehber say where to
  go. F5 is off with its reason on Kontrol and Rehber. The Ctrl+F / Ctrl+0 labels follow the
  tab. A greyed command's tooltip, its key (through a speaker `QShortcut`) and the palette all
  give the reason from `refusals.py`. `refresh_reasons()` costs 0.5-0.6 ms per call with no job
  (probe on all six tabs).
- **Group C fixes.** R-C-1: "Kayıtlı filtrelere ekle…" only after a replace that is not
  `belge`. R-C-3: the CLI `farkli` reads missing sizes. R-C-4/5/6: texts and the asserted Q-30
  text. R-C-7: the chip edge uses `edge`.
- **(5) Shortcut audit.** `--check --contract docs/ui-goal/shortcut-contract.tsv`: 0 problems,
  exit 0. `--paths --check`: 368 rows, 302 tab x action pairs, 27 exempt, 0 problems, exit 0.
- **(6) Window thread.** Page counting and batch preparation run in the worker. The close
  question does not block. `job_state` runs only for a print. The only file I/O added on the
  window thread is the settings read in Dışa Aktar (R-O-11).
- **(7) Tests.** The changed assertions were spot-checked. The B-035 close tests now pin the
  owner's Q7 behaviour (refused on every try, Yes closes), which is stricter, not weaker. The
  removed xfails (M-01/02/03/05/07/09/11/13/15/16/17/27/30/38, B-027/028) became real
  assertions of the approved texts. `LONG = 190` in test_export.py keeps the same check and
  leaves room for the subfolder. One gap is R-O-13.

Targeted runs (offscreen):
- test_q7_yukle, test_q6_fixes, test_refusals, test_q5_shortcuts: 80 passed.
- test_cli_values, test_retention, test_separator, test_job_format: 34 passed.
- test_cli_select*, test_export, test_exporting, test_store, test_ui_measure: 67 passed.
- test_disa_aktar subset (subfolder, delete warning, parity, subtitle): 13 passed.

| ID | Sev | File:line | Finding | Suggested fix | Action |
|---|---|---|---|---|---|
| R-O-1 | S2 | src/evrakci/cli/main.py:44 | `evrakci ayar saklama <değer>` saves `Settings(args.deger)`, so `check_subfolder` is put back to its default (True). Probe: with `{"saklama":"sakla","kontrol_ayri_klasor":false}`, `ayar saklama 30` writes `{"saklama": "30", "kontrol_ayri_klasor": true}`. The user turned the subfolder off in Ayarlar or Dışa Aktar. After a retention change in the CLI, the next window or CLI export puts the documents to check into "Kontrol gerekenler" without a word. The window's own save keeps the setting (`dataclasses.replace`). No test covers the CLI path. | Load the current settings (a broken file falls back to the defaults, as the dialog does) and `dataclasses.replace(current, retention=...)`. Add a CLI test that `kontrol_ayri_klasor: false` survives `ayar saklama`. | fix now |
| R-O-2 | S3 | src/evrakci/pipeline/store.py:288 | The day limit deletes any job that was ever exported once its job.json is N days old, also when it was edited after that export. Example: export on day 0, a week of corrections (cuts, values) with no new export, then 30 days idle: the job and all the unexported corrections are deleted. `job_state` already tells "changed after the last export" (Q-27). The owner's words ("deletes only jobs that were exported") are met literally, but the edits are lost. | Owner: also require `last_export.state == job_state(job)` (with an empty state counting as unchanged, as the subtitle does), or keep it as it is and say so in the Saklama note. Add a test either way. | ledger |
| R-O-3 | S3 | src/evrakci/ui/disa_aktar.py:582-590, 573-580 | When the settings file cannot be written (OSError) or is broken (`_settings()` is None), unticking "Kontrol gerekenleri ayrı klasöre koy" is not saved and nothing is said. The next `refresh()` (tab change, job reload) calls `_load_separate`, which ticks the box again, so an export after a tab switch writes into the subfolder although the user unticked it. | Keep the session's choice in the screen (`self._separate_choice`) and let `_load_separate` prefer it. Or say "Ayar kaydedilemedi: …" in the status bar. | ledger |
| R-O-4 | S3 | src/evrakci/ui/settings_dialog.py:330-335 | A failed save of the Dışa aktarma checkbox writes "Ayar kaydedilemedi: …" into `retention_note`, which is on the Saklama page. On the Dışa aktarma page the box shows a state that is not saved, and nothing is said there. | Give the export page its own note label, or put the box back and say it there. | fix now |
| R-O-5 | S3 | docs/ui-goal/baseline/known-fails.tsv:6-8, tools/ui_measure.py:151-162 | Three DEC-CON-01 rows are justified only by "CI only (B-104) ... cause unknown". The key is (rule, widget path) for every theme, size and text size. So the Değerler value column 1, a Yükle KvRow label and a Şablonlar inspector label are not contrast-checked at all in CI. A real regression in that widget (for example in HC or at 150 %) would pass. The value on CI (1.01:1) is what an empty or not-yet-painted label measures, so the rows probably hide a timing problem in the tool, not a colour. | Narrow the key to (rule, widget, theme, size, text) as seen on CI, and attach the CI ui-measure.tsv rows to B-104. Find the cause: let the tool wait for a settled non-empty text, or record the sampled colours. The two AUD-HIT-02 zoom rows are justified (Q-32 is open). | ledger |
| R-O-6 | S4 | tools/ui_measure.py:143-148 | `exempt_row` drops AUD-A11Y-01 and DEC-FOC-01, both enforced under Q-03, for every widget below `PageCanvas`. The owner's exemption (Q-16) was for the window-scroll rule. A focusable child added to the canvas later (a box editor, a handle) would skip the name and ring checks without a row in known-fails. | Move these two into known-fails.tsv with a reason (visible and dated), or limit the exemption to the canvas's inner surface class. Owner note under Q-16. | ledger |
| R-O-7 | S4 | src/evrakci/ui/yukle.py:607-610, src/evrakci/cli/jobs.py:109-110 | Window and CLI differ. The CLI `is olustur a.pdf b.pdf a.pdf` warns "a.pdf zaten ekli.", and the window's new job from the same files says nothing (`repeated_files` is only in `_batches_prepared`). The other way round: the CLI `olustur` with one broken file refuses the whole job ("PDF açılamadı: bad.pdf", exit 2, probe), while the window keeps the good files. | Warn in `create_job` too (the same `repeated_files([], names)`). Write down that the CLI create is all-or-nothing on purpose, or make it keep the readable files and list the failures. | ledger |
| R-O-8 | S4 | src/evrakci/ui/refusals.py:101-105 | `_export`: when Ctrl+E is off for a reason other than an engel, `blocked` falls back to all findings. The reason then becomes "Dışa aktarılamıyor: " + the first finding's title, which can be a bilgi or kontrol row, or "" (the no-job "bilgi" finding has an empty title, giving "Dışa aktarılamıyor: "). | Use only engel rows. Otherwise return the bare "Dışa aktarılamıyor." that Q5 lists. | fix now |
| R-O-9 | S4 | src/evrakci/pipeline/writer.py:50,57; src/evrakci/pipeline/exporting.py:142-146 | A file (not a folder) named "Kontrol gerekenler" in the output folder passes the pre-flight (no .pdf). Then `target.parent.mkdir` raises FileExistsError after the earlier documents are already written. That reports "önceki bir dışa aktarımdan dosya var (...)", with no "Yazılanlar" list. The same handler shows only `old[0].name` for an old PDF in the subfolder, not its folder. | Check `out_dir / CHECK_SUBFOLDER` for a non-folder in `folder_state` and before writing, and give the relative path in the message. | ledger |
| R-O-10 | S4 | src/evrakci/pipeline/job.py:249-254 | `job_state` hashes the page sizes, `read_errors` and `value_sources` too. A job exported from the CLI before its missing page sizes were filled gets a different state once the window fills them on open. The printed subtitle then says "Dışa aktarma planı, henüz yazılmadı" for an export nobody changed (Q-27). | Leave the derived page data out of the fingerprint (sizes, ink ratio), or record the state after the sizes are applied. Add a test with an older job. | ledger |
| R-O-11 | S4 | src/evrakci/ui/disa_aktar.py:566-571 | `_deletes_job` reads ayar.json from disk on the window thread on every `findings()` (every folder keystroke and pattern sync). It is small, but it is file I/O per keystroke on a slow share or USB profile. | Read the settings once per `refresh()` and when the Ayarlar dialog closes. | ledger |
| R-O-12 | S4 | src/evrakci/ui/degerler.py:1646 | The worker writes `self._engine_reason` on the screen widget. The Q7 review (c38f503) made Yükle's worker keep off widget attributes, and this is the same pattern. It is harmless today (one str), but it is the rule the run set. | Return the reason in the exception (`EngineUnavailable` text is already the message) and compare with the class, not with a stored attribute. | ledger |
| R-O-13 | S4 | tests/ui/test_disa_aktar.py:1189-1207 | The delete-warning test never shows the row on a real screen: the screen case has a document to check (so no warning), and the "shows" case calls `findings()` directly. A break in `_deletes_job` → `_findings_rows` wiring with a clean job would pass. | Add a screen case with no Kontrol document and "delete after export" set: the bilgi row with `DELETE_WARNING` is in `screen._findings`. | ledger |
| R-O-14 | S4 | src/evrakci/ui/degerler.py:1334-1340 | D-3 punctuation varies: "6 değer onaylandı" (no stop), "6 değer onaylandı; 1 tanesi Kontrol'dü." (stop), and with skipped values "...; okunamayan 2 değer atlandı" (no stop). | One rule: always end with "." or never. This is a text change (owner list). | ledger |
| R-O-15 | S4 | see list below | Turkish text that is not in decisions.md, Q-29/Q-30, refusals.py or the Q5 list in shortcut-mismatches.md, nor in an approved proposal. | Put these on the owner list (OWNER-QUEUE) as built, or reword to approved text. | ledger |
| R-O-16 | S4 | src/evrakci/cli/main.py:51 | The CLI confirmation for a day limit still says "{N} günden eski işler silinir". After B-005 only exported jobs are deleted. The window label was declared accurate, but the CLI sentence is not. | "{N} gün sonra dışa aktarılmış işler silinir" or similar. This is new text, so it goes on the owner list with R-O-15. | ledger |

R-O-15, unlisted texts (file:line, text):
1. src/evrakci/ui/yukle.py:146: "Parola korumalı olabilir". P-yukle-02 recommended option 1
   ("PDF açılamadı: <dosya>" only). This is option 2's new text, which was not approved.
2. src/evrakci/ui/yukle.py:672: "{N} dosya zaten ekli: a, b, c…" (and "{N} parti eklendi. "
   before it). P-yukle-01 approved only "<dosya> zaten ekli.".
3. src/evrakci/ui/degerler.py:1736: "Okuma durdu. Kalan belgeleri 'Yalnızca eksikleri oku' ile
   deneyebilirsiniz." (D-1, unexpected error). The proposal (F-degerler-05) words only the
   count.
4. src/evrakci/ui/actions.py:372: tooltip "Açık düzenleyicide 1-4. okumayı al" (Okuma seç).
5. src/evrakci/cli/jobs.py:897-899: option `--kontrol-ayri-yok` and its help "kontrol
   gerekenleri ayrı klasöre koyma". The decision covers the window label only.
6. src/evrakci/pipeline/settings.py:61: "Geçersiz ayar: kontrol_ayri_klasor: …". This follows
   the Q-29 pattern "Geçersiz ayar: …", but the key and the use are new.
7. src/evrakci/ui/refusals.py:19: "Sayfa {number} bu görünümde yok." (9edb37c). It is in
   refusals.py, so it is allowed by the run lead's rule, but it is missing from the Q5 list in
   shortcut-mismatches.md that the owner sees.
8. src/evrakci/ui/disa_aktar_model.py:202: DELETE_WARNING "Yazıldıktan sonra bu iş silinir;
   yalnızca dışa aktarılan dosyalar kalır.". It is worded in disa-aktar-findings.md, and the owner
   approved the behaviour, not this sentence. Listed for completeness.

Counts: S1 0, S2 1, S3 4, S4 11.

(8) known-fails.tsv: the two AUD-HIT-02 zoom rows are justified (the Q-32 owner choice is
open). The three DEC-CON-01 "CI only, cause unknown" rows are not justified as they stand
(R-O-5).
