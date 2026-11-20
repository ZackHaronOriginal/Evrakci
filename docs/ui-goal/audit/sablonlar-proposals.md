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

## Action paths: keys with no mouse path (2026-11-20, `audit_shortcuts.py --paths`)
Four Şablonlar commands are reachable only by key. Each needs a new label or a new control, so none is changed in `src/`:
- `sablonlar.kaydir` (arrows) and `sablonlar.kaydir_1mm` (Shift+arrows): nudge the selected box by 0,25 mm / 1 mm. The registry label has no direction, so one menu entry cannot say which way to move. Options: (a) four menu entries per size ("Kutuyu sola kaydır"...), new Turkish text; (b) a "Konum" group of four arrow buttons in the box inspector, a look change; (c) the box's X/Y fields in the inspector already set a position exactly: owner decides whether that counts as the mouse path for fine moves.
- `local.kutu_boyutu` (Ctrl+arrows, `sablon_canvas.py`): resize the selected box by 0,25 mm / 1 mm; same options, plus the inspector's W/H fields.
- `local.kutu_yerlestir` (Enter while "Kutu çiz" is on): places a 40 x 10 mm box. Needs a visible "Kutu yerleştir" command or a click on the sheet that does the same, i.e. new text or a behaviour change.
The matching strict xfails in `tests/test_action_paths.py` (`KEY_ONLY`) stay until the owner picks an option.
