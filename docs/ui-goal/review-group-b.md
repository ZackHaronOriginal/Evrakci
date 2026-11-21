# Group B review (quick wins, `b3709f9..c7008ab`)

Scope: `src tests tools .github shortcut-contract.tsv shortcuts.md` across I-47 a+b, I-21, I-19, I-17,
I-23, I-22, I-28, B-089 and the side-panel fix. Read-only review (Opus), 2026-11-20. Severity as in
`bugs.md`. Known ledger rows B-083..B-090 are not repeated.

Owner rules checked: no shortcut-only action (every new key D, K, R, N, Shift+N, Ctrl+L has a menu
item and the contract/`shortcuts.md` rows match the registry; Alt+1..4 has the click path and is
held by Q-23); new Turkish text (all user-visible strings in the spec tables except R-B-9); D13
(core changes `value_level`, `can_revert`, `set_value(required)`, `weakest_examples`,
`save_dict` have core tests; job format unchanged); synthetic tests only; no test was weakened
(sync asserts became `waitUntil` for the write-behind saver; B-012 xfail removed because fixed).

Suite (`QT_QPA_PLATFORM=offscreen pytest -q -p no:cacheprovider tests`, Linux, at c7008ab): 2681 passed, 4 skipped, 202 xfailed, 0 failed (10 min 08 s). `ruff check src tests tools`: clean.

