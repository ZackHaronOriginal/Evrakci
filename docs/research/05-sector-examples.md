# 05 — Sector examples: how the best apps in and around our domain design their UI

**Research limits (read first).** In this session `WebFetch` could not resolve most vendor hosts (helpx.adobe.com, help.abbyy.com, docs.paperless-ngx.com, spectrum.adobe.com, docs.uipath.com, knowledge-base.rossum.ai, naps2.com). Only `WebSearch` result summaries were available, so every claim marked [n] comes from a search summary of the cited page, not from a full read. Material from general knowledge of the products is tagged "(unverified)". Exact pixel sizes of third-party UIs were not obtainable and are not invented. A follow-up pass with those hosts allowed should confirm the items listed under "Open verification items".

## TL;DR

- The strongest analogue for checking hundreds of pages is Lightroom Classic culling: grid for overview, one-key loupe for detail, single-key flags (P pick, X reject, U unflag), and auto-advance after each decision [1]. Kontrol should be built on this model.
- Every serious OCR/IDP verifier uses a "review only what is uncertain" queue: Acrobat's red-box "suspects" with Find Next Suspect [2], ABBYY FineReader's Verify Text dialog (skip, pick suggestion, add to dictionary) [3], and Google Document AI's review UI, which highlights below-threshold rows yellow, sorts them to the top and shows missing required fields in red [4]. Değerler should copy this.
- Confidence alone is not trustworthy. Acrobat users report "no suspects" for about 70% of files where they expected some [2]; an ABBYY-authored tutorial warns verification will not catch all errors because the engine can be confidently wrong [3]. Evrakçı must also offer a "check everything" path and spot-check sampling, not only a low-confidence queue.
- Review screens are dual-pane: extracted data on one side, the source document on the other, with hover or focus linking the field to its box on the page [4][5]. Tab / "next field" is the universal keyboard flow (Rossum, UiPath `n`, Docsumo Tab) [5].
- Microsoft's Office visual refresh hid the Quick Access Toolbar by default and moved common commands; after user feedback Microsoft reversed it in 2023 and turned the QAT back on [6]. Lesson: never hide frequent commands for visual calm.
- Acrobat's "new experience" moved tools to a left rail and thumbnails to a right panel; community threads complain about the forced thumbnail position and offer an opt-out ("Disable new Acrobat") [7]. Lesson: let users keep spatial habits; do not move panels between versions.
- Spectrum treats density as a first-class token axis ("compact" and "spacious" variants per size, e.g. `accordion-small-top-to-text-spacious` = 9px desktop / 12px mobile) and ships "medium" for desktop, "large" for touch [8]. Evrakçı should expose 2 or 3 sizes, not a continuum.
- Scanner front-ends (NAPS2) win on a flat toolbar (Scan, Import, Save PDF, OCR, Profiles) and saved scan profiles [9]; this is the model for Yükle.
- Pro tools (Resolve, Final Cut, Figma) separate "pages" or workspaces by task, and give a fast "Cut" workspace with an overview timeline above a zoomed detail timeline [10]. This maps to Kontrol's overview strip plus detail view.
- Progress, undo and batch actions must be visible at all times; nothing may be silently accepted (Evrakçı-specific, derived from the context brief).

## 1. Scanning and PDF tools

### Adobe Acrobat (2023+ "new experience")
- **Layout.** Adobe's help describes a quick-tools pane on the left (annotate, select, fill forms) plus a right rail whose top part handles bookmarks/page navigation and whose bottom part handles zoom and view options; thumbnails of all pages appear in a right panel; Organize Pages lives under Edit [7]. Sources disagree on exact placement, so check the live app (unverified).
- **Thumbnails and organise.** Page thumbnails with drag to reorder, rotate, delete, split and extract are the standard PDF vocabulary; Acrobat's version is the reference users already know (unverified in detail).
- **OCR verification.** "Enhance scans" has a Recognize text checkbox. After OCR, Correct Recognized Text marks doubtful words in red boxes; a "Review recognized text" box shows the suggested text, the user types or accepts, and Find Next Suspect moves on [2]. Users can double-click any word to make it a suspect manually [2].
- **Praised/criticised.** Criticism: forced right-side bookmarks/thumbnails and a changed layout [7]; "no suspects" results that do not match visible errors (about 70% of cases for one user) [2]; corrected text not appearing unless output style is changed [2]; manual suspect review impractical in big batches [2].
- **Takeaway.** The suspect model (box on the image, suggestion, accept, next) is right; the failure is trusting it exclusively. Provide "next uncertain" and "next unreviewed" separately.

