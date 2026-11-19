# UI bug ledger

Maintained with the `ui-bug-hunt` skill (`.claude/skills/ui-bug-hunt/SKILL.md`). One row per bug,
newest last. Do not delete rows; change Status. Severity: S1 data loss / silent wrong output /
no keyboard path; S2 unusable in a supported theme or size; S3 visible, workable; S4 polish.
Status: open, fixed (commit or test), wontfix (reason), needs-repro.

| ID | Sev | Tab | Where (theme / size / text) | Repro | Expected vs actual | Evidence | Status |
|---|---|---|---|---|---|---|---|
| B-001 | S? | Yükle | n/a (code read, not yet run) | Ctrl+O while a read runs | Start a read, press Ctrl+O, pick files | Files added or a message; actual: nothing happens, no message | needs-repro |
| B-002 | S? | Yükle | n/a (code read, not yet run) | batch with no QR page after a filter split | Split by filter, look at batch status | Batch and inspector agree; actual: batch says Kontrol, inspector says Hazır | needs-repro |
| B-003 | S? | Yükle/Dışa Aktar | n/a (code read, not yet run) | PDF/A değil file | Export a job with one non-PDF/A file | One rule everywhere; actual: info in list, a check in outcome card, deletion rule and index | needs-repro |
| B-004 | S? | Dışa Aktar | n/a (code read, not yet run) | file-name pattern override | Edit pattern in window, restart, export; compare with CLI export | Override saved or clearly per session; actual: applies to all templates, lost on restart, CLI names differ | needs-repro |
| B-005 | S? | Yükle | n/a (code read, not yet run) | retention wording | Set retention days, have a never-exported job | Label matches behaviour; actual: label says exported jobs, limit also deletes never-exported jobs | needs-repro |
| B-006 | S? | Rehber | n/a (code read, not yet run) | blank pages option | Read the guide, look for the job setting | Window control exists; actual: only `evrakci is bos-sayfalar` sets it | needs-repro |
| B-007 | S? | Rehber | n/a (code read, not yet run) | Kaç adet … sayfa | Print 10 sheets | Page count matches wording; actual: counts sheets, prints twice as many pages; defaults 20 vs CLI 10 | needs-repro |
| B-008 | S? | Dışa Aktar | n/a (code read, not yet run) | delete after export | Export with delete-after-export | Open job closes; actual: stays open in the window | needs-repro |
| B-009 | S? | Dışa Aktar | n/a (code read, not yet run) | window export tests | Read tests/ui export tests | Default OCR path covered; actual: every test unchecks the text-layer box | needs-repro |
| B-010 | S? | Değerler | n/a (code read, not yet run) | saved template choice | Two templates, pick the second, reopen job | Saved pick restored; actual: template with most Kontrol values wins (reproduced in a scratch test) | needs-repro |
| B-011 | S? | Değerler | n/a (code read, not yet run) | unexpected read error | Make the reader raise mid-job | Finished values kept; actual: lost (cancel keeps them, error does not) | needs-repro |
| B-012 | S? | Kontrol/Değerler | n/a (code read, not yet run) | Değerlerde aç | Press it from a document in Kontrol | Document selected in Değerler; actual: document number dropped in main_window.py | needs-repro |
| B-013 | S? | Değerler | n/a (code read, not yet run) | variant drawing | Start variant drawing from Değerler | Opens the document's page; actual: page 1 | needs-repro |
| B-014 | S? | Değerler | n/a (code read, not yet run) | unread or failed documents | Job with a failed document | Visible warning; actual: Counts.unread_documents computed, never shown | needs-repro |
| B-015 | S? | Şablonlar | n/a (code read, not yet run) | Del on a variable | Select variable, press Del | Label and action agree; actual: whole variable removed, label says Kutuyu sil (undoable) | needs-repro |
| B-016 | S? | Şablonlar | n/a (code read, not yet run) | inspector box fields | Type a position beyond the sheet | Rejected or clamped; actual: box can leave the sheet | needs-repro |
| B-017 | S? | Şablonlar | n/a (code read, not yet run) | damaged template file | Put a corrupt template in the folder | Message; actual: skipped silently in window, CLI reports it | needs-repro |
| B-018 | S? | Şablonlar | n/a (code read, not yet run) | template management | Look for rename/delete/import/export/threshold in window | Available or documented; actual: missing in window, CLI only, rename nowhere | needs-repro |
| B-019 | S? | Şablonlar | n/a (code read, not yet run) | exported template | Export template, open file | No job data; actual: job name in each box example label | needs-repro |
| B-020 | S? | Kontrol | n/a (code read, not yet run) | K on first page | Press K on page 1 of a job | Clear result; actual: relabels İşin başı to Elle kesim, splits nothing (verified in core) | needs-repro |
| B-021 | S? | Kontrol | n/a (code read, not yet run) | M on QR document with hidden manual cut | Press M | Documents merge or toast is honest; actual: only QR cut removed, still split, toast says merged (verified in core) | needs-repro |
| B-022 | S? | Kontrol | n/a (code read, not yet run) | status line messages | Trigger a refusal | Cleared and announced; actual: plain label, never cleared, not announced | needs-repro |
| B-023 | S? | Kontrol | n/a (code read, not yet run) | Geri al on queued toast | Make two edits, press Geri al on the older toast | Undoes that toast's step; actual: undoes newest step | needs-repro |
| B-024 | S? | Kontrol | n/a (code read, not yet run) | failed thumbnail or page render | Corrupt a page render | Error state; actual: stays Yükleniyor, loupe blank, no message | needs-repro |
| B-025 | S? | Kontrol | n/a (code read, not yet run) | approve document | Approve a document | Rider cleared; actual: rider stays, unapprove only by undo | needs-repro |
| B-026 | S? | App | n/a (code read, not yet run) | Ctrl+F on Kontrol | Press Ctrl+F | Search; actual: opens go-to dialog | needs-repro |
| B-027 | S? | App | n/a (code read, not yet run) | Ctrl+G | Press on tabs other than Kontrol and Değerler | Same on every tab per shortcuts.md; actual: routed on two tabs only | needs-repro |
| B-028 | S? | App | n/a (code read, not yet run) | F5 | Press on Kontrol and Rehber | Refreshes or is disabled; actual: enabled, does nothing | needs-repro |
| B-029 | S? | App | n/a (code read, not yet run) | autosave failure | Make autosave fail | Visible error; actual: no try/except, Kaydedilemedi shown only after Ctrl+S | needs-repro |
| B-030 | S? | App | n/a (code read, not yet run) | error toast icon | Trigger an error toast | Error icon; actual: info icon | needs-repro |
| B-031 | S? | App | n/a (code read, not yet run) | palette placeholder | Open Ctrl+K | Placeholder true; actual: says documents are searched, only commands are | needs-repro |
