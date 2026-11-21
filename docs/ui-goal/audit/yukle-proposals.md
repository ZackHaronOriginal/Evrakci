# Yükle audit: proposals for the owner

Nothing here is changed in `src`. Each item adds Turkish text, changes how A looks or behaves, or needs a decision.
Evidence ids are rows of `yukle-findings.md`.

## P-yukle-01 (F-yukle-18, S3): the same file added twice

Measured: P-139, `batches 2 -> 4` after two adds of one file; pages, Kontrol and the export count the scan twice.
Needs new text (a warning) and a decision on behaviour. Options:
1. Warn after the read: "tarama-1.pdf zaten ekli." with "Geri al" in the toast (the add is already one undoable edit, so no question is needed).
2. Skip a batch whose file name and page count match an existing one and say so (loses a legitimate second copy).
3. Leave as is (the user may scan the same sheet twice on purpose).
Recommendation: option 1; no behaviour change, only a sentence. Needs the owner's yes for the sentence.

## P-yukle-02 (F-yukle-19, S3): one unreadable file drops the good ones

Measured: P-135 (`batches 1 (before 1)` after one good and one broken file), P-140. The failure is raised while counting pages
(`ui/yukle.py:_begin work`) and while analysing (`add_batches work`), before anything is attached, so the whole add is dropped.
Not fixed because keeping the readable files changes the counting phase, the progress rows (`_Reading`) and the result
message (the bar names only one file; naming all needs new text). Options:
1. Keep the readable files, report each failed file with the existing sentence "PDF açılamadı: <dosya>" in one bar line per file.
2. Same, and mention a password for protected PDFs (new text).
3. Leave as is: nothing half-added is the current promise.
Recommendation: option 1, needs the owner's yes on the behaviour.

## P-yukle-03 (F-yukle-42, S3, the S1 question is answered): name the cost of Del in the toast

The data-loss question is closed: removing a batch that has cuts, deletes, a filter, a rotation, a template and read values and
pressing Ctrl+Z restores all of it and the batch file stays on disk (`tests/ui/test_yukle_audit.py::test_undo_of_removing_an_edited_batch_restores_job_data_and_the_batch_file`).
The remaining finding is feedback only: the toast "<dosya> işten çıkarıldı." says nothing about the edits that went with it.
Option: "... işten çıkarıldı; sayfalarındaki kesme ve silmeler de gitti." when the batch has edits (new text; the number of edits is known from the job).

## P-yukle-04 (F-yukle-39 part, S3): Qt buttons

Done without new text of ours: Qt's own `qtbase_tr.qm` is loaded at start (`app.py:install_qt_translation`), so "OK / Cancel / Yes / No"
read Tamam / İptal / Evet / Hayır. Open for the owner: the file is shipped in the PySide6 wheel
(`PySide6/Qt/translations/qtbase_tr.qm`); the frozen Windows build has to keep that folder (not checked here, no Windows build in this environment).

## P-yukle-05 (F-yukle-08, rest): the shared toast placement

Done: the toast label wraps to a second line (`feedback.py:_Toast`, one line changed) and Yükle shortens the file name; a screen
reader hears the full name (new optional `spoken` argument of `Toaster.show`). Not changed: `feedback.py:_place` still lets a
toast wider than the window start at x = -4 (shadow room); with wrapping the width is capped (592 px) so this no longer shows at 1366 px.

## P-yukle-04 addendum (F-yukle-39)

`install_qt_translation` now logs a warning when `qtbase_tr.qm` is missing (the buttons then stay English). The frozen build is
still unchecked: `packaging/` does not add the `.qm` explicitly.

## Not changed here (findings with "needs owner = yes", unchanged from the findings file)

F-yukle-09, 11, 16, 20, 21, 22, 23, 24, 25, 28, 29, 31, 33, 34, 35, 37, 40, 41, 43 to 48: each adds text, changes the look of A
or the motion rules (D7), so they wait for the owner. F-yukle-07 (the overlay counts 200 files) needs "200+" text or a count
off the window thread; not done. F-yukle-26 (search icon is a button), 27 (thousands dot), 30 (busy cursor delay), 32 (layout
margins), 36 (keys with no job), 38 (tool limits) and 49 (announce after a move) need no text but are S4: left open.

## P-app-01 (B-035): the close confirmation after a failed save

Done without new text: when the last save failed, closing the window (also Ctrl+Q), İşi kapat (Ctrl+W) and opening another job first retry
the save (`main_window.py:_unsaved_refusal`). If it still fails, the close is blocked and the existing "Kaydedilemedi: ..." status is shown.
No existing dialog text fits ("Bir iş sürüyor. Durdurup kapatılsın mı?" is about running work). Proposal for the owner: a Yes/No
question such as "Değişiklikler kaydedilemedi. Yine de kapatılsın mı? Son değişiklikler kaybolur." so the window can still be closed
when the folder stays unwritable (now the only way out is to fix the folder or use Yeniden dene).