### ABBYY FineReader PDF
- **Verification.** Recognize > Verify Text opens a dialog listing words containing low-confidence characters; the user picks a suggested replacement, edits, skips (which removes the highlight) or adds the word to the dictionary [3]. Uncertain characters are highlighted in the text window, and the highlight can be switched off in options [3].
- **Enterprise sibling.** FlexiCapture has a dedicated field verification window and hotkeys to jump to the next/previous low-confidence character [11] (details unverified, search summary only).
- **Criticism.** ABBYY's own tutorial says verification will not catch all errors because the OCR engine can be confident and wrong [3].
- **Takeaway.** Character-level highlighting inside the field (not just a red field border) tells the user which letter to look at; important for Turkish ı/İ, ş, ğ confusions (Evrakçı-specific inference).

### Adobe Scan, Kofax/Tungsten Power PDF, PaperPort, Readiris
No primary source could be read. From general knowledge (unverified): Adobe Scan is a phone app with auto-capture, edge detection and a post-capture crop/filter step; Power PDF and PaperPort are ribbon-based, with PaperPort showing a desktop of thumbnail "stacks"; Readiris is a ribbon app with a one-click output pipeline. None offers a keyboard-first, 100–800 page timeline; this gap is Evrakçı's niche.

### NAPS2 (open source)
- Flat toolbar: Scan, Import, Save PDF, Save Images, Email, Print, OCR, Profiles; saved profiles hold source, resolution, colour depth and format; Batch Scan sits under the Scan dropdown with an option to put every image from the batch into one file [9]. Command-line interface for automation [9]. Reports conflict on whether OCR is free (Tesseract-based, 60+ languages) [9] (unverified).
- **Takeaway.** Named scan profiles ("Belge, 300 dpi, gri, çift yüzlü") and a plain toolbar make a scanning front-end approachable. Yükle should use profiles, not a settings dialog.

## 2. Photo culling: Lightroom (Classic)
- **Keys.** P = Pick flag, X = Reject flag, U = unflag; Caps Lock or Photo > Auto Advance toggles automatic move to the next photo; reports on Shift behaviour conflict (suspends vs. forces advance), so verify in-app [1]. Shortcuts are remappable [1]. Adobe forum bug reports show how fragile localized shortcuts are: a Rotate Left default in Spanish, Italian and Swedish builds clashed with Shift+P [1]. Lesson: Turkish-layout keyboards must be tested, and shortcuts should not depend on shifted letters.
- **Views (unverified from memory):** G = Grid, E = Loupe, filmstrip along the bottom in every module, N = Survey, C = Compare; star ratings 1–5 and colour labels 6–9.
- **Why it fits Kontrol.** Culling 800 images is the same cognitive task as checking 800 page thumbnails: scan the grid, zoom on suspect items, mark decision, advance. Key properties: (a) the decision keys are single unshifted letters, (b) there is a persistent current-item highlight, (c) the filmstrip stays visible while zoomed, (d) filters on flag state ("show only rejected") exist.
- **Criticisms:** slow thumbnail/preview generation on large libraries (unverified); accidental flag toggles need undo, which Lightroom provides via Ctrl+Z.

