# Findings: splitting (R5c-1, 2026-11-19)

Research for ideas only. Nothing here is a decision. No code or text was copied; sources were read and paraphrased. Every claim has a link to a page that was opened with WebFetch on 2026-11-19. Caveat on method: WebFetch returns a short model-written summary of a page, not the raw page, so quotes are paraphrases and fine detail (defaults, edge cases) should be re-checked before an idea is specced. Source reads of open-source code are listed in "Source read".

What we do today (inventories): QR separator page (K-09, Y-26), "every N pages" filter on a selection (K-10, K-21 to K-30), manual cut (K-11, K-14), merge with previous (K-16, K-17), cuts survive deleting their page (K-19), empty pages never cut and an optional drop with no window control (K-20), first-page and hidden-cut oddities (Kontrol observations O-03, O-04).

## Source read

- Paperless-ngx `src/documents/barcodes.py` (GPL-3.0, read only): https://github.com/paperless-ngx/paperless-ngx/blob/dev/src/documents/barcodes.py . `get_separation_pages()` builds a map from page index to a keep/drop flag; separator barcodes follow the retain setting, ASN and tag barcodes always keep the page and never split on page 0; `separate_pages()` walks the pages, starts a new document at each split index and adds the split page only when its flag says keep; empty documents are filtered out at the end, so a dropped separator on page 1 yields no empty first document.
- PdfQRSplit (MIT): https://github.com/adlerweb/PdfQRSplit . Tiny script: one separator text, drop by default, `-k` keeps the page at the end of the previous document, `--keep-page-next` at the start of the next, `-b` brightness cut-off before barcode reading.
- scanprep (MIT): https://github.com/baltpeter/scanprep . Separator split and blank removal are two independent switches, both on by default; the page does not say how blankness is judged.

## Comparison

