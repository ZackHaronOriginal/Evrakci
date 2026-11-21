# Findings: undo (R5c-1, 2026-11-19)

Research for ideas only. Nothing here is a decision. No code or text copied. Every claim links to a page opened with WebFetch on 2026-11-19 (summaries, paraphrased).

What we do today: one unbounded undo stack per job shared by Yükle, Kontrol, Değerler and Dışa Aktar, separate stack on Şablonlar (A-52); each step stores the whole job before and after as dicts (inventory-app-wide "Undo depth"; `ui/controller.py:_Snapshot`, `_edit`); named steps in the Düzen menu (A-53, K-119); history submenu of the last 30 (A-54); in memory only, lost on close (A-56, K-121); toasts with Geri al that act on their own step only while it is the newest, otherwise hidden (Kontrol O-06; fixed, B-023, cefd148 and faf32a5); approval is an undo step (K-59).

## Source read

- PDF Arranger `undo.py` (GPL-3.0, read only): https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/undo.py . Memento pattern: `Manager.commit(label)` runs before each action, drops the redo tail, appends a snapshot of the page list (duplicated page objects, selected indices, vertical scroll position). `undo()` first snapshots the live state when at the tip so redo can come back. No limit on states in that file. `__set_state()` restores the list, keeps zoom, marks thumbnails for re-render, restores selection and scroll. A TODO notes that showing the action name in the menu is not done.
- Qt `QUndoStack` (documentation): https://doc.qt.io/qt-6/qundostack.html

## Comparison

| Practice | Who does it (links) | What we do (ID) | Gap | Cost to us | Perf cost | Risk |
|---|---|---|---|---|---|---|
| Snapshot of the working state per step (including selection and scroll position) | PDF Arranger records selection indices and scroll position per step (https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/undo.py) | Whole-job snapshot per step; selection is restored by page id after model reset (K-38) | Check whether undo also restores scroll position and selection (unverified) | S to M | Snapshots of a 800-page job grow with step count (see below) | Memory over a long session |
| Cap on stack depth; macros count as one step | Qt `undoLimit` default unlimited, oldest dropped past the cap, macro is one command (https://doc.qt.io/qt-6/qundostack.html); PDF Arranger sets no cap in `undo.py` (link above) | No limit set, nothing capped (A-56) | A long session with full-job dicts per step may grow unbounded | S to M (set a limit or store diffs) | Memory is the cost to measure with the perf-profile skill | Dropping old steps silently breaks "never silent"; say so in the history menu |
| Merge many small commands into one step | Qt `mergeWith` and command id (https://doc.qt.io/qt-6/qundostack.html) | Each key press is one step; rotate of a selection is one step (K-42, K-119) | Pressing R four times is four steps | S | none | Low; could confuse the names |
| Menu text names the next undo and redo | Qt `undoText()`, `redoText()`, `createUndoAction` (https://doc.qt.io/qt-6/qundostack.html); PDF Arranger lists this as a TODO (link above) | Done: "Geri al: Kesim ekle" (A-53) | none (we are ahead of PDF Arranger) | none | none | none |
| Clean state marker for "saved" | Qt `setClean()`, `cleanChanged` (https://doc.qt.io/qt-6/qundostack.html) | Every edit autosaves (A-55, Y-55) | Not needed | n/a | n/a | n/a |
| Undo of an item moved to a holding place | FastRawViewer: Ctrl+Z restores the last rejected file, history length in preferences (https://www.fastrawviewer.com/howtos/sorting-photos) | Soft delete plus undo (K-43); history length not user-set | Low | none | none | none |
| Explicit "emergency exit" and redo as a heuristic | NN/g User Control and Freedom (https://www.nngroup.com/articles/ten-usability-heuristics/) | Undo, redo, toasts (K-116, A-52) | Done (B-023, cefd148, faf32a5): toast "Geri al" acts on its own step and is hidden once a newer step exists (O-06) | done | none | Medium: a wrong undo is data loss in the eyes of staff |
| Undo list persisted with the job | Not found in any source read | Lost on close (A-56) | Not a gap supported by evidence | n/a | n/a | n/a |

## Ideas for the owner's ranking

1. Selective undo: undo an older step while keeping newer ones. Problem: an older edit cannot be reverted without dropping newer ones. Gains: everyone in a long session. Evidence: NN/g heuristic 3 (link above) plus inventory. Effort M. Already done and not an idea: a toast's "Geri al" acts on its own step (B-023, cefd148 and faf32a5).
2. Measure memory of the whole-job snapshot stack on a 800-page job over hundreds of steps and decide on `undoLimit` or diffs. Problem: A-56 no limit. Evidence: Qt `undoLimit` (https://doc.qt.io/qt-6/qundostack.html); PDF Arranger leaves it unbounded (https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/undo.py), so no evidence of harm in other apps. Effort S to measure, M to change.
3. Merge repeated rotate presses of the same pages into one step (Qt `mergeWith`). Problem: R pressed three times to turn 270 degrees. Effort S.

## Unverified

- Whether undo of a Kontrol edit restores selection and scroll position in our app (K-38 covers selection by id; scroll not checked).
- Memory per snapshot in our job (not measured; no code run).
- Whether Paperless, NAPS2 or ABBYY offer undo (pages read do not say; Transact page does not mention undo, https://ephesoft.com/docs/?p=47801).
