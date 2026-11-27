# Competitor and reference research (ideas only)

Researched 2026-11-19. Scope: Evrakçı tabs Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber.

## Header: how to use this file

- This is research for ideas only. Do NOT copy code, text, icons, layouts pixel-for-pixel or strings from any project listed here into the Evrakçı repo. Several are GPL, AGPL or LGPL, some need a CLA to contribute, and commercial products are proprietary. Reading a source file to understand an approach is fine; transcribing it is not. If a design idea is adopted, re-derive it in our own words and code.
- Nothing was cloned. Nothing was installed.
- Second pass 2026-11-19: every entry's link was opened again (except those listed under "Not reopened in the second pass"); corrections are marked "[corrected]", new entries "[new]".
- Method: every fact below comes from a page opened with WebFetch, and the URL is given next to it. Facts that appeared only in a web search result snippet (not an opened page) are marked "(search snippet only)". Anything not seen is marked "unverified".
- Date caveat: GitHub release pages as fetched show day and month but often not the year. Where the year was not shown it is written "year not shown". The page footer said 2026, but that is the site's copyright, so it was not used as proof.
- Many GitHub fetches reported an empty "Releases" section on the repo front page. Release data therefore comes from each repo's `/releases` page where fetched.
- Several sites returned 403 to the fetch tool (docs.paperless-ngx.com, helpx.adobe.com split page and Action Wizard page, docs.mayan-edms.com). Those facts are unverified or taken from other opened pages.

Tab legend: Y = Yükle, K = Kontrol, Ş = Şablonlar, D = Değerler, X = Dışa Aktar, R = Rehber.

---

## Group 1: Open source

