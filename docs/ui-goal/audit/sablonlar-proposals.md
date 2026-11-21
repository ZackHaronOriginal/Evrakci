# Şablonlar audit: proposals (owner decisions)

Phase 4 Görev B. Nothing here is changed in `src/`. Reasons are measured in `sablonlar-findings.md`.

## Not done in this pass (no owner needed, but not cheap or safe)
- F-sablonlar-09 (undo merges separate edits of one box): needs `QUndoCommand.mergeWith` rules by source and time; touching the undo model risks losing steps. Option: merge only same-source edits within 1 s. Left open.
- F-sablonlar-02, 04, 05, 06, 14 to 17, 28: S3, no owner needed, left for a later pass.

## Needs the owner (look, text, shortcut, vocabulary)
- F-sablonlar-07 (B-017) wording: the message now reads "Şablon dosyası okunamadı: <id>" (the core's own phrase, shown in the left-column message). Owner may want a next step added ("Dosyayı kontrol edin veya silin").
- F-sablonlar-12 (page beyond the example's pages), 18 (raw path in read failure), 25 (template name checks), 33 (core note wording), 34 (short drag message): new Turkish text.
- F-sablonlar-20 (placeholder contrast 3.29 / 4.08), 21 (zoom buttons 24 px), 30 (green undo icons in hc): colour/size tokens of the approved look.
- F-sablonlar-26, 27, 36, 37, 38, 45: look of boxes, badges, card and draw mode.
- F-sablonlar-31, 32: vocabulary (Bölüm / Kutu / varyant; Okunmadı vs Okunamadı).
- F-sablonlar-35: the toast of "Bütün örneklerde dene" is cut: shared Toaster width; wrapping was fixed globally in 4e5d62e, re-measure first.
- F-sablonlar-39 to 44: accessibility events, box browsing keys (new shortcuts), variant origin display, rename/copy/delete of templates, per-template undo, 10 mm nudge.
- F-sablonlar-23 (rule scope), 24 (tool artefact).
