# Ideas for ranking (Phase 5d)

Nothing here is decided. Rank each row in the last column: **must**, **should**, **later** or **drop**.
Blank rows stay "not ranked" and are not built. A ranked row then gets a one-page spec in 5e, and you approve each spec before any build.

- The Kontrol filters (feature-ideas 1-7, here I-01, I-03 to I-07) are the plan's first build item in 5e. I-08 (remove filter) belongs with them.
- Bugs are not ideas and are not listed; see the last section.
- "changes Dx: needs your yes" means the idea would reopen a fixed decision in `decisions.md`.
- Turkish labels marked "draft" are working names only, not UI text.
- Effort: S small, M medium, L large. Core: "no" = UI only; "minimal hook D13" = a small, tested change in `src/evrakci/pipeline/` or the CLI (D13).
- Findings files are in `docs/ui-goal/research/`. FI-n = `feature-ideas.md` item n.

## Kontrol

| ID | Idea | Problem it solves | Who gains | Evidence | Effort | Risk | Perf cost | Tab | Core change | Your rank |
|---|---|---|---|---|---|---|---|---|---|---|
| I-01 | Select pages by QR content or pattern (prefix, mask); also cut at any QR value, not only `EVRAKCI-AYIRAC` (FI-1, splitting 3 merged) | Separator or form QR carries a box number or kind; staff cannot jump to or cut at "all KAP-..." | Chambers with pre-printed numbered forms | findings-splitting.md; [Kodak mask](https://resources.kodakalaris.com/support/Capture%20Pro%20Help/Content/Separating_documents_with_bar_code_zones.htm); [DocuWare](https://knowledgecenter.docuware.com/docs/processing-documents) | M | Medium: how non-separator QR shows | Low (text kept at analysis) | Kontrol | minimal hook D13 (keep decoded QR text, mask) | drop (owner 2026-11-20: QR is only the separator) |
| I-02 | Option: keep the separator page as the first page of the next document | Content-bearing sheets are lost as separators | Offices using real forms as separators | findings-splitting.md; [Paperless](https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md) | M | Medium: changes page counts and names | None | Kontrol | minimal hook D13 | |
| I-03 | Select blank pages with a threshold and live count (FI-2) | Blank backs stay unless all-or-nothing drop is used | Duplex scanners | findings-splitting.md; [scanprep](https://github.com/baltpeter/scanprep) | S | Low: Del stays undoable | Low (ink ratio exists) | Kontrol | no | |
| I-04 | Select by page size or orientation, with "looks different" marks (icon plus word) and a jump command (FI-3, FI-4, filtering 1 merged) | Odd inserts and sideways pages hide in 400 pages | Reviewers of mixed piles | findings-filtering.md; [ScanTailor](https://github.com/4lex4/scantailor-advanced) | M | Medium: a second mark must not clash with Kontrol orange (D1) | Low | Kontrol | no | |
| I-05 | Select pages whose OCR text contains a word, with Turkish case folding; later a result list (FI-5, search 3 merged) | Place cuts without a QR separator | Staff of documents with fixed titles | findings-search.md; [Paperless search](https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md) | L | High: OCR before Değerler on 800 pages | High | Kontrol | minimal hook D13 (page text before Değerler) | |
| I-06 | Select low-confidence pages or values, with reasons and counts (FI-6) | Go straight to what the machine is unsure of | Reviewers in long sessions | feature-ideas.md FI-6; findings-review-qc.md | M | Medium: must not add a second "Kontrol" colour | Low | Kontrol | no | |
| I-07 | Saved filters as a chip row, stored with the template, and combining filters (AND) with one count (FI-7, filtering 3 merged, plan 5e item 2) | Same filter set up again for every job of a kind | Repeat jobs | findings-filtering.md; [Paperless saved views](https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/usage.md) | M | Medium: filters must not hard-code document kinds | Low | Kontrol | no | |
| I-08 | Window commands now only in CLI or missing: "remove filter" (K-28), restore an emptied page (K-20), remove a template from documents (K-52) | Wrong N cannot be taken back; core can, window cannot | Everyone using filters | findings-filtering.md 2; findings-page-operations.md 3 | S | Low | None | Kontrol | no (core exists) | |
| I-09 | Select this document; select odd or even pages; verify and document Ctrl+Space (toggle focused page) | Filters and templates need a selection; today staff drag | Keyboard-only staff, duplex piles | findings-selection.md; [PDF Arranger manual](https://github.com/pdfarranger/pdfarranger/wiki/User-Manual); invert selection stays deferred | S | Low | None | Kontrol | no | |
| I-10 | Move a page (cut and paste to another position or end of document) | Pages scanned in the wrong order | Offices with feeder jams | findings-page-operations.md 1; [PDF Arranger](https://github.com/pdfarranger/pdfarranger) | L | High: split and name rules after a move | Low | Kontrol | minimal hook D13 | |
| I-11 | "Come back later" mark on a document (postpone) (page-ops 2 and review-qc merged; the two versions conflicted) | Unsure reviewers cannot park a document | Reviewers | findings-page-operations.md 2; findings-review-qc.md (judges it less safe); [ABBYY](https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work) | S-M | High: adds a third review state; changes the approved İncelendi / İncelenmedi vocabulary (decisions.md, round 1): needs your yes | None | Kontrol | minimal hook D13 (job state) | |
| I-12 | Say what happens to the separator and typed values at a cut or merge | After M or K staff cannot tell if values moved | Every reviewer | findings-splitting.md 1; [Transact](https://ephesoft.com/docs/?p=47801) | S | Low | None | Kontrol | no | |
| I-13 | Quiet hint when a document is far from the usual page count, e.g. "3 belge 1 sayfa" (draft) (FI-9) | Wrong cuts in a batch of a known kind | Reviewers | feature-ideas.md FI-9 | M | Medium: false hints add noise (never-silent vs calm) | Low | Kontrol | no | |
| I-14 | Loupe with the neighbouring page (last of one document, first of next) (FI-10) | Judging a cut needs both sides | Reviewers | feature-ideas.md FI-10 | M | Medium: loupe layout, 150 % text | Low | Kontrol | no | |
| I-15 | Suggest a template per document from QR kind or OCR text; staff confirm (FI-15) | Applying the right template by hand is repetitive | Mixed batches | feature-ideas.md FI-15 | L | High: wrong suggestion; must stay a suggestion | Medium | Kontrol | minimal hook D13 | |
| I-16 | Thumbnail cache capped by bytes, not 400 entries; measure first; add 200 % zoom sweep and 8 hour soak to the perf script (perf 1 and 4 merged) | Memory grows with zoom in long sessions | Staff on 4 to 8 GB PCs | findings-performance.md; [QPixmapCache](https://doc.qt.io/qt-6/qpixmapcache.html) | S-M | Low | Positive if it works | Kontrol | no | |

## Değerler

| ID | Idea | Problem it solves | Who gains | Evidence | Effort | Risk | Perf cost | Tab | Core change | Your rank |
|---|---|---|---|---|---|---|---|---|---|---|
| I-17 | Show which cell is wrong, not only the row | One bad cell hides among four | Every reviewer | findings-review-qc.md 1; [Transact](https://ephesoft.com/docs/?p=47801) | M | Low | Low | Değerler | no | |
| I-18 | Sample check: calibration line ("N errors in M sampled Emin values"), sample size scaled to the batch, stop rule (qc 2 and 3 merged) | Nobody learns whether Emin is trustworthy; 20 values for 800 documents | Owner and template setter | findings-review-qc.md; [ACL NLP4DH 2023](https://aclanthology.org/2023.nlp4dh-1.20.pdf); [NARA guide](https://Archives.gov/files/records-mgmt/policy/digitization-quality-mgmt-guide.pdf) (analogy) | S | Medium: wording must not scare | None | Değerler | no | |
| I-19 | Show every section's reading next to the suggestion (O-16) | Enter rests on one anchor | Reviewers | findings-review-qc.md 4; [PMC5356416](https://pmc.ncbi.nlm.nih.gov/articles/PMC5356416) | S | Low | None | Değerler | no | |
| I-20 | Crop strip: the same variable across documents | A shifted box is hard to see one document at a time | Template setters | findings-review-qc.md 5; [ABBYY](https://docs.abbyy.com/flexi-capture/operator-work/field-verification-operator-work) | M | Medium: 800 crops in memory | Medium | Değerler | no | |
| I-21 | Carry the document from Değerler to Kontrol (O-09; mirror of B-012, not in the ledger) | Tab switch loses the document | Everyone using both tabs | findings-review-qc.md 6; findings-template-design.md 1 | S | Low | None | Değerler, Kontrol | no | |
| I-22 | Show "Zorunlu" and warn on an empty required value | Empty accepted silently; file name fails at export (O-11, O-12) | Staff who learn at export | findings-value-editing.md 1; [invoice2data](https://github.com/invoice-x/invoice2data/blob/master/src/invoice2data/extract/invoice_template.py) | S | Low | None | Değerler | no | |
| I-23 | "Okunana dön" (draft): revert a value to the machine reading in the window (V-65, O-10) | Core can, window cannot | Reviewers | findings-value-editing.md 2 | S | Low | None | Değerler | no (core exists) | |
| I-24 | "Apply to similar" after a correction, with preview (V-69 does a version in Örnek) | Same fix typed again and again | Reviewers | findings-value-editing.md 5 | M | Medium: wrong bulk edit; must be undoable | Low | Değerler | no | |
| I-25 | "Re-read this value from a box I draw" | A bad crop cannot be retried | Reviewers | findings-region-reading.md 5; [Kofax Rubber Band](https://docshield.tungstenautomation.com/KC/en_US/11.1.0-40hy9nfk91/help/main/KC_validation/t_rubberband_ocr.html) | M | Medium | Low | Değerler | no (reader exists; check) | |
| I-26 | Read all variants and offer the most confident | Wrong variant gives wrong value | Mixed layouts | findings-region-reading.md 4; [Kofax index zone](https://docshield.tungstenautomation.com/KC/en_US/11.1.0-40hy9nfk91/help/main/KC_administration/c_indexgrpzonepropgen.html) | M | Medium | High (read time per variant) | Değerler | minimal hook D13 | |
| I-27 | Reading trials first: padding, single-line mode (psm 7), preprocessing, weakest word as flag score (region 1 and 2 merged); switch on only what the harness shows wins | Live reads skip standard small-crop advice; a mean hides one bad word | Everyone reading values | findings-region-reading.md; [Tesseract ImproveQuality](https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html); [ACL NLP4DH 2023](https://aclanthology.org/2023.nlp4dh-1.20.pdf) | S (measure), S-M | Medium: Turkish effect unmeasured | None or lower | Değerler | minimal hook D13 (if switched on) | |

## Şablonlar

| ID | Idea | Problem it solves | Who gains | Evidence | Effort | Risk | Perf cost | Tab | Core change | Your rank |
|---|---|---|---|---|---|---|---|---|---|---|
| I-28 | "Weakest examples first" list after "dene" (S-58) | Only a count shows, not which examples fail | Template setters | findings-template-design.md 2; [Kofax Zone Test](https://docshield.tungstenautomation.com/KC/en_US/11.1.0-40hy9nfk91/help/main/KC_administration/c_zonetest.html) | S | Low | Low | Şablonlar | no | |
| I-29 | Try a template on a PDF that is not in the job (S-37); nothing stored | Testing needs a real job | Template setters | findings-template-design.md 3; Kofax Zone Test (above) | M | Medium: privacy, nothing may be kept | Low | Şablonlar | no (CLI exists, S-62) | |
| I-30 | Snap a drawn box to a word (region 6 and template 4 merged) | Boxes drawn loosely read badly | Template setters | findings-template-design.md 4; findings-region-reading.md 6; analogy only: [Kofax Rubber Band](https://docshield.tungstenautomation.com/KC/en_US/11.1.0-40hy9nfk91/help/main/KC_validation/t_rubberband_ocr.html) | M | Medium: weak evidence | Low | Şablonlar | no | |
| I-31 | Optional "what it contains" hint per variable: digits only, date, number, single line; red mark when text does not fit (region 3, value 3, value 6 merged) | No type today (S-17); display kind is guessed (O-17) | Everyone reading values | findings-region-reading.md 3; findings-value-editing.md 3 and 6; [DocuWare](https://knowledgecenter.docuware.com/docs/processing-documents) | M | Medium: must stay optional (users define content) | None | Şablonlar, Değerler | minimal hook D13 | |
| I-32 | Optional per-variable replace list and fixed value (region 7, value 4, template 5 merged) | Same OCR slip fixed by hand every time | Template setters | findings-value-editing.md 4; findings-template-design.md 5; [invoice2data](https://github.com/invoice-x/invoice2data) | M | Medium: silent rewrite must be shown | None | Şablonlar, Değerler | minimal hook D13 | |
| I-33 | Mark-present zone (checkbox, stamp) | Need unproven | Unknown | findings-template-design.md 7; [OnBase](https://docs.hyland.com/r/OnBase/Advanced-Capture/Foundation-23.1/Advanced-Capture/Configuration/Configuring-Advanced-Capture/Configuring-Advanced-Capture-Forms/Configuring-A-Data-Field-Zone) | L | High | Medium | Şablonlar | minimal hook D13 | |

## Yükle

| ID | Idea | Problem it solves | Who gains | Evidence | Effort | Risk | Perf cost | Tab | Core change | Your rank |
|---|---|---|---|---|---|---|---|---|---|---|
| I-34 | Review progress and "resume where I stopped": open Kontrol at the first İncelenmedi (FI-8) | After an hour staff lose their place | Long sessions | feature-ideas.md FI-8 | S-M | Low | None | Yükle, Kontrol | minimal hook D13 (job state) | |

## Dışa Aktar

| ID | Idea | Problem it solves | Who gains | Evidence | Effort | Risk | Perf cost | Tab | Core change | Your rank |
|---|---|---|---|---|---|---|---|---|---|---|
| I-35 | Add "Belge no", job name and export time to `index.xlsx`; document number column in the printed list (naming 3 and printing 3 merged) | Sheet rows cannot be tied to numbered file names (Obs. 10) | Staff reconciling sheet and folder | findings-naming-export.md 3; findings-printing.md 3; [Kofax log](https://www.manualsdir.com/manuals/658182/kofax-capture.html?page=8) | S | Low | None | Dışa Aktar | minimal hook D13 (index.xlsx is core) | |
| I-36 | Forbidden characters: delete or replace, and fix the checkbox label that says "değiştir" (Obs. 9) | Label and rule disagree | Everyone naming files | findings-naming-export.md 4; [Paperless](https://github.com/paperless-ngx/paperless-ngx/blob/dev/docs/advanced_usage.md) | S | Low: visible change, names change | None | Dışa Aktar | minimal hook D13 (if the rule changes) | |
| I-37 | Check the long-path opt-in in the Windows build | Deep network folders shorten names | Staff exporting to network shares | findings-naming-export.md 5; [Microsoft](https://learn.microsoft.com/en-us/windows/win32/fileio/maximum-file-path-limitation) | S (check), M (ship) | Low | None | Dışa Aktar | no (packaging) | |
| I-38 | Print: repeated header row, page footer with date and job name, and a print preview (printing 1 and 2 merged) | Multi-page list loses its header; no date; no look before paper | Staff filing the printed list | findings-printing.md; [Qt HTML subset](https://doc.qt.io/qt-6/richtext-html-subset.html); [QPrintPreviewDialog](https://doc.qt.io/qt-6/qprintpreviewdialog.html) | S-M | Low: not tried on real printers | Low | Dışa Aktar | no | |
| I-39 | Bulk rename preview: old name, new name, conflict flag before export; copy to clipboard (FI-11) | Wrong names found only after export | Everyone exporting | feature-ideas.md FI-11 | M | Low | Low | Dışa Aktar | no | |
| I-40 | Export a "problems only" report of kontrol items (FI-12) | Supervisor wants the list without the app | Supervisors | feature-ideas.md FI-12 | S-M | Low: must match the app (never silent) | None | Dışa Aktar | minimal hook D13 (index.xlsx sheet) | |
| I-41 | Debounce the folder check on the output path (Obs. 14) | Directory listing per keystroke; slow on network shares | Staff on shares | findings-performance.md 3; [PDF Arranger](https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/pdfarranger.py) (not re-checked) | S | Low | Positive | Dışa Aktar | no | |

## Rehber

No idea rows. Rehber items found by research are bugs (B-006, B-007, B-018 fix idea "document CLI commands in Rehber").

## App-wide

| ID | Idea | Problem it solves | Who gains | Evidence | Effort | Risk | Perf cost | Tab | Core change | Your rank |
|---|---|---|---|---|---|---|---|---|---|---|
| I-42 | Command palette "go to" entries for documents and jobs; keep palette recents between runs (A-33); Ctrl+G shows its target before Enter (FI-14) (search 1 and 2 merged) | Moving to "Belge 37" needs a dialog; recents lost at restart | Keyboard-heavy staff | findings-search.md; [VS Code](https://code.visualstudio.com/docs/getstarted/userinterface) | S-M | Low | Low | App-wide | no | |
| I-43 | Undo: selective undo of an older step; merge repeated rotate presses into one step; measure the whole-job snapshot stack on 800 pages and decide a limit (undo 1, 2, 3 merged; "Geri al acts on its own step" is done, B-023) | Old edits cannot be reverted alone; R three times is three steps; no memory limit (A-56) | Long sessions | findings-undo.md; [Qt QUndoStack](https://doc.qt.io/qt-6/qundostack.html); [PDF Arranger undo](https://github.com/pdfarranger/pdfarranger/blob/main/pdfarranger/undo.py) | M | Medium: silent drop of old steps is forbidden | Medium | App-wide | no | |
| I-44 | Screen reader pass (NVDA, Accessibility Insights) on Kontrol and Değerler; one spoken description of the current page ("Belge 16, sayfa 2, kontrol gerekli"); announce Kontrol history band changes (status line is B-022) (a11y 1, 2, 3 merged) | Hand-painted timeline may be silent | Screen reader and magnifier users | findings-accessibility.md; [Qt accessibility](https://doc.qt.io/qt-6/accessible-qwidget.html); [WCAG 4.1.3](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) | S (test), M | Low | None | App-wide | no | |
| I-45 | Text size 175 and 200 % | Only 150 % at most | Weak eyesight | findings-accessibility.md 4; [WCAG 1.4.4](https://www.w3.org/WAI/WCAG22/Understanding/resize-text.html) | M | High: changes D5 and the 150 % tab-overflow decision (2026-11-13): needs your yes | Low | App-wide | no | |
| I-46 | Check D9 high contrast against edited Windows contrast themes (this is only a check of D9, not a new theme) | Unknown if user-edited colours are followed | High-contrast users | findings-accessibility.md 5; [Microsoft](https://learn.microsoft.com/en-us/windows/apps/design/accessibility/high-contrast-themes) | S-M | Low | None | App-wide | no | |
| I-47 | Busy cursor for any window-thread block over 1 second (opening a big job, first paint); helper exists but unused (A-65) | No cue while the window waits | Everyone on older PCs | findings-performance.md 2; [NN/g](https://www.nngroup.com/articles/response-times-3-important-limits/) | S | Low | None | App-wide | no | |
| I-48 | Pre-filled forms from the office's own data: import Excel sheets or pasted tables (member lists, registry exports), map their columns to the user's own variables (header detection, no built-in field list), merge rows of the same company or person across sheets, then print or export a chosen form already filled for each record; staff only check and correct | Forms are handed out blank and missing fields are later typed in by hand from data the office already has | Staff preparing forms and mailings; members who get a pre-filled form | Owner idea (2026-11-19), shown with a local search tool that merges several Excel exports | L | High: personal data (KVKK): local only, nothing leaves the PC; wrong merge of two companies; needs a form layout designer or reuse of templates | Low | New module / App-wide | no (new module next to the pipeline; one core for window and CLI) | later (owner 2026-11-19: idea to grow, not now) |
| I-49 | Check or fill read values against the office's own data: after Değerler reads a key (e.g. a registry number), look it up in imported sheets and show matching fields (address, NACE code) as a suggestion beside the read value; human confirms | Read values with low confidence or missing fields are re-typed although the office already has them | Reviewers in Değerler | Same owner idea (2026-11-19); relates to I-15 template suggestion and the review-qc findings | M | Medium: personal data stays local; suggestions must never overwrite silently (never silent); stale imports | Low | Değerler | minimal hook D13 (a lookup source for values) | later (owner 2026-11-19: idea to grow, not now) |

## New owner ideas (2026-11-20): later, need thinking and planning first

Logged as given; not specced or built now. Several extend rows above (noted).

| ID | Idea | Relates to | Your rank |
|---|---|---|---|
| I-50 | Şablon review step: after a template is applied, check every applied template; each value shows its 3 best candidate readings and a quick way to pick or change one | I-19, I-24, I-26 | later |
| I-51 | Smarter reading per variable: declare its kind beforehand (number, text, date, ...) and let the reader use it | I-27, I-31 | later |
| I-52 | Check all drawn boxes of one variable together (across documents) and build the value list from that view | I-20 | later |
| I-53 | Variables learn from earlier confirmed answers: check that the reader looks at the right place and that new values look like past correct ones | I-26, I-30 | later |
| I-54 | Rule-based filters and checks on values: length, number vs text, known formats (e.g. bank account number / IBAN), and check-digit or other calculations to verify a value | I-31, I-32 | later |
| I-55 | Connect variables to a future CRM-like app: fetch and send data | I-48, I-49 | later |
| I-56 | Learn from the corrections staff make: every value fixed in Değerler (with its template, box, the reader's text and the confirmed text) is kept as a local example; a learning step after the OCR uses these examples to correct the reader's typical mistakes for that template and box (e.g. I read as 1, 0 as O), so reading gets better with each job. Aim stated with the idea: below 1 % wrong values in the end result. Needs planning: local-only training (no network), how much data is enough, how a learned correction is shown to the reviewer (suggestion, never a silent change), measuring the error rate before and after on synthetic and anonymised data | I-53, I-26, I-30, I-19 | later |
| I-57 | Password-protected PDFs: ask for the password when a scanned PDF is locked, open it, and keep the password only for that session (owner idea 2026-11-26) | Today a locked PDF is refused with "PDF açılamadı" | Offices that receive locked PDFs | owner | M | Medium: passwords must never be stored or logged | low | Yükle | later |

## Already deferred: later (already decided)

Decided 2026-11-13 (decisions.md, "Owner answers before close"); they start as "later" and need no ranking unless you want to move one.

| ID | Idea | Note |
|---|---|---|
| L-1 | First-run tour | Deferred. |
| L-2 | Completion sound (FI-13; the taskbar flash part also stays out) | Deferred. Taskbar progress already exists. |
| L-3 | Invert selection | Deferred; key I is unreliable on Turkish keyboards. |

## Left out on purpose

- Bugs, not ideas: B-003 (PDF/A state differs in list, card, index), B-004 (name pattern not saved with the job), B-006 (no window control for dropping blank pages; I-03 is the filter, not the switch), B-012 (Kontrol "Değerlerde aç" ignores the document), B-013 (variant drawing opens page 1), B-018 (template rename, delete, import, export missing; rename also an open product decision), B-022 (status line not announced), B-023 (toast Geri al acts on its own step: fixed).
- Open ledger entries that touch ideas: B-025 (no unapprove; wontfix) and B-034 (meaning of İncelendi vs Dışa Aktar) bear on I-11 and I-34.