## 3. Office: ribbon, Backstage, Quick Access, Fluent refresh
- Microsoft's Fluent/visual refresh simplified the ribbon, collapsed it by default in some apps (tabs only) and initially hid the Quick Access Toolbar [6].
- After feedback Microsoft reversed course in April 2023: commonly used commands returned to the QAT and the QAT became on by default in the Microsoft 365 visual refresh [6].
- Backstage (the File view) update status could not be confirmed [6].
- Excel review and data validation UX (unverified, general knowledge): red-triangle corner marks on suspicious cells, a Review tab with comments, and data validation circles ("Circle Invalid Data"). The pattern is a small corner mark rather than a blocking dialog.
- **Takeaway.** Keep a visible, user-pinnable strip of top actions (QAT-like) for Undo, Redo, Next problem. Do not collapse the main command bar by default for older users.

## 4. Document management: Paperless-ngx and DEVONthink
- **Paperless-ngx.** Documented concepts: an inbox tag that marks unprocessed documents, an inbox count in the sidebar (fixed in a release so it counts only inbox tags the user may see), bulk edit of tags and correspondents, a document detail page with side-by-side editing view, a global search and keyboard shortcuts added in a 2.x release [12]. Specific key bindings could not be retrieved.
- **DEVONthink.** A DEVONthink forum thread asks for keyboard-only inbox tagging, which shows users want to file inbox items without the mouse and that this was not smooth [13] (unverified beyond title).
- **Takeaway.** "Inbox" semantics: items needing a human are counted in a badge on the tab (Kontrol and Değerler badges). Bulk edit must be keyboard reachable.

## 5. Intelligent document processing validation screens
- **Rossum.** Validation screen with a top bar (zoom in/out/reset, search) and a customisable left sidebar; fields with low extraction confidence do not get the "tick" icon, so the user reviews only documents where a tick is missing or validation errors exist; confidence is stored per field (`rir_confidence`); shortcuts exist for header fields, tables and search, with Tab to next field [5].
- **Google Document AI HITL (deprecated after 2025-01-16, so legacy but instructive).** Rows below threshold highlighted yellow; low-confidence entities sorted to the top; missing required fields in red; hovering a field on the page highlights the matching row in the left panel; confidence 0–100 with per-field or per-document thresholds [4].
- **UiPath Validation Station / Docupath / Docsumo.** Dual-pane (extracted data left, source right) [5]; "n" to move to the next field (UiPath); Docsumo: Cmd+Shift+Enter confirm and save, Cmd+Shift+E edit fields, Tab to next, Shift+S split screen [5].
- **Nanonets, Hypatos, Docparser.** Public docs describe routing rules for low-confidence documents; no on-screen detail verified [4].
- **Takeaways.** (1) Show a three-state status per value: confirmed by person, suggested-and-high-confidence, uncertain/missing. (2) Make the "tick" meaning explicit: it must mean a human accepted, not that the machine is sure. (3) Sort or filter uncertain items first, but keep original order available. (4) Link table row and image region both ways.

## 6. Design-system and pro-tool layouts
- **Adobe Spectrum.** Density is a token dimension (`spacious`, `compact`) combined with size (small, medium, large) [8]; a layout token such as `accordion-small-top-to-text-spacious` has a desktop value of 9px and mobile 12px [8]; two scale sets, medium for desktop and large for touch [8]. Third-party analysis argues density is not size and a library needs two, at most three, sizes [8].
- **DaVinci Resolve.** Workspaces as "pages" (Cut, Edit, Colour, Deliver). Cut page has one viewer and two timelines (upper overview of the whole edit, lower precision view); Edit page has two viewers [10]. Both edit the same timeline [10].
- **Final Cut, Figma (unverified, general knowledge).** Final Cut: magnetic timeline, inspector right, browser left. Figma: layers left, canvas centre, properties right; UI3 shrinks chrome and floats the toolbar at the bottom. All three keep the inspector contextual to the selection.
- **Takeaway.** Overview timeline above detail view for Kontrol; a right-hand inspector that always shows the selected page's facts and actions.

## 7. Pattern library: pattern, where seen, how Evrakçı should use it