### 1.1 Paperless-ngx
- Link: https://github.com/paperless-ngx/paperless-ngx
- Licence: GPL-3.0 (https://github.com/paperless-ngx/paperless-ngx)
- Platform: Docker-first (compose); other install methods exist in docs (same URL). Server plus web UI, not a desktop app.
- Relevant: barcode splitting at ingest. Barcodes work on PDF, and TIFF if an option is on; QR Code, Code 128, Data Matrix listed; only content matters, not type. Separator pages are discarded by default ("dedicated separator sheets such as PATCH-T pages"); a retain option keeps the separator as first page of the next document. ASN barcodes: "Each detected ASN barcode starts a new document" and the page is kept, so an ASN label can sit on a content page. Tag barcodes can also split and assign tags. (https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/advanced_usage.md)
- Informs: Y, K, R (separator vs "barcode on content page" semantics, retain-separator option, explaining it in the guide).
- Maturity: latest release v3.5.1, published 18 November, year not shown (https://github.com/paperless-ngx/paperless-ngx/releases and https://github.com/paperless-ngx/paperless-ngx/releases/tag/v3.5.1).
- Inspect: source on GitHub (GPL-3.0, read only); demo not checked (unverified). Repo front page showed an empty Releases section when reopened; the v3.5.1 release page shows "18 Nov" without a year.

### 1.2 NAPS2
- Link: https://github.com/cyanfish/naps2
- Licence: GPL 2.0 or later; NAPS2.Escl.*, NAPS2.Images.*, NAPS2.Internals, NAPS2.Sdk under LGPL 2.1 or later; NAPS2.Sdk.Samples MIT (https://github.com/cyanfish/naps2)
- Platform: Windows 7+ (x64, x86), macOS 10.15+, Linux x64/arm64 (GTK 3.20+). Scanner drivers: WIA, TWAIN, SANE, ESCL. (same URL)
- Relevant: scan-then-organize page list with Tesseract OCR, PDF/TIFF/JPEG/PNG output (same URL). Home page adds automatic deskew, manual duplex, crop/brightness/contrast, OCR in 100+ languages and a command-line interface (https://www.naps2.com/). Neither the repo page nor the home page mentions barcode, patch-T or blank-page detection; treat as unsupported-until-shown (unverified). [corrected]
- Informs: Y (scanner acquisition, page list handling), X.
- Maturity: 8.6.1 marked Latest, 19 November 2026 per asset timestamps; 9.0b1 pre-release the same day (https://github.com/cyanfish/naps2/releases). Very active.
- Inspect: free, source on GitHub. Best desktop reference for scan UX on Windows.

### 1.3 scanprep
- Link: https://github.com/baltpeter/scanprep
- Licence: MIT (https://github.com/baltpeter/scanprep)
- Platform: Python CLI (PyPI, Snap, source); needs zbar (same URL).
- Relevant: splits a batch-scanned PDF at pages carrying a barcode with text `SCANPREP_SEP`, also removes blank pages (both on by default, each can be turned off). Ships a printable separator PDF. Output named `0-<file>.pdf`, `1-<file>.pdf`. (same URL)
- Informs: Y, R (the minimal "separator plus blank removal" contract).
- Maturity: unverified; the commits page showed no history (https://github.com/baltpeter/scanprep/commits/main). Splitting and blank removal can each be turned off (`--no-page-separation`, `--no-blank-removal`); any barcode type zbar reads works (https://github.com/baltpeter/scanprep).
- Inspect: source, small enough to read in minutes.

### 1.4 PdfQRSplit
- Link: https://github.com/adlerweb/PdfQRSplit
- Licence: MIT (https://github.com/adlerweb/PdfQRSplit)
- Platform: Python script using zxing, pypdf4, pillow (same URL).
- Relevant: scans each page for a barcode; default separator text `ADAR-NEXTDOC` (changeable). `-k` keeps the separator in the previous document, `--keep-page-next` in the next one; the README does not state the default when neither is given [corrected: draft said "dropped by default"]. `-b` sets the brightness threshold used before reading (default 128). (same URL)
- Informs: Y, Kontrol options for where the separator page goes.
- Maturity: unverified; 15 commits shown, no dates.
- Inspect: source, tiny.

### 1.5 PDF Arranger
- Link: https://github.com/pdfarranger/pdfarranger
- Licence: GPL-3.0 (https://github.com/pdfarranger/pdfarranger)
- Platform: Linux, Windows, macOS, FreeBSD (Python GTK) (same URL).
- Relevant: merge, split, rotate, crop, rearrange pages in a GUI (README). The User Manual (https://github.com/pdfarranger/pdfarranger/wiki/User-Manual) confirms: pages shown side by side, reorder by drag or copy/paste, selection by all/odd/even/range/inverted/same-file, Shift-click range, Ctrl+A / Ctrl+Shift+A, undo and redo, 90-degree rotation, automatic white-border crop and drag-marker crop. Backend pikepdf. [corrected]
- Informs: K (page strip editing, selection variants, undo), and a candidate for a source read (selection and undo).
- Maturity: 1.14.0 published 23 May, year not shown (https://github.com/pdfarranger/pdfarranger/releases).
- Inspect: free, source.

### 1.6 PDFsam Basic
- Link: https://github.com/torakiki/pdfsam
- Licence: AGPL, since version 3 (earlier GPLv2) (https://github.com/torakiki/pdfsam)
- Platform: "multi-platform", JavaFX; v4+ bundles its own JDK (same URL).
- Relevant: extract, split, merge, mix, rotate PDFs. Split methods (https://pdfsam.org/pdf-split/): by page numbers (every page, even/odd, custom list, every n), by size, by bookmarks with optional regex; the paid-or-separate "Visual" edition adds split on text change at a position. [corrected]
- Informs: X (split and merge options vocabulary).
- Maturity: v6.0.10 published 4 November, 2026 per asset timestamps (https://github.com/torakiki/pdfsam/releases).
- Inspect: free, source. AGPL: read only.

### 1.7 OCRmyPDF
- Link: https://github.com/ocrmypdf/OCRmyPDF
- Licence: MPL-2.0; some non-core parts MIT; docs and tests CC-BY-SA 4.0 (https://github.com/ocrmypdf/OCRmyPDF)
- Platform: Linux, Windows, macOS, FreeBSD; Docker images x64/ARM (same URL).
- Relevant: adds a Tesseract text layer under the image, produces PDF/A by default (`--output-type pdfa` to require), `--deskew`, image clean-up before OCR, 100+ languages (same URL). This is our PDF/A with text layer target.
- Informs: X.
- Maturity: v17.14.2 published 16 Nov, year not shown (https://github.com/ocrmypdf/OCRmyPDF/releases). Active.
- Inspect: free, source. MPL-2.0 is file-level copyleft; still do not copy.

### 1.8 invoice2data
- Link: https://github.com/invoice-x/invoice2data
- Licence: MIT (https://github.com/invoice-x/invoice2data)
- Platform: Python CLI and library.
- Relevant: YAML/JSON templates, regex per field (several regexes allowed), static and custom fields, currency, `replace:` clean-up, line items, `--new-template` guesses a template from a sample, optional OCR backends, can rename PDFs from content; default text backend pdfium (same URL). Regex based, not coordinate zones.
- Informs: Ş, D (template file format, per-field clean-up rules, rename by content).
- Maturity: unverified; no dates on the page.
- Inspect: source.

### 1.9 ScanTailor Advanced
- Link: https://github.com/4lex4/scantailor-advanced (the `ScanTailor/scantailor-advanced` URL returned 404)
- Licence: GPL-3.0 (https://github.com/4lex4/scantailor-advanced)
- Platform: not stated on the page.
- Relevant: multi-column thumbnails, page-selection shortcuts, Ctrl+G go-to-page, picture zones, margins/alignment, light and dark colour schemes, multi-threaded batch processing, default parameter profiles (same URL) [corrected]. The earlier claim about deskew deviation highlighting is not on the opened page: unverified.
- Informs: K, Y.
- Maturity: unverified; Releases section empty, 512 commits. Version v1.0.16 seen only in a search snippet.
- Inspect: free, source.

### 1.10 Mayan EDMS
- Link: https://gitlab.com/mayan-edms/mayan-edms (the GitHub mirror says it is no longer maintained and very outdated: https://github.com/mayan-edms/mayan-edms)
- Licence: GPL-2.0 (https://gitlab.com/mayan-edms/mayan-edms/-/raw/master/LICENSE) [corrected]. The "GitHub mirror no longer maintained" remark was not reopened.
- Platform: Docker Compose deployment; Python/Django (GitHub mirror page).
- Relevant: "Free Open Source DMS" with topics OCR, PDF, indexing, workflow (https://gitlab.com/mayan-edms/mayan-edms). Detailed feature docs not read (docs.mayan-edms.com returned 403).
- Informs: R (document lifecycle ideas only). Low priority.
- Maturity: unverified; GitLab page shows 2 tags, no names.

### Also checked (lower priority)

| Name, link | Licence | What | Tabs | Notes |
|---|---|---|---|---|
| Docspell, https://github.com/eikek/docspell | AGPL-3.0 or later | Personal DMS; imports from scanners, email; OCR; tags with ML suggestions. Splitting not mentioned. | R | v0.43.0 "Latest", 15 Mar, year not shown (https://github.com/eikek/docspell/releases) |
| Teedy, https://github.com/sismics/docs | GPL-2.0 | Lightweight DMS: OCR, workflow, versioning, inbox scanning, tested with 1M documents | R | v1.11, 12 March, year not shown (https://github.com/sismics/docs/releases) |
| OpenKM CE, https://github.com/openkm/document-management-system | GPL-2.0 up to 6.x; v7.0+ binary only; repo archived 10 March 2026 | DMS | none | Not worth studying (same URL) |
| pdf-scan-splitter, https://github.com/kduma-OSS/CLI-pdf-scan-splitter | not stated | Splits every page to its own PDF, names by first Code-128 barcode, `UNKNOWN.pdf` otherwise; runs in Docker with zbar | Y | Last commit 16 December 2022 (https://github.com/kduma-OSS/CLI-pdf-scan-splitter/commits). Rename-by-barcode idea only |
| ZBar, https://github.com/mchehab/zbar | LGPL-2.1 | Barcode reader suite; EAN, Code 128/39/93, Codabar, ITF, QR, SQ | Y | Release date unverified (https://github.com/mchehab/zbar) |
| zxing-cpp, https://github.com/zxing-cpp/zxing-cpp | Apache-2.0 | Barcode read/write, QR, Data Matrix, Aztec, PDF417, Code 128; Python wrapper exists | Y | Release date unverified (https://github.com/zxing-cpp/zxing-cpp) |
| Tesseract, https://github.com/tesseract-ocr/tesseract | Apache-2.0 (Leptonica BSD-2) | OCR engine, 100+ languages; `--psm` page segmentation option exists; Turkish not named on the page, tessdata_fast (Apache-2.0, https://github.com/tesseract-ocr/tessdata_fast) file list was cut before `tur`, so Turkish data is unverified | Ş, D | Major 5 current stable, 5.0.0 on 30 Nov 2021 (https://github.com/tesseract-ocr/tesseract) [corrected] |

| [new] Stirling-PDF, https://github.com/Stirling-Tools/Stirling-PDF | MIT with exceptions: `app/proprietary`, `app/saas`, `engine`, several `frontend/src/editor/*` and `frontend/src/processor` carry their own licences (https://raw.githubusercontent.com/Stirling-Tools/Stirling-PDF/main/LICENSE) | Open-core PDF toolbox, 50+ tools, split and OCR listed, desktop client, browser UI, Docker server; split options and auto-split not described on the page | X, K | Source inspectable for the MIT parts; check each directory's licence before reading |
| [new] Label Studio, https://github.com/HumanSignal/label-studio | Apache-2.0 | Multi-user annotation tool with a data manager, bounding boxes on images, pre-labelling from model predictions; page mentions no keyboard hotkeys and no OCR | Ş, D (box drawing and review pattern only) | Source inspectable |

Zonal OCR: a search for open-source coordinate-zone template tools found only invoice2data (keyword based) and DIY Tesseract cropping (search snippet only, https://github.com/invoice-x/invoice2data). No mature open-source "draw zones on a sample page" product was found. That gap is the argument for studying the commercial zone editors below.

---

## Group 2: Commercial capture and batch scanning

### 2.1 ABBYY FlexiCapture
- Link: https://www.abbyy.com/flexicapture/
- Licence: proprietary. Platform: on-prem or cloud; HTML5 web stations in Chrome, Firefox, Edge; SDK; mobile (same URL).
- Relevant: capture, classify, extract, validate. Field verification docs: fields reviewed one at a time, Enter confirms, Ctrl+Enter postpones (marks unverified), Ctrl+Up/Down moves between processed fields, Ctrl+Alt+I shows the page image for the field with a zoom list, Ctrl+Alt+F shows the same field in analogous documents. (https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work)
- Informs: D, K.
- Maturity: unverified. Trial: the page offers a demo request, no free trial; on-prem, cloud or SDK; languages not listed on the page (https://www.abbyy.com/flexicapture/) [corrected]. Shortcut table re-confirmed on the docs page.

### 2.2 Tungsten Capture (formerly Kofax Capture)
- Link: https://docshield.tungstenautomation.com/KC/en_US/11.1.0-40hy9nfk91/help/main/KC_administration/c_batchseppatchcode.html
- Licence: proprietary. Platform: Windows (unverified from opened pages).
- Relevant: a reserved patch code type closes the current batch and opens a new one; the barcode on the separator sheet picks the batch class; a code reserved for batch separation cannot also be used for document separation; Separator Sheet Utility prints the sheets (same URL). Rubber Band OCR in validation fills index fields from drawn zones (search snippet only). The opened page does not explain document-level separation by patch code.
- Informs: Y, Ş, R (batch level versus document level separators).
- Maturity: documentation 11.1 and 11.2 seen in search; current version unverified. Trial: unverified.

### 2.3 Tungsten (Ephesoft) Transact
- Link: https://ephesoft.com/docs/?p=47801 and https://docshield.tungstenautomation.com/Transact/en_US/2023.1.00-oismpn77w5/help/User/Transact_Help/operatorrolesfeatures/c_validateuserinterface.html
- Licence: proprietary.
- Relevant: Validate screen has three panels: documents and pages (red/green status per document, Alt multi-select), extracted index fields, and image preview. Fields turn red when the field is not found, below OCR confidence threshold, or fails its validation pattern; a red field must be dealt with before the Validate button approves and advances. Group tabs show a green circle or a red exclamation mark. Toolbar has Merge, Split, Table. Ctrl+Shift+O opens a page view for reordering pages. Merge (Alt multi-select or via a drop-down) and Split (choose whether fields/tables carry to the new document). Right panel: image preview with zoom, rotation, image/OCR toggle. (https://ephesoft.com/docs/?p=47801; the last ~6k characters of the page were not read)
- Informs: D, K (the reasons a field needs attention, tab-level status marks).
- Maturity and trial: unverified.

### 2.4 Hyland OnBase Advanced Capture and Brainware
- Links: https://www.hyland.com/en/products/brainware and https://docs.hyland.com/r/OnBase/Advanced-Capture/Foundation-23.1/Advanced-Capture/Configuration/Configuring-Advanced-Capture/Configuring-Advanced-Capture-Forms/Configuring-A-Data-Field-Zone
- Licence: proprietary.
- Relevant: OnBase data field zones are drawn by dragging a box on the document; the dialog has tabs by data type (Text Field, Line Item, Grouped Line Item, Optical Mark, Signature Detection); the drawn box appears in a Result Verification panel; after save, keyword zones show green and snippet zones hatched red in the viewer, and the form must still be saved to the database with Save Configuration. [corrected] Brainware is mostly template-less, routes exceptions to a customizable verification screen and learns from corrections; page mentions no free trial, demo by request (https://www.hyland.com/en/products/brainware).
- Informs: Ş (draw-a-box zone editor with typed fields), D.
- Maturity and trial: unverified.

### 2.5 DocuWare
- Link: https://knowledgecenter.docuware.com/docs/processing-documents
- Licence: proprietary.
- Relevant: splitting by fixed page count, by text criteria (needs a sample document), or when a barcode value changes. Indexing readout areas: text before/after/between a string, field delimiters, a "Correct text" option replaces single characters (uppercase I back to 1, O back to 0), replacement lists, default or abort when a value is missing, date and number formats. (same URL)
- Informs: Y, Ş, D (read-error corrections and per-field formats as template options).
- Maturity and trial: unverified.

### 2.6 Fujitsu PaperStream Capture (PFU, now Ricoh)
- Link: https://www.fujitsu.com/uk/products/computing/peripheral/scanners/business/paperstream/ps-capture/ (redirected to a generic page when fetched, so no facts taken from it)
- Licence: proprietary.
- Relevant (search snippet only): separation by blank page, page numbers, zonal OCR, patch code, barcode 1D/2D; up to 100 meta data fields; AI-OCR option for field auto-add. The datasheet fetch (https://scanners.us.fujitsu.com/-/media/project/scanners/files/products/datasheets/pscp_datasheet_06_21.pdf) redirected and was not read.
- Informs: Y. Everything about this product is unverified from opened pages.

### 2.7 Kodak Capture Pro
- Link: https://resources.kodakalaris.com/support/Capture%20Pro%20Help/Content/Separating_documents_with_bar_code_zones.htm
- Licence: proprietary.
- Relevant: draw a barcode zone in Job Setup; under Separation choose "create a new document" (or a new batch); optionally delete the separator page, yet its barcode stays available for document-level indexing; optional mask or minimum length so only matching values split; optional rotate-all-pages to the barcode orientation. (same URL)
- Informs: Y, Ş, K (value mask on separator codes avoids false splits).
- Maturity and trial: unverified.

### 2.8 Adobe Acrobat (Organize Pages, Split, Action Wizard)
- Link: https://helpx.adobe.com/acrobat/desktop/edit-documents/organize-pages/split-pdfs.html (403 to the fetch tool)
- Licence: proprietary, subscription.
- Relevant (search snippet only): split by page count, file size or top-level bookmarks. Action Wizard page also returned 403, so Action Wizard facts are unverified.
- Informs: X. Low priority for ideas; PDF-XChange below was verified instead.

### 2.9 PDF-XChange Editor
- Link: https://help.pdf-xchange.com/pdfxt11/splitting-pages.html
- Licence: proprietary (free tier or trial: unverified).
- Relevant: Organize tab Split Document by bookmark nesting level, every n pages, or maximum file size, with filename macros; Split Pages cuts single pages at set positions or along guide lines (same URL). Thumbnails pane: Ctrl+T, drag to reorder, Ctrl+click to multi-select (search snippet only).
- Informs: K, X.

### 2.10 Tungsten Power PDF
- Link: https://www.tungstenautomation.com/products/power-pdf
- Licence: proprietary. Platform: Standard on Windows 8.1, 10, 11; Mac edition macOS 10.15 to 26; mobile apps (https://www.tungstenautomation.com/products/power-pdf) [corrected].
- Relevant: Split, rearrange, delete pages; Advanced edition has batch processing and batch workflows. Free 15-day full-function trial, one install, no card (same URL). OCR is not mentioned on the page.
- Informs: K, X. Trial can be inspected.

### 2.11 Readiris 17 (IRIS)
- Link: https://iriscorporate.com/softwares/readiris-17/ : the page opened was an IRIS product overview that does not mention batch, split, barcode, Turkish or trial. All Readiris claims unverified.

### 2.12 Hyland OnBase (platform)
- Link: https://www.hyland.com/en/solutions/products/onbase
- Relevant: "automated multichannel capture" that classifies and verifies; no further detail on the page. Informs: R only.

---

## Group 3: Review UIs and large-list UX references

### 3.1 ABBYY FlexiCapture verification (see 2.1)
- Keyboard model worth copying as a pattern (not code): Enter = confirm, a distinct key = postpone and mark unverified, jump between processed fields, page image of the current field only (https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work). Informs D.

### 3.2 Tungsten Transact Validate screen (see 2.3)
- Three panels and red/green status per document, reasons for red (https://ephesoft.com/docs/?p=47801). Informs D and K.

### 3.3 OnBase Advanced Capture viewer
- Search snippet only: captured values highlighted during verification and the viewer zooms to the captured zone automatically (search result, no page opened). Idea matches our need for weaker eyesight: the crop of the region is shown big next to the value. Unverified.

### 3.4 FastRawViewer (photo culling)
- Link: https://www.fastrawviewer.com/howtos/sorting-photos
- Licence: proprietary. Platform: not stated on the page. Re-confirmed; also Ctrl+Z undoes the last reject.
- Relevant: select with Ctrl+/ or select-and-advance with Ctrl+. or Shift+Right; Shift+click ranges, Ctrl+click picks; hover checkbox at thumbnail corner; rating Alt+. and Alt+,; rejects move to a _Rejected subfolder and can be restored; all shortcuts customizable (same URL). Informs K (select-and-advance, reversible reject).
- Trial: unverified.

### 3.5 Photo Mechanic
- Search snippet only: shortcut keys cover captions, keywords, labels; no AI scoring; price unverified. No page opened. Informs K. Unverified.

### 3.6 Qt QListView (our own toolkit)
- Link: https://doc.qt.io/qt-6/qlistview.html
- `uniformItemSizes` lets the view optimize when all items are equal; `layoutMode: Batched` lays out in groups of `batchSize` (default 100) while the event loop keeps running so visible items are usable early; the page does not quantify the gain, so measure. IconMode is presentation, not a performance setting. Informs K. Free, documentation only. Re-confirmed: default `uniformItemSizes` false, `batchSize` default 100. Relevant to the existing perf-profile skill.

### 3.7 TanStack Virtual
- Link: https://tanstack.com/virtual/latest
- Windowing: mounts only viewport rows plus overscan (demo: 100,000 rows, about 10 mounted); estimated sizes first, refined by measurement; grid and two-axis layouts; restores scroll position when returning to a view. The page does not name a licence (unverified; see its GitHub). It is a web library, not usable in PySide6; useful only as a vocabulary and pattern source (estimated size first, overscan, restore scroll). Informs K.

### 3.8 Hyland Perceptive Intelligent Capture Verifier
- Search snippet only: a Verifier guide exists with Indexing Window, Document Pane and Form Pane (https://docs.hyland.com/PIC/en_US/5.6/Print/Perceptive_Intelligent_Capture_Verifier_User_Guide_5.6.x.pdf). Not opened. Unverified.

Not found: a photo-library tool or open-source project documenting thumbnail strip virtualization specifically; Qt's `QListView` docs and TanStack Virtual are the closest verified sources.

---

## Added in the second pass

### 4.1 Stirling-PDF [new]
See the table above. Licence is MIT with named non-MIT directories; do not assume the whole tree is MIT. Informs X, K (page tools). https://github.com/Stirling-Tools/Stirling-PDF

### 4.2 Label Studio [new]
Apache-2.0 annotation tool (https://github.com/HumanSignal/label-studio). The opened page gives no keyboard-shortcut or OCR facts; useful only as a reference for drawing boxes on images and a data manager list. Informs Ş.

### 4.3 Azure Document Intelligence Studio [new]
- Link: https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/studio-overview?view=doc-intel-4.0.0
- Licence: proprietary cloud service, so it conflicts with our offline rule; reading its docs for ideas only.
- Relevant: a visual labeling interface to label, train and validate custom field-extraction models; a classification model that can split a multi-document file by page range; optional barcode extraction add-on (same URL). Informs Ş, Y (concept vocabulary only).

---

## Not reopened in the second pass
OpenKM CE, Readiris, PaperStream Capture, Photo Mechanic, Perceptive Verifier, Brainware page, OnBase platform page, Acrobat, Paperless-ngx docs site (403). Their text above is unchanged and keeps its first-pass status.

---

## Recommended shortlist (study in depth, 10)

1. ABBYY FlexiCapture field verification: documented keyboard model (Enter confirm, Ctrl+Enter postpone, Ctrl+Up/Down move, Ctrl+Alt+I show page image) for Değerler.
2. Tungsten Transact Validate screen: red/green status per document and tab, explicit reasons a field is red, merge and split in the review screen (D, K).
3. Kodak Capture Pro barcode separation: value mask and minimum length against false splits, delete separator but keep its barcode (Y, Ş, K).
4. DocuWare Processing: split criteria set and "Correct text" read-error fixes, defaults, date and number formats (Y, Ş, D).
5. Hyland OnBase Advanced Capture zones: drag-a-box zone editor with typed fields and coloured overlay (Ş).
6. Paperless-ngx (GPL-3.0, read source only): barcode split semantics, retain-separator flag, ASN barcode on a content page (Y, K, R).
7. PDF Arranger (GPL-3.0, read source only): page strip with drag reorder, rich selection (odd/even/range/inverted), undo and redo, rotate, crop (K).
8. PdfQRSplit and scanprep (MIT): shortest complete separator-detection code with keep-page options and blank removal (Y).
9. FastRawViewer: select-and-advance keys, reversible reject with undo, customisable shortcuts (K).
10. Qt QListView docs (our own toolkit): uniform item sizes and batched layout for the Kontrol strip (K, performance).

Also useful but not shortlisted: OCRmyPDF (PDF/A and text layer, X; MPL-2.0), NAPS2 (scan UX, GPL), invoice2data (MIT, template format idea), Tungsten Capture (batch versus document separators, R).

## Could not verify

- Release dates with year for Paperless-ngx, PDF Arranger, OCRmyPDF, Docspell, Teedy (day and month only).
- Release data and platform for ScanTailor Advanced, Mayan EDMS licence and activity, scanprep, PdfQRSplit, invoice2data, ZBar, zxing-cpp.
- Whether NAPS2 supports barcode or patch-T separation.
- All of PaperStream Capture, Readiris, Photo Mechanic, Perceptive Verifier, Acrobat Action Wizard (pages blocked, redirected or not opened).
- Free trial availability for ABBYY, Hyland, DocuWare, Capture Pro, Tungsten Capture, Transact.
- Paperless-ngx configuration page (docs.paperless-ngx.com returned 403); barcode facts come from its GitHub docs source.
- Turkish OCR support in any commercial product.
- Whether NAPS2, Stirling-PDF auto-split, or ScanTailor Advanced deskew highlighting exist (not shown on opened pages).
- Turkish traineddata availability in tessdata_fast (file list truncated).

Checked 2026-11-19: 27 entries opened, 10 corrected, 3 added (Stirling-PDF, Label Studio, Azure Document Intelligence Studio). Shortlist: 10 entries.
