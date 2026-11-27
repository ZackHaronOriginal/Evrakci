# Findings: selection (R5c-1, 2026-11-19)

Research for ideas only. Nothing here is a decision. No code or text copied. Every claim links to a page opened with WebFetch on 2026-11-19 (summaries, paraphrased).

What we do today: click, Shift+click, Ctrl+click (K-31), rubber band (K-32), Ctrl+A (K-33), Esc clears (K-34), Shift+arrows from the Qt default (K-35), current page acts as selection (K-36), selection card counts drawn selection only (K-37), selection survives edits by page id (K-38), right-click selects first (K-39), 2 px ring plus check badge (K-40). Non-contiguous selection by keyboard is not an app shortcut and Ctrl+Space was not checked (K-41). Invert selection is deferred ("later").

## Source read

- Qt `QAbstractItemView` selection modes (our toolkit, documentation): https://doc.qt.io/qt-6/qabstractitemview.html . ExtendedSelection: plain click replaces, Ctrl+click toggles, Shift+click ranges, drag selects several; the page states Ctrl+Space toggles the current item. Only the first 100000 characters were read.
- PDF Arranger user manual (GPL-3.0 app, wiki page): https://github.com/pdfarranger/pdfarranger/wiki/User-Manual . Source: https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/pdfarranger.py read to roughly line 1000 of 3436 (icon view in MULTIPLE mode, `iv_selection_changed` refreshes action states; select-all and odd/even bodies were not visible).

## Comparison

| Practice | Who does it (links) | What we do (ID) | Gap | Cost to us | Perf cost | Risk |
|---|---|---|---|---|---|---|
| Ctrl+Space toggles the focused item | Qt documents it for item views (https://doc.qt.io/qt-6/qabstractitemview.html); WAI-ARIA listbox pattern lists Space or Ctrl+Space toggle (https://www.w3.org/WAI/ARIA/apg/patterns/listbox/) | Unclear whether it works on our timeline (K-41) | Keyboard-only users cannot pick non-adjacent pages if it does not | S (check, then a test) | none | Low |
| Shift+Space range from last selected; Ctrl+Shift+Home/End to the ends | ARIA listbox pattern, marked optional (https://www.w3.org/WAI/ARIA/apg/patterns/listbox/) | Shift+arrows only (K-35) | No "select to document start/end" | S to M | none | Must not clash with Ctrl+Left/Right document jumps (K-69); run shortcut-audit |
| Select all, deselect all with a separate key | PDF Arranger Ctrl+A and Ctrl+Shift+A (https://github.com/pdfarranger/pdfarranger/wiki/User-Manual) | Ctrl+A, Esc (K-33, K-34) | None | none | none | none |
| Select odd, even, same file, same format, invert | PDF Arranger selection menu (https://github.com/pdfarranger/pdfarranger/wiki/User-Manual) | None. Invert is deferred ("later") | Odd/even helps duplex piles; "same batch file" fits our batches | M | none | Low; show count of matches |
| Select-and-advance in one key | FastRawViewer: toggle current and move on with Ctrl+. or Shift+Right (https://www.fastrawviewer.com/howtos/sorting-photos) | Shift+arrows extend, no toggle-and-advance | Marking scattered pages while walking is two keys per page | S | none | Overlaps K / Del which act on current page (K-36) |
| Hover checkbox in the thumbnail corner | FastRawViewer (https://www.fastrawviewer.com/howtos/sorting-photos) | Check badge appears on selected only (K-40) | Mouse users without Ctrl know no way to multi-select | S to M | paint only | Hover is mouse only; keep keyboard path |
| Multi-select documents with a modifier in a left list | Transact Validate: Alt selects several documents, grey when selected (https://ephesoft.com/docs/?p=47801) | Selection is pages, not documents; merge acts on the current document (K-16) | No "select whole document" | S ("select this document") | none | Low |
| Separate active item from selected items visually | FastRawViewer distinguishes active and selected (https://www.fastrawviewer.com/howtos/sorting-photos); we have a focus ring and a selection ring (K-40) | Done | none | none | none | none |

## Ideas for the owner's ranking

1. Check and document Ctrl+Space (toggle focused page) and add a test. Problem: K-41 unknown. Gains: keyboard-only staff. Evidence: Qt and ARIA pages above. Effort S.
2. "Select this document" (all pages of the current document). Problem: filter and template need a selection; today staff drag. Evidence: Transact multi-select (https://ephesoft.com/docs/?p=47801), PDF Arranger "same file" (https://github.com/pdfarranger/pdfarranger/wiki/User-Manual). Effort S.
3. Select odd or even pages in the selection or document. Problem: duplex piles where backs are blank. Evidence: PDF Arranger (link above). Effort M.

## Unverified

- Whether PDF Arranger's code does select-all or odd/even by index (source lines not read).
- Ctrl+Space on our timeline (K-41).
- Qt documentation was read only up to 100000 characters.