| ID | Sev | File:line | Finding | Suggested fix | When |
|---|---|---|---|---|---|
| R-B-1 | S3 | ui/sablon_live.py:169-171 | I-28 x I-47: a "Bütün örneklerde dene" that is still running when another job opens (Şablonlar has no `busy()`, so `_switch_refusal` lets the switch through) or another template opens lands in `_all_done` afterwards: `tried_all = True` and job A's / template A's results drive N, Shift+N, Ctrl+L and the example marks on job B. `_refresh_examples` and `open_template` reset the state but do not cancel or tag the task. | Remember `(job_id, template.id)` when the try-all starts; drop the result in `_all_done` (or cancel `_all_task` in `_refresh_examples` / `open_template`). Test: switch job during a gated try-all. | fix now |
| R-B-2 | S3 | ui/saver.py:211 | A stalled write reports `os.strerror(ETIMEDOUT)`: C-library text, English (on the Windows CRT possibly "Unknown error"), shown as "Kaydedilemedi: ..." in the band, status and the Ctrl+S toast. Not Turkish, not from a spec table. | Pass a Turkish reason from the I-47 table (needs a new approved string, e.g. a draft row "disk yanıt vermiyor"), or show "Kaydedilemedi" with no reason. | ledger |
| R-B-3 | S3 | ui/workers.py:100, 269-272 | Every `run_background` makes a `Background` parented to the window and never deleted; it keeps its task and callbacks. The delete-after-export callbacks (`disa_aktar.py:1079` `done`) hold the deleted job's `JobController` (whole job + undo snapshots), so each deleted job stays in memory for the session. | `deleteLater()` the previous handle in `run_background` once it is not running and its close timer is idle, or clear `_on_done/_on_failed/_on_cancelled/task` in `_finish`. | fix now |
| R-B-4 | S3 | ui/degerler.py:1362-1366 | The "Zorunlu değer boş bırakılamaz; Kontrol'e alındı." toast is shown whenever `set_value` returns False on a required cell, also when `_edit` failed (e.g. `KeyError` "değerler okunmadı") and the typed text was not empty: a wrong "it is now Kontrol" after the real error in the status line. | Toast only when the cleaned text is empty (`not " ".join(text.split())`). | fix now |
| R-B-5 | S3 | cli/jobs.py:493-497 vs ui/degerler.py:1328 | Window and CLI differ on Okunana dön: the window disables R for an unedited value (`can_revert` needs `edited`), `is deger --geri-al` still reverts it (Emin value becomes Kontrol). | Use `can_revert` in the CLI too (error "nothing to go back to"), or allow it in the window; one rule in `review.py`. | ledger |
| R-B-6 | S3 | tests/conftest.py:46-70; ui/gc_guard.py:69 | Order dependence: the first test that makes a `JobController`, a `Task` or calls `configure_application` turns the cycle collector off for the rest of the session (`gc.disable()` + `gc.freeze()`); the look fixture restores fonts and palette, not GC. Later tests collect cycles only while they spin the event loop (a test that never does collects none); memory grows over the 25 min run and finalizer timing depends on which test ran first. The module fixture also builds a QApplication for pure core tests. | Session fixture that installs the guard once up front (same state for every order), or restores `gc.enable()` / uninstalls at module end; skip `_look` for modules without Qt. | ledger |
| R-B-7 | S3 | ui/sablon_read.py:34-40 | I-17 spec says `sablon_read.level_of` reuses core `value_level`; it keeps its own rule (Okunamadı = empty text, threshold-based Kontrol). Şablonlar and Değerler can name one reading differently. | Route `level_of` through `value_level` (keep the template minimum as an extra Kontrol rule) and add a parity test. | ledger |
| R-B-8 | S4 | ui/degerler.py:1567; spec I-47 table | "Okuma motoru denetleniyor" (approved draft) is not built: the first Oku shows "Okunuyor: 0 / N belge" while the engine probe runs, and a missing engine ends as "Okunamadı: ..." after the progress row flashed. Spec test (i) exists. | Show the approved title while the probe runs, or record the deviation in the spec. | ledger |
| R-B-9 | S4 | ui/loading.py:138-139; ui/sablon_weak.py:70 | Text not in a spec table: accessible name "Yükleme"; composed tooltip "Önce Ctrl+T ile örnekleri deneyin. (Sonraki zayıf örnek (N))" (nested brackets). | Use "İş açılıyor"/the card title as the name; tooltip = the reason alone. | ledger |
| R-B-10 | S4 | ui/yukle.py:387-396; ui/main_window.py:1266-1274; degerler.py, sablon_live.py, sablon_sync.py | One "is a job loading" question asked four ways: `MainWindow.loading()`, `YukleScreen.loading()/_loading_cancellable()` (copies reading `_background`), and five `getattr(window, "loading", lambda: False)()`. | One helper in `workers` (`loading(owner)`, `loading_cancellable(owner)`) used everywhere. | ledger |
| R-B-11 | S4 | ui/yukle.py:464; ui/main_window.py:1207 | `refresh_jobs` and `refresh_recent_jobs` repeat the same "run counter + pending task set + queued done" worker pattern; each job open reads every job file twice (list + recent), with full `store.load`. | One `workers.fetch(owner, work, on_done)` with drop-older semantics; the recent list could reuse the job list's entries. | ledger |
| R-B-12 | S4 | pipeline/store.py:142, 155 | Two copies of the PermissionError retry loop (`save_dict`, `_read_text`). | One `_retry_locked(fn)` helper. | ledger |
| R-B-13 | S4 | ui/disa_aktar.py:1135 | Dead after the fix round: `_delete_job(controller, ...)` is used only by `test_p4_disa_rehber.py:63`. | Point the test at `_delete_job_files` and drop the wrapper. | ledger |
| R-B-14 | S4 | cli/jobs.py:456-458 | Dead branch text: `value_level == "okunamadi"` implies no suggestion, so `hint` is always "" there. | Print `[okunamadı]` directly. | ledger |
| R-B-15 | S4 | ui/loading.py:94 | `ProgressCard.show_progress` imports `yukle_parts` late because `yukle_parts` imports `loading` (cycle). | Move `eta_text`/`rate_text` into `loading.py`. | ledger |
| R-B-16 | S4 | ui/main_window.py:1300-1340 | `_sync_loading` saves tooltips at load start and puts them back at the end; a screen that changed its tooltip meanwhile (Şablonlar weak-example tips, Değerler read reasons) gets the stale one back. | Let each screen's `_sync_actions` own its tooltip and read `loading()`; drop the save/restore map. | ledger |
| R-B-17 | S4 | tests/ui/test_saver.py:137, 144; tests/ui/test_workers.py:50 | Wall-clock asserts (edit < 100 ms, longest 20 ms-tick gap < 100 ms) are what the spec asks for, but they share the window thread with `gc_guard` ticks and are the likeliest flaky tests on Windows CI. | Keep; if one flakes, raise the gap bound to 150 ms on CI only with a comment, never drop it. | ledger |

Interactions checked and found sound: snapshots handed to the saver are fresh dicts (`job_to_dict`
copies everything), so undo/redo never mutates a dict the writer is serialising; frozen job =
no edit, no undo/redo (`_GuardedStack`, `_undo_to`), no save, delete waits for the write in flight
(`wait_idle`), a failed delete rewrites `job.json` (B-088); I-22 emptied value and I-23 revert make
the same core state and R is off for it; Geri al on the required toast is bound to its own step;
`gc_guard.working()` wraps every worker (Task, saver, thumbnails, side-panel renders) and every
start path calls `install()`; close during load cancels it and drops late results (`_closed`);
Ctrl+S, export, job switch and close all flush through `when_idle` with the 10 s stall bound.
