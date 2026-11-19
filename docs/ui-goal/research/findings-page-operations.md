# Findings: page operations (R5c-1, 2026-11-19)

Research for ideas only. Nothing here is a decision. No code or text copied. Every claim links to a page opened with WebFetch on 2026-11-19 (summaries, paraphrased).

What we do today: rotate right/left per page, one undo step per selection (K-42); soft delete with restore, never confirmed (K-43 to K-47); apply template to selection (K-48 to K-52); no reorder or move of pages in Kontrol (K-53); batch reorder, remove and rename in Yükle (Y-14 to Y-17); separators cannot be deleted (K-47); duplicate checks absent (Yükle observation 7).

## Source read

- PDF Arranger (GPL-3.0, read only): https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/pdfarranger.py . Read about the first 1000 of 3436 lines. Actions `delete`, `rotate` (integer argument) and `reverse_order`, `swap_odd_even` are wired to handlers; the handler bodies were not in the excerpt. Reordering uses `self.model.reorder(...)` with a position map (seen in `split_booklet`). Every change calls `commit(label)` first (see undo findings).
- User manual: https://github.com/pdfarranger/pdfarranger/wiki/User-Manual

## Comparison

| Practice | Who does it (links) | What we do (ID) | Gap | Cost to us | Perf cost | Risk |
|---|---|---|---|---|---|---|
| Rotate in 90 degree steps on a selection | PDF Arranger (https://github.com/pdfarranger/pdfarranger/wiki/User-Manual) | Same (K-42) | none | none | none | none |
| Delete that can be reversed (move to a holding place, restore by undo) | FastRawViewer moves rejects to a `_Rejected` folder and Ctrl+Z restores (https://www.fastrawviewer.com/howtos/sorting-photos) | Soft delete, dimmed, restore by Del or Geri al (K-43, K-44) | none; our model matches | none | none | none |
| Reorder pages by drag, or by copy and paste | PDF Arranger (https://github.com/pdfarranger/pdfarranger/wiki/User-Manual); Transact page view opened with Ctrl+Shift+O, drag to reorder (https://ephesoft.com/docs/?p=47801) | Not possible in Kontrol; only whole batches (K-53, Y-14) | A page scanned out of order (back before front) needs a rescan or a new batch | L (page order is derived from batch order in the core; a per-job page order is a model change) | Reorder invalidates thumbnails only by id | High: page numbers are shown everywhere (Y-13); must stay explainable |
| Reverse order, swap odd/even | PDF Arranger actions `reverse_order`, `swap_odd_even` (https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/pdfarranger.py) | None | Feeders that scan stacks upside down give reversed order | M (needs reorder first) | none | Same as reorder |
| Insert blank page, duplicate page | PDF Arranger (https://github.com/pdfarranger/pdfarranger/wiki/User-Manual) | None | We do not need blank pages; duplicates not requested | n/a | n/a | PRODUCT.md: no extra paper work, likely not wanted |
| Crop white borders automatically; manual crop with drag markers | PDF Arranger (https://github.com/pdfarranger/pdfarranger/wiki/User-Manual) | None; our export is page images as scanned | Not an Evrakçı goal as far as inventories show | n/a | n/a | Out of scope |
| Merge and split documents, with the new document's index fields kept or cleared | Transact (https://ephesoft.com/docs/?p=47801) | Merge (M) / cut (K) (K-14 to K-17) | See splitting findings idea 1 | S | none | Low |
| Page list reorder in a separate page view panel | Transact Ctrl+Shift+O (https://ephesoft.com/docs/?p=47801) | Loupe (Space) is a viewer only (K-91) | None unless reorder is wanted | M if reorder exists | none | none |
| Pages sent out for correction: "postpone" without deciding | ABBYY Ctrl+Enter postpones a field (https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work) | Enter approves; no "come back to this" mark on a document or page | Staff who are unsure leave it unapproved, which looks the same as not seen | S to M | none | Must not become a second status vocabulary beside İncelendi |
| Rotate also changes what OCR sees | Not examined by this agent | `Döndür` drops thumbnails (K-42) | unknown | n/a | n/a | Unverified |

## Ideas for the owner's ranking

1. A page-level "move page" command (cut and paste to another position, or to the end of the document). Problem: pages scanned in the wrong order. Gains: offices with feeder jams. Evidence: PDF Arranger drag and paste, Transact page view (links above). Effort L, risky; list it as a research item for the owner, not a recommendation.
2. A "come back later" mark on a document (postpone) separate from İncelendi. Problem: reviewers unsure about a document cannot park it. Evidence: ABBYY postpone (https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work). Effort S to M.
3. Restore-empty-page and remove-template commands already in core/CLI but not in the window (K-20, K-52). Problem: internal gap. Evidence: inventory, no external source. Effort S.

## Unverified

- Bodies of PDF Arranger delete, rotate and reorder handlers (not in the excerpt read).
- Whether any shortlist app prevents deleting the last page of a document or warns (not in pages read).
- NAPS2 page-list features: README and a docs URL gave nothing usable (https://github.com/cyanfish/naps2; https://www.naps2.com/doc/ returned 404).