### Yükle (jobs and scan batches)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Flat toolbar with saved scan profiles | NAPS2 [9] | Big "Tara" and "İçe Aktar" buttons, profile dropdown; no settings dialog needed for daily work |
| Batch to one file option | NAPS2 batch scan [9] | Whole job is one batch; splitting happens later in Kontrol |
| Inbox badge for unprocessed items | Paperless-ngx [12] | Job list rows show "x sayfa kontrol bekliyor" counts |
| Per-job progress with named stage (Tarama, OCR, Bölme) | Acrobat Enhance scans, Resolve Deliver (unverified) | Row-level progress bar with stage text and page count, not a modal spinner |

### Kontrol (page-thumbnail timeline)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Grid to loupe in one key, filmstrip stays visible | Lightroom G/E [1] | Space or Enter toggles large preview; thumbnail strip never disappears |
| Single unshifted decision keys + auto-advance | Lightroom P/X/U, Caps Lock [1] | e.g. one key marks "belge burada başlıyor", one removes a cut; user-visible Auto-advance toggle |
| Overview timeline over detail timeline | Resolve Cut page [10] | Compact whole-job strip (colour per document) above the working thumbnails |
| Filter by state | Lightroom flag filters (unverified) | Filters: "ayırıcısı olmayan", "şüpheli", "elle kesilen" |
| Inspector for selection | Final Cut, Figma (unverified) | Right panel with page number, why split here (QR / filtre / elle), undo history |
| Red box on the image, then next suspect | Acrobat [2] | "Sonraki şüpheli" key jumps between uncertain splits |
| Page organise (reorder, rotate, delete) | Acrobat Organize Pages [7] | Keep standard drag/rotate/delete verbs and icons |

### Şablonlar (template editor)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Draw box on example page, named field list beside it | Rossum/Docsumo "Edit Fields" [5] | Canvas left, field list right; selecting either highlights the other |
| Contextual inspector | Figma properties panel (unverified) | Numeric position/size fields for exact tweaks, arrow-key nudging |
| Test on other pages | IDP training UIs | "Başka sayfada dene" button showing the box on 3 sample pages |

### Değerler (review table)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Uncertain first, yellow highlight, missing in red | Google Document AI [4] | Filter chip "Sadece belirsizler"; never colour alone, add icon and text |
| Dual-pane data and source with two-way hover linking | Document AI, Docupath, UiPath [4][5] | Table left, page crop right; selecting a cell scrolls the crop to the box |
| Tab / `n` next field, confirm shortcut | Rossum, UiPath, Docsumo [5] | Tab = next value, Enter = accept suggestion, plus "Sonraki belirsiz" key |
| Suggestion list with skip / add to dictionary | ABBYY Verify Text [3] | Per-cell suggestions; "sözlüğe ekle" for names (kurum, şahıs) |
| Character-level highlight | ABBYY [3] | Underline uncertain characters inside the cell text |
| Tick means a human accepted | Rossum tick icon [5] | Status column: Önerildi / Onaylandı / Düzeltildi / Eksik |
| Do not trust confidence alone | Acrobat 70% report [2], ABBYY note [3] | Provide "tümünü gözden geçir" mode and random spot-check of confirmed rows |

### Dışa Aktar (export)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Pre-flight summary before the irreversible step | Resolve Deliver (unverified), Office Backstage Print/Export | Checklist: x belge, y adsız, z belirsiz değer; export button disabled or warned if unresolved |
| Output profile | NAPS2 profiles [9] | Saved naming scheme and Excel columns |
| Progress with cancel and per-file result | Paperless-ngx consumption (unverified) | List of written files with open-folder link |

### Rehber (scanning guide)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Contextual help from the main task | Office help pane (unverified) | Each tab has "?" opening the relevant Rehber section; do not make the guide a separate world |
| Checklist with scan settings | Scanner software profiles [9] | Rehber ends with "Bu ayarı profil olarak kaydet" |

