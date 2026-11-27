# Findings: printing (5c, R5c-3)

Researched 2026-11-19 at commit 89c4844. Ideas only, nothing decided. "We do" cites [inventory-disa-aktar.md](inventory-disa-aktar.md) (D-xx) and the code. External claims link to pages that were opened.

## What we do
Only one print path exists: "Dizini yazdır…" (Ctrl+P) on Dışa Aktar prints the file list as an HTML table through `QTextDocument` and the system print dialog (D-53; `ui/disa_aktar.py:index_html`, `print_index`). All rows are printed, not the filtered view. Columns: Durum, Dosya adı, Sayfalar (a range, Obs. 2), Şablon, Not. No print preview. No document number, no date or time on the sheet (Obs. 10). The header is a plain `<tr>` of `<th>`, not a `<thead>`. Kontrol, Değerler and Rehber have no print command in the inventory (grep of the inventories for "print" finds only D-53). Printing separator sheets is outside this inventory (unverified whether the app offers one).

## Comparison table

| Practice | Who does it (opened links) | What we do | Gap | Cost to us | Perf cost | Risk |
|---|---|---|---|---|---|---|
| Preview before paper | Qt provides `QPrintPreviewDialog`; one drawing slot serves preview and print ([Qt docs](https://doc.qt.io/qt-6/qprintpreviewdialog.html)) | System print dialog only (D-53) | No preview; a 100-row list wastes paper if the wrong columns print | S to M (the document is already a `QTextDocument`; a preview needs a paint slot) | low | Preview dialog is not tested on real hardware (Obs. 15) |
| Table header repeated on every page | Qt recognises `thead` and uses it when a printed table spans pages ([Qt HTML subset](https://doc.qt.io/qt-6/richtext-html-subset.html)) | Header row is a plain row, so it likely appears on page 1 only (by code reading plus the Qt page; not printed) | Long lists lose their header on page 2+ | S | none | Untested on a printer |
| Page numbers and margins | `QTextDocument.print` with no fixed page size makes a temporary copy, adds a 2 cm margin and a page number at the bottom ([Qt docs](https://doc.qt.io/qt-6/qtextdocument.html)) | No page size is set in our code (read in `print_index`), so these defaults apply (by reading; not printed) | No job name, date or "page n of m" under our own control | S | none | none |
| Forced page breaks | `page-break-before` and `page-break-after` supported in the Qt subset ([Qt HTML subset](https://doc.qt.io/qt-6/richtext-html-subset.html)) | Not used | Only needed for a multi-section sheet | S | none | none |
| Printed reports carry date and page number | Kofax Capture Batch Summary report: selected date range, totals row, footer with page number and generation time ([Tungsten docs](https://docshield.tungstenautomation.com/KC/en_US/11.1.0-40hy9nfk91/help/main/KC_reportviewer/c_batchsummaryreport.html)) | No date, no totals line beyond "N belge, M sayfa" | A paper index cannot be dated or matched to a folder later | S | none | none |
| Printed audit of what was exported | Kofax document audit records each export per document ([manual](https://www.manualsdir.com/manuals/658182/kofax-capture.html?page=8)); that page does not say if it prints | Printed index lists planned names, not an export record (works before writing too, D-53) | After writing, the sheet does not say "written at 14:32 to folder X" | S | none | Printing the plan vs the result needs a clear title |
| Print a selection or only Kontrol rows | Not found in any opened page | All rows, even when the list is filtered (D-53) | Unverified whether staff want it | S | none | none |

## Ideas for the owner's ranking
1. **Header row repeated and page footer with date, job name.** Problem: multi-page index loses its header; no date on paper. Who gains: staff filing the printed list. Evidence: [Qt HTML subset](https://doc.qt.io/qt-6/richtext-html-subset.html), [Kofax report footer](https://docshield.tungstenautomation.com/KC/en_US/11.1.0-40hy9nfk91/help/main/KC_reportviewer/c_batchsummaryreport.html). Effort S.
2. **Print preview.** Problem: no look before paper. Evidence: [Qt](https://doc.qt.io/qt-6/qprintpreviewdialog.html). Effort S to M.
3. **Document number column in the printed list** (links to `belge_NNN` and to the sheet). Problem: Obs. 10. Evidence: same inventory. Effort S.

## Unverified
- No printer was used; header repetition, margins and page numbers come from Qt docs plus code reading.
- PaperStream, Capture Pro, ABBYY and Acrobat printing of batch or document lists: not found or pages not opened. A search for capture-software batch reports returned only Kofax material.
- Whether Kofax reports can be printed or exported: the opened pages do not say.
