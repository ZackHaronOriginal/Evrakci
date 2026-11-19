# Competitor and reference research (ideas only)

Researched 2026-11-19. Scope: Evrakçı tabs Yükle, Kontrol, Şablonlar, Değerler, Dışa Aktar, Rehber.

## Header: how to use this file

- This is research for ideas only. Do NOT copy code, text, icons, layouts pixel-for-pixel or strings from any project listed here into the Evrakçı repo. Several are GPL, AGPL or LGPL, some need a CLA to contribute, and commercial products are proprietary. Reading a source file to understand an approach is fine; transcribing it is not. If a design idea is adopted, re-derive it in our own words and code.
- Nothing was cloned. Nothing was installed.
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
- Inspect: source on GitHub; demo not checked (unverified).

### 1.2 NAPS2
- Link: https://github.com/cyanfish/naps2
- Licence: GPL 2.0 or later; NAPS2.Escl.*, NAPS2.Images.*, NAPS2.Internals, NAPS2.Sdk under LGPL 2.1 or later; NAPS2.Sdk.Samples MIT (https://github.com/cyanfish/naps2)
- Platform: Windows 7+ (x64, x86), macOS 10.15+, Linux x64/arm64 (GTK 3.20+). Scanner drivers: WIA, TWAIN, SANE, ESCL. (same URL)
- Relevant: scan-then-organize page list with Tesseract OCR, PDF/TIFF/JPEG/PNG output (same URL). The front page does not mention barcode or patch-T separators; whether the app has them is unverified.
- Informs: Y (scanner acquisition, page list handling), X.
- Maturity: 8.6.1 marked Latest, 19 November 2026 per asset timestamps; 9.0b1 pre-release the same day (https://github.com/cyanfish/naps2/releases). Very active.
- Inspect: free, source on GitHub. Best desktop reference for scan UX on Windows.

### 1.3 scanprep
- Link: https://github.com/baltpeter/scanprep
- Licence: MIT (https://github.com/baltpeter/scanprep)
- Platform: Python CLI (PyPI, Snap, source); needs zbar (same URL).
- Relevant: splits a batch-scanned PDF at pages carrying a barcode with text `SCANPREP_SEP`, also removes blank pages (both on by default, each can be turned off). Ships a printable separator PDF. Output named `0-<file>.pdf`, `1-<file>.pdf`. (same URL)
- Informs: Y, R (the minimal "separator plus blank removal" contract).
- Maturity: unverified; page shows 5 commits and no dates.
- Inspect: source, small enough to read in minutes.

### 1.4 PdfQRSplit
- Link: https://github.com/adlerweb/PdfQRSplit
- Licence: MIT (https://github.com/adlerweb/PdfQRSplit)
- Platform: Python script using zxing, pypdf4, pillow (same URL).
- Relevant: scans each page for a barcode; default separator text `ADAR-NEXTDOC` (changeable). Separator dropped by default; `-k` keeps it in the previous document, `--keep-page-next` in the next one. `-b` sets the brightness threshold used before reading (default 128). (same URL)
- Informs: Y, Kontrol options for where the separator page goes.
- Maturity: unverified; 15 commits shown, no dates.
- Inspect: source, tiny.

### 1.5 PDF Arranger
- Link: https://github.com/pdfarranger/pdfarranger
- Licence: GPL-3.0 (https://github.com/pdfarranger/pdfarranger)
- Platform: Linux, Windows, macOS, FreeBSD (Python GTK) (same URL).
- Relevant: merge, split, rotate, crop, rearrange pages in a GUI. The README text does not confirm thumbnails or drag-drop by name; those are unverified from opened pages (a screenshot exists on the page).
- Informs: K (page strip editing: move, rotate, delete).
- Maturity: 1.14.0 published 23 May, year not shown (https://github.com/pdfarranger/pdfarranger/releases).
- Inspect: free, source.

### 1.6 PDFsam Basic
- Link: https://github.com/torakiki/pdfsam
- Licence: AGPL, since version 3 (earlier GPLv2) (https://github.com/torakiki/pdfsam)
- Platform: "multi-platform", JavaFX; v4+ bundles its own JDK (same URL).
- Relevant: extract, split, merge, mix, rotate PDFs. Split methods are not detailed on the repo page (unverified).
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
- Relevant: YAML/JSON templates with keywords and regex per field, static and custom fields, currency, `replace:` clean-up; optional OCR backends Tesseract, ocrmypdf, docTR, PaddleOCR, Google Vision; can rename PDFs to match content (same URL). Keyword/regex based, not coordinate zones.
- Informs: Ş, D (template file format, per-field clean-up rules, rename by content).
- Maturity: unverified; no dates on the page.
- Inspect: source.

### 1.9 ScanTailor Advanced
- Link: https://github.com/4lex4/scantailor-advanced (the `ScanTailor/scantailor-advanced` URL returned 404)
- Licence: GPL-3.0 (https://github.com/4lex4/scantailor-advanced)
- Platform: not stated on the page; Flathub listing exists (search snippet only).
- Relevant: staged pipeline (page split, deskew with deviation highlighting that flags pages with too much skew, content selection, margins, dewarping, zoning, output), multi-threaded batch processing (same URL). The "flag only the pages that need a look" pattern fits Kontrol.
- Informs: K, Y.
- Maturity: unverified; Releases section empty, 512 commits. Version v1.0.16 seen only in a search snippet.
- Inspect: free, source.

### 1.10 Mayan EDMS
- Link: https://gitlab.com/mayan-edms/mayan-edms (the GitHub mirror says it is no longer maintained and very outdated: https://github.com/mayan-edms/mayan-edms)
- Licence: unverified (GitLab page shows a licence badge but does not name it).
- Platform: Docker Compose deployment; Python/Django (GitHub mirror page).
- Relevant: "Free Open Source DMS" with topics OCR, PDF, indexing, workflow (https://gitlab.com/mayan-edms/mayan-edms). Detailed feature docs not read (docs.mayan-edms.com returned 403).
- Informs: R (document lifecycle ideas only). Low priority.
- Maturity: unverified; GitLab page shows 2 tags, no names.

### Also checked (lower priority)

| Name, link | Licence | What | Tabs | Notes |
|---|---|---|---|---|
| Docspell, https://github.com/eikek/docspell | AGPL-3.0 | Personal DMS; imports from scanners, email; OCR; tags with ML suggestions. Splitting not mentioned. | R | v0.43.0 "Latest", 15 Mar, year not shown (https://github.com/eikek/docspell/releases) |
| Teedy, https://github.com/sismics/docs | GPL-2.0 | Lightweight DMS: OCR, workflow, versioning, bulk importer, tested to 1M documents | R | v1.11, 12 March, year not shown (https://github.com/sismics/docs/releases) |
| OpenKM CE, https://github.com/openkm/document-management-system | GPL-2.0 up to 6.x; v7.0+ binary only; repo archived 10 March 2026 | DMS | none | Not worth studying (same URL) |
| pdf-scan-splitter, https://github.com/kduma-OSS/CLI-pdf-scan-splitter | not stated | Splits every page to its own PDF, names by first Code-128 barcode, `UNKNOWN.pdf` otherwise; runs in Docker with zbar | Y | Last commit 16 December 2022 (https://github.com/kduma-OSS/CLI-pdf-scan-splitter/commits). Rename-by-barcode idea only |
| ZBar, https://github.com/mchehab/zbar | LGPL-2.1 | Barcode reader suite; EAN, Code 128/39/93, Codabar, ITF, QR, SQ | Y | Release date unverified (https://github.com/mchehab/zbar) |
| zxing-cpp, https://github.com/zxing-cpp/zxing-cpp | Apache-2.0 | Barcode read/write, QR, Data Matrix, Aztec, PDF417, Code 128; Python wrapper exists | Y | Release date unverified (https://github.com/zxing-cpp/zxing-cpp) |
| Tesseract, https://github.com/tesseract-ocr/tesseract | Apache-2.0 | OCR engine, LSTM since v4, 100+ languages; page does not cover region/rectangle options | Ş, D | 5.0.0 on 30 Nov 2021; newer releases not read (https://github.com/tesseract-ocr/tesseract) |

Zonal OCR: a search for open-source coordinate-zone template tools found only invoice2data (keyword based) and DIY Tesseract cropping (search snippet only, https://github.com/invoice-x/invoice2data). No mature open-source "draw zones on a sample page" product was found. That gap is the argument for studying the commercial zone editors below.

---

## Group 2: Commercial capture and batch scanning

### 2.1 ABBYY FlexiCapture
- Link: https://www.abbyy.com/flexicapture/
- Licence: proprietary. Platform: on-prem or cloud; HTML5 web stations in Chrome, Firefox, Edge; SDK; mobile (same URL).
- Relevant: capture, classify, extract, validate. Field verification docs: fields reviewed one at a time, Enter confirms, Ctrl+Enter postpones (marks unverified), Ctrl+Up/Down moves between processed fields, Ctrl+Alt+I shows the page image for the field with a zoom list, Ctrl+Alt+F shows the same field in analogous documents. (https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work)
- Informs: D, K.
- Maturity: unverified. Trial: page does not mention a free trial; demo by request form (https://www.abbyy.com/flexicapture/).

### 2.2 Tungsten Capture (formerly Kofax Capture)
- Link: https://docshield.tungstenautomation.com/KC/en_US/11.1.0-40hy9nfk91/help/main/KC_administration/c_batchseppatchcode.html
- Licence: proprietary. Platform: Windows (unverified from opened pages).
- Relevant: a reserved patch code type closes the current batch and opens a new one; the barcode on the separator sheet picks the batch class; a code reserved for batch separation cannot also be used for document separation; Separator Sheet Utility prints the sheets (same URL). Rubber Band OCR in validation fills index fields from drawn zones (search snippet only).
- Informs: Y, Ş, R (batch level versus document level separators).
- Maturity: documentation 11.1 and 11.2 seen in search; current version unverified. Trial: unverified.

### 2.3 Tungsten (Ephesoft) Transact
- Link: https://ephesoft.com/docs/?p=47801 and https://docshield.tungstenautomation.com/Transact/en_US/2023.1.00-oismpn77w5/help/User/Transact_Help/operatorrolesfeatures/c_validateuserinterface.html
- Licence: proprietary.
- Relevant: Validate screen has three panels: documents and pages (red/green status per document, Alt multi-select), extracted index fields, and image preview. Fields turn red when the field is not found, below OCR confidence threshold, or fails its validation pattern; a red field must be dealt with before the Validate button approves and advances. Group tabs show a green circle or a red exclamation mark. Toolbar has Merge, Split, Table. Ctrl+Shift+O opens a page view for reordering pages. (https://ephesoft.com/docs/?p=47801)
- Informs: D, K (the reasons a field needs attention, tab-level status marks).
- Maturity and trial: unverified.

### 2.4 Hyland OnBase Advanced Capture and Brainware
- Links: https://www.hyland.com/en/products/brainware and https://docs.hyland.com/r/OnBase/Advanced-Capture/Foundation-23.1/Advanced-Capture/Configuration/Configuring-Advanced-Capture/Configuring-Advanced-Capture-Forms/Configuring-A-Data-Field-Zone
- Licence: proprietary.
- Relevant: OnBase data field zones are drawn by dragging a box on the document; the dialog has tabs by data type (Text Field, Line Item, Grouped Line Item, Optical Mark, Signature Detection); saved zones show as green or hatched red on the page. Brainware is mostly template-less, routes exceptions to a customizable verification screen and learns from corrections; page mentions no free trial, demo by request (https://www.hyland.com/en/products/brainware).
- Informs: Ş (draw-a-box zone editor with typed fields), D.
- Maturity and trial: unverified.

### 2.5 DocuWare
- Link: https://knowledgecenter.docuware.com/docs/processing-documents
- Licence: proprietary.
- Relevant: splitting by fixed page count, by text criteria (needs a sample document), or when a barcode value changes. Indexing readout areas: text before/after/between a string, field delimiters, fixes for common read errors such as "1" read as "I", replacement lists, default or abort when a value is missing, date and number formats. (same URL)
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
- Relevant: Organize tab Split Document by bookmark nesting level, number of pages, or maximum file size; Split Pages by position and by guide lines. (same URL) Thumbnails pane: Ctrl+T, drag to reorder, Ctrl+click to multi-select (search snippet only).
- Informs: K, X.

### 2.10 Tungsten Power PDF
- Link: https://www.tungstenautomation.com/products/power-pdf
- Licence: proprietary. Platform: Windows 8.1 to 11 including ARM; macOS (page gives conflicting version ranges).
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
- Licence: proprietary. Platform: not stated on the page.
- Relevant: select with Ctrl+/ or select-and-advance with Ctrl+. or Shift+Right; Shift+click ranges, Ctrl+click picks; hover checkbox at thumbnail corner; rating Alt+. and Alt+,; rejects move to a _Rejected subfolder and can be restored; all shortcuts customizable (same URL). Informs K (select-and-advance, reversible reject).
- Trial: unverified.

### 3.5 Photo Mechanic
- Search snippet only: shortcut keys cover captions, keywords, labels; no AI scoring; price unverified. No page opened. Informs K. Unverified.

### 3.6 Qt QListView (our own toolkit)
- Link: https://doc.qt.io/qt-6/qlistview.html
- `uniformItemSizes` lets the view optimize when all items are equal; `layoutMode: Batched` lays out in groups of `batchSize` (default 100) while the event loop keeps running so visible items are usable early; the page does not quantify the gain, so measure. IconMode is presentation, not a performance setting. Informs K. Free, documentation only. Relevant to the existing perf-profile skill.

### 3.7 TanStack Virtual
- Link: https://tanstack.com/virtual/latest
- Windowing: mounts only viewport rows plus overscan (demo: 100,000 rows, about 10 mounted); estimated sizes first, refined by measurement; grid and two-axis layouts; restores scroll position when returning to a view. Licence not stated on the page (unverified). It is a web library, not usable in PySide6; useful only as a vocabulary and pattern source (estimated size first, overscan, restore scroll). Informs K.

### 3.8 Hyland Perceptive Intelligent Capture Verifier
- Search snippet only: a Verifier guide exists with Indexing Window, Document Pane and Form Pane (https://docs.hyland.com/PIC/en_US/5.6/Print/Perceptive_Intelligent_Capture_Verifier_User_Guide_5.6.x.pdf). Not opened. Unverified.

Not found: a photo-library tool or open-source project documenting thumbnail strip virtualization specifically; Qt's `QListView` docs and TanStack Virtual are the closest verified sources.

---

## Recommended shortlist (study in depth)

1. ABBYY FlexiCapture field verification: best-documented keyboard model for confirm, postpone, jump (D).
2. Tungsten Transact Validate screen: red/green per document, explicit reasons (not found, low confidence, pattern fail), group tab marks (D, K).
3. Kodak Capture Pro barcode separation: value mask, delete separator but keep its barcode for indexing, new batch versus new document (Y, Ş, K).
4. Tungsten Capture batch separator patch code: batch level versus document level separators (Y, R).
5. Hyland OnBase Advanced Capture zones: drag-a-box zone editor with typed fields and visible zone overlay (Ş).
6. DocuWare Processing: split criteria set and per-field read-error corrections, defaults and formats (Y, Ş, D).
7. Paperless-ngx barcode docs: separator discarded versus retained, ASN barcode on a content page (Y, K, R).
8. NAPS2: scan-to-page-list UX, OCR, multi-OS scanner drivers (Y).
9. FastRawViewer: select-and-advance keys, reversible reject, customizable shortcuts (K).
10. PDF-XChange Editor: split-by-bookmark, pages, size, guide lines and thumbnail pane behaviours (K, X).
11. OCRmyPDF: PDF/A plus text layer options and deskew flags (X).
12. Qt QListView docs (uniform sizes, batched layout): direct input to Kontrol strip performance (K).

### Three open-source projects to read the source of

1. Paperless-ngx (GPL-3.0): barcode detection and split logic, ASN handling. Read only.
2. OCRmyPDF (MPL-2.0): how PDF/A and text-layer output are assembled. Read only.
3. PdfQRSplit (MIT; scanprep, MIT, as a second small read): shortest complete example of separator detection with keep-page options. Read only.

Honourable mention: NAPS2 (GPL 2+/LGPL SDK) for scanner and page-list handling; invoice2data (MIT) for the template file format.

---

## Could not verify

- Release dates with year for Paperless-ngx, PDF Arranger, OCRmyPDF, Docspell, Teedy (day and month only).
- Release data and platform for ScanTailor Advanced, Mayan EDMS licence and activity, scanprep, PdfQRSplit, invoice2data, ZBar, zxing-cpp.
- Whether NAPS2 supports barcode or patch-T separation.
- All of PaperStream Capture, Readiris, Photo Mechanic, Perceptive Verifier, Acrobat Action Wizard (pages blocked, redirected or not opened).
- Free trial availability for ABBYY, Hyland, DocuWare, Capture Pro, Tungsten Capture, Transact.
- Paperless-ngx configuration page (docs.paperless-ngx.com returned 403); barcode facts come from its GitHub docs source.
- Turkish OCR support in any commercial product.