## Rules we should adopt for Evrakçı
1. Kontrol must have a one-key toggle between grid and large preview, and the thumbnail strip must remain visible in both states (Lightroom G/E model [1]). Test: from grid, one key press shows the loupe and the strip is still on screen.
2. Decision keys must be single, unshifted, remappable keys and must work on a Turkish Q keyboard; no shortcut may depend on a letter that Turkish locales remap [1]. Test: run the shortcut table on tr-TR layout.
3. Offer an Auto-advance toggle with a visible on/off state in the toolbar (Lightroom Caps Lock/Auto Advance [1]). Default off for destructive actions, on for "confirm".
4. Provide two separate jump commands: "Sonraki şüpheli" (machine flagged) and "Sonraki incelenmemiş" (human has not looked). Acrobat's "no suspects" failures [2] show the first alone is insufficient.
5. Every value and every split has a visible state from {önerildi, onaylandı, düzeltildi, eksik}; "onaylandı" is set only by a human action [5]. Export warns if any item is önerildi or eksik.
6. Değerler uses a dual-pane layout: table and page crop, with two-way linking (select cell scrolls crop; click box selects cell) [4][5].
7. Uncertain values are marked with icon plus text plus colour (never colour alone), sorted or filterable to top, and missing required values are visually distinct (Document AI: yellow below threshold, red for missing [4]).
8. In Değerler, Tab moves to next value, Enter accepts the suggestion and moves on, Esc reverts; one printed shortcut sheet is reachable from every tab [5].
9. Show uncertain characters inside a value (underline or tint) rather than only flagging the field (ABBYY [3]).
10. Provide a "tümünü incele" mode and a random spot-check of N confirmed rows before export, because confidence can be confidently wrong [2][3].
11. Keep a persistent top strip with Geri Al, Yinele, Sonraki şüpheli; do not hide it or collapse it by default (Microsoft's QAT reversal [6]).
12. Do not relocate panels between releases; allow the user to keep panel positions (Acrobat thumbnail complaint [7]).
13. Define exactly two or three density levels (e.g. Normal, Geniş, Çok geniş) rather than free scaling, following Spectrum's compact/spacious plus size model [8]; desktop mouse default must not be the touch-size scale.
14. Yükle uses named scan profiles and a flat toolbar with at most about 6 primary buttons (NAPS2 [9]).
15. Show an overview strip of the whole job above the working thumbnails, with documents colour-coded and the viewport indicated (Resolve Cut page [10]).
16. Show progress per job and stage with a count (page x of y); long operations never block the window.
17. Dışa Aktar opens with a pre-flight summary of counts (belge, belirsiz, eksik) before any file is written.

## Qt/PySide6 feasibility notes
- Grid/loupe/filmstrip: `QListView` in `IconMode` with a custom `QStyledItemDelegate` and lazily loaded thumbnails (`QThreadPool` + `QPixmapCache`) handles hundreds of items; the loupe is a `QGraphicsView` or custom widget. All standard Qt (general knowledge).
- Overview strip: a custom-painted `QWidget`; cheap to draw as coloured rectangles for 800 pages.
- Dual-pane review: `QSplitter` with `QTableView` (model/delegate for state icons) and a `QGraphicsView` crop; two-way linking via selection model signals.
- Shortcuts: `QShortcut`/`QAction` with `Qt.WidgetWithChildrenShortcut`; prefer `QKeySequence` by key code and test on tr-TR layout; provide user remapping stored in `QSettings`.
- Density tokens: central stylesheet or palette generator driven by a small token dictionary (size, density); Qt has no built-in density axis.
- Per-character highlight inside table cells: custom delegate with `QTextLayout` formats.

## Open verification items
Lightroom grid/loupe/survey/compare keys and ratings; Paperless-ngx shortcut list; Rossum full shortcut table; ABBYY FlexiCapture hotkeys; Spectrum exact control heights; Acrobat final thumbnail placement; NAPS2 OCR licensing; Resolve and Final Cut inspector specifics. These need the blocked hosts allowed or direct app inspection.

## Sources (accessed 2026-11-12 via search summaries; pages not fully read)
1. Lightroom Classic shortcut guides and Adobe community thread on Shift+P localization: https://fstoppers.com/lightroom/keyboard-shortcuts-actually-speed-lightroom-classic-718346 ; https://photofocus.com/photography/lightroom-shortcuts-for-faster-culling/ ; https://community.adobe.com/t5/lightroom-classic-discussions/shift-p-no-longer-picks-and-advances-in-es-it-and-sv/m-p/13011266
2. Adobe Acrobat OCR and suspects: https://helpx.adobe.com/bg/acrobat/desktop/create-documents/scan-documents-to-pdfs/enhance-scans.html ; https://blog.adobe.com/en/publish/2016/03/08/correcting-ocr-errors ; https://community.adobe.com/questions-18/correct-recognized-text-finds-no-suspects-only-in-random-files-593178
3. ABBYY FineReader checking text: https://help.abbyy.com/en-us/finereader/15/user_guide/checkingtext ; https://help.abbyy.com/en-us/finereader/16/user_guide/checkingtext
4. Google Document AI human review: https://docs.cloud.google.com/document-ai/docs/hitl/complete-review-task ; https://docs.cloud.google.com/document-ai/docs/hitl/whats-new ; Nanonets: https://docs.nanonets.com/docs/confidence-scores
5. Rossum https://knowledge-base.rossum.ai/docs/keyboard-shortcuts ; https://rossum.app/api/docs/openapi/guides/automation/ ; Docupath https://intercom.help/docupath/en/articles/15810167-using-the-dual-pane-review-screen ; UiPath https://docs.uipath.com/activities/other/latest/document-understanding/compact-validation-station ; Docsumo https://support.docsumo.com/docs/what-are-the-keyboard-shortcuts-that-i-can-use-on-the-edit-and-review-screen
6. Microsoft Office visual refresh and QAT: https://techcommunity.microsoft.com/blog/microsoft365insiderblog/quick-access-toolbar-on-by-default/4219349 ; https://betanews.com/2023/04/09/microsoft-bows-to-feedback-and-reverses-quick-access-toolbar-changes-in-office ; https://medium.com/microsoft-design/behind-the-design-refreshing-the-office-apps-for-windows-11-b9bfef5b9d3e
7. New Acrobat experience: https://experienceleague.adobe.com/en/docs/document-cloud-learn/acrobat-learning/getting-started/new-workspace ; https://helpx.adobe.com/au/document-cloud/help/new-acrobat-experience.html ; https://community.adobe.com/t5/acrobat-discussions/quot-new-acrobat-quot-bookmarks-thumbnails-now-forced-to-right-side-why/m-p/14030305
8. Adobe Spectrum: https://spectrum.adobe.com/page/design-tokens ; https://opensource.adobe.com/spectrum-design-data/tokens/layout-component ; https://eightshapes.com/articles/size-in-design-systems/ ; https://opensource.adobe.com/spectrum-web-components/tools/styles
9. NAPS2: https://www.naps2.com/doc/batch-scan ; https://thedigitalprojectmanager.com/tools/naps2-review/ ; https://www.linuxlinks.com/naps2-document-scanning-application/
10. DaVinci Resolve Cut page: https://mixinglight.com/color-tutorial/overview-resolve-16-cut-page ; https://forum.blackmagicdesign.com/viewtopic.php?p=735564 ; https://documents.blackmagicdesign.com/UserManuals/DaVinci-Resolve-17-Editors-Guide.pdf
11. ABBYY FlexiCapture verification: https://docs.abbyy.com/flexi-capture/interface/verificator-field-win ; https://help.abbyy.com/en-us/flexicapture/12/web_capture_station/hotkeys
12. Paperless-ngx: https://docs.paperless-ngx.com/usage ; https://www.github.com/paperless-ngx/paperless-ngx/releases?page=2
13. DEVONthink forum: https://discourse.devontechnologies.com/t/inbox-tagging-only-keyboard/53168