| Practice | Who does it (links) | What we do (ID) | Gap | Cost to us | Perf cost | Risk |
|---|---|---|---|---|---|---|
| Separator page dropped by default, with an option to keep it as first page of the next document | Paperless-ngx option `PAPERLESS_CONSUMER_BARCODE_RETAIN_SPLIT_PAGES` (https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/advanced_usage.md); PdfQRSplit keep-previous and keep-next (https://github.com/adlerweb/PdfQRSplit) | Separator is always dropped and never exported (K-09) | A sheet that carries content plus a code (a stamped cover page) cannot be used as a separator | M (core flag, export plan, Kontrol caption) | none | Changes which pages are exported; must stay visible, never silent |
| Barcode on a content page starts a document and the page is kept (serial-number style) | Paperless ASN barcodes, page kept (https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/advanced_usage.md; same rule in `get_separation_pages`, https://github.com/paperless-ngx/paperless-ngx/blob/dev/src/documents/barcodes.py) | Only the `EVRAKCI-AYIRAC` prefix splits (Y-26); other QR text is ignored | Cannot split on a pre-printed form number | M to L (analysis stores QR text per page, new cut kind) | Analysis already decodes QR; cost is storing text | New cut kind needs icon, tab shape and word (K-13 rule: not colour alone) |
| Value mask and minimum length on separator codes, so only matching codes split | Kodak Capture Pro barcode zones: mask and minimum length (https://resources.kodakalaris.com/support/Capture%20Pro%20Help/Content/Separating_documents_with_bar_code_zones.htm) | Prefix test only (Y-26) | A stray QR on a page (a delivery sticker) is not a split | S | none | Low; our prefix is already a mask |
| Split when the barcode value changes, not at a sheet | DocuWare splits when the barcode value changes (https://knowledgecenter.docuware.com/docs/processing-documents) | Not offered | Pre-numbered forms where every page carries the document number cannot be split without a separator sheet | M | none | Needs per-page text (see QR text above) |
| Fixed page count (our filter) | DocuWare page count (https://knowledgecenter.docuware.com/docs/processing-documents); PDF-XChange split every n pages (https://help.pdf-xchange.com/pdfxt11/splitting-pages.html) | Filter N on a selection (K-10, K-21, K-22), leftover flag (K-24) | None for the basic case. We are ahead on non-contiguous selection (K-23); no source found for that | none | none | none |
| Split by maximum file size | PDF-XChange (https://help.pdf-xchange.com/pdfxt11/splitting-pages.html) | Not offered | Email attachment limits apply to exported files, not to our split | L, and the owner defines documents by content, not size | Needs size estimate per document | Conflicts with PRODUCT.md rule that staff define document content; likely not wanted |
| Split by text criterion (needs a sample document) | DocuWare text criteria (https://knowledgecenter.docuware.com/docs/processing-documents) | Not offered (OCR text per page is not available before Değerler; feature-ideas item 5) | Staff cannot cut at "page that says Kapasite Raporu" | L | OCR over 800 pages, offline | Wrong cuts if OCR misreads; needs the confirm step |
| Separator and blank removal as independent switches | scanprep, both default on (https://github.com/baltpeter/scanprep) | Drop-empty is a core option with no window control (K-20, O-02) | Staff cannot turn blank dropping on or restore an empty page in the window | S (a toggle and a restore command exist in core/CLI) | none | Low; wording must say what is dropped |
| Empty documents never created by a dropped first page | Paperless `separate_pages()` filters empty documents (https://github.com/paperless-ngx/paperless-ngx/blob/dev/src/documents/barcodes.py) | Not checked in code by this agent (unverified; see K-09, K-12 for the documented behaviour) | Unknown | none | none | none |
| Merge two documents, split one into two, with a choice of what the new document keeps | Tungsten Transact Validate: merge selected, split a document in two, and choose whether the new one keeps index fields, table data, both or neither (https://ephesoft.com/docs/?p=47801) | Merge (M) and cut (K) exist; values stay with pages by id (inventory-degerler) | The "what happens to values after a cut or merge" is not explained at the moment of the edit | S (a line in the toast) | none | Low |

## Ideas for the owner's ranking

1. Say what happens to the separator and to values at the moment of a cut or merge. Problem: after M or K staff cannot tell whether typed values moved. Gains: every reviewer. Evidence: Transact asks what the new document keeps before it splits (https://ephesoft.com/docs/?p=47801). Effort S.
2. Window control for "drop empty pages" plus "restore this page". Problem: blank backs of double-sided sheets stay unless the CLI is used. Gains: offices that scan duplex. Evidence: scanprep treats blank removal as its own default-on switch (https://github.com/baltpeter/scanprep); our gap is K-20 and O-02. Effort S.
3. Split on any QR or barcode value with a prefix or mask the owner sets (not only `EVRAKCI-AYIRAC`). Problem: pre-printed forms. Gains: chambers with numbered forms. Evidence: Kodak mask and minimum length (https://resources.kodakalaris.com/support/Capture%20Pro%20Help/Content/Separating_documents_with_bar_code_zones.htm); DocuWare value change (https://knowledgecenter.docuware.com/docs/processing-documents). Effort M.
4. Option "keep the separator page as the first page of the next document". Problem: content-bearing sheets. Evidence: Paperless retain option and PdfQRSplit `--keep-page-next` (links above). Effort M.
5. Later (not gaps): none of the deferred items (first-run tour, completion sound, invert selection) belong to this area.

## Unverified

- Whether Paperless or Kodak show a preview of the split before it is applied (not in the pages read). DocuWare page says nothing on preview (https://knowledgecenter.docuware.com/docs/processing-documents).
- How scanprep judges a blank page (page gives no criteria).
- Defaults of Paperless barcode DPI and upscale settings (not on the page read).
- Patch-T batch versus document separators in Tungsten Capture: seen only in competitors.md, not reopened by this agent.
- Everything fetched came through a summarising fetch tool; line-level source detail in `barcodes.py` was not read verbatim.
