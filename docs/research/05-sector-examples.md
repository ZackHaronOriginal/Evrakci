# 05 — Sector examples: how the best apps in and around our domain design their UI

**Research limits and verification status (second pass, 2026-11-12).** Despite the task note, in this session `WebFetch` still could not resolve helpx.adobe.com, spectrum.adobe.com, help.abbyy.com, docs.paperless-ngx.com, learn.microsoft.com or nngroup.com (`getaddrinfo ENOTFOUND`); only github.com and raw.githubusercontent.com were reachable. Evidence levels used below:
- **[F] full read**: raw source files read in full via GitHub (Spectrum token JSON, Paperless-ngx docs/source, NAPS2 resource strings and README).
- **[S] search-confirmed**: `WebSearch` restricted to the vendor domain returned a summary of the primary Adobe, ABBYY, Microsoft or NN/g page. This is a vendor page's content as summarised, not a full read; pixel sizes and exact button wording can still differ.
- **(unverified)**: no primary evidence in either pass. Items that stay unverified are listed in "Open verification items".
A "Verification log" at the end records what changed from the first draft.

## TL;DR

- The strongest analogue for checking hundreds of pages is Lightroom Classic culling: G grid, E/Space loupe, filmstrip always present, single-key flags (P pick, X reject, U unflag), and Shift+key to set a flag and advance to the next photo [1][S]. Kontrol should be built on this model.
- Every serious OCR/IDP verifier uses a "review only what is uncertain" queue: Acrobat's suspects (a "Recognized as" field and Accept, which jumps to the next suspect) [2][S], ABBYY's Verify Text dialog plus next/previous low-confidence word/character buttons in the Text pane [3][S], and Google Document AI's review UI (yellow below threshold, sorted first, missing required fields red) [4]. Değerler should copy this.
- Confidence alone is not trustworthy. A user reports "no suspects" in about 70% of files where errors were visible [2]; ABBYY's own tutorial warns verification misses confidently wrong output [3]; Excel validation likewise only fires on typed entry, not paste or fill [14][S]. Evrakçı needs a "check everything" path and spot-checks, not only a low-confidence queue.
- Review screens are dual-pane (data one side, source document other side) with Tab / "next field" navigation [5].
- Microsoft hid the Quick Access Toolbar in its visual refresh and reversed it in 2023 [6]. Ctrl+F1 and double-click on a tab collapse the ribbon [15][S]. Lesson: never hide frequent commands for visual calm.
- Acrobat's new experience: All Tools pane and Quick Action toolbar on the left, navigation pane (page thumbnails) on the right; Organize Pages sits under the Edit section of All Tools [7][S]. Users complained about the forced right-side thumbnails [7]. Lesson: do not move panels between versions.
- Spectrum density is a token axis, and it is now measurable [F]: a Medium table row is 32 px compact / 40 px regular / 48 px spacious on desktop, and the touch ("mobile") scale is about 1.25x [8]. Spacing tokens are static and do not scale [8][S].
- Scanner front-ends (NAPS2) win on a small toolbar (Scan, Batch Scan, Import, Save PDF, Email PDF, Print, OCR, Profiles), a "Customize Toolbar" command, and saved profiles that hold device and scan settings [9][F][S].
- Paperless-ngx shows bulk editing as a sticky edit bar (tag/correspondent/type/path/custom-field dropdowns on the left, actions on the right, red Delete) and a full hotkey set (A, P, O, Ctrl+arrows, Ctrl+Shift+S) with a Shift+? help dialog [12][F].
- Progress, undo and batch actions must be visible at all times; nothing may be silently accepted (Evrakçı-specific, derived from the context brief).

## 1. Scanning and PDF tools

### Adobe Acrobat (2023+ "new experience")
- **Layout [7][S].** Document view: document pane in the centre, All Tools pane and Quick Action toolbar on the left, navigation pane on the right. Page thumbnails open from the Page Thumbnails icon in the right navigation rail. The All Tools menu has an AI Assistant section and an Edit section; Edit contains Edit a PDF, Organize Pages, Add Rich Media and Prepare a Form. Known issue documented by Adobe: the left All Tools pane can open empty after an update, with "classic view" as workaround. (Correction: the earlier draft said the right rail's lower part held zoom and view options; not confirmed, dropped.)
- **Organize Pages on web [S].** Thumbnails of all pages; top bar with add, extract, rotate, delete and "design a new page" tools; hover on a thumbnail shows Rotate left, Rotate right and Delete; drag a thumbnail to reorder; plus icons between thumbnails insert pages; selected pages show a blue checkbox (used for extract); Undo is on the top bar.
- **Organize Pages on desktop [S].** Extract offers "delete pages after extracting" and "extract pages as separate files" (leave both unchecked to keep the original); deleting everything is not allowed (at least one page must remain); Split is a separate operation by maximum number of pages or maximum file size.
- **Scan & OCR [S].** Open file, All tools > Scan & OCR > Enhance scanned file, choose pages, dialog has a Recognize text checkbox.
- **OCR suspects [2][S].** All tools > Scan & OCR > Correct recognized text. Acrobat flags a word as suspect when it cannot confidently match the bitmap; the original image stays visible with searchable text hidden behind. Suspects are highlighted boxes on the page image; the dialog has a "Recognized as" field; the user edits it, compares to the image, and chooses Accept, after which Acrobat advances to the next suspect automatically; Close/Cancel ends the review. Correction: current help describes no separate "Find Next Suspect" button; that name comes from the 2016 Adobe blog [2]. Users can double-click any word to make it a suspect manually [2].
- **Praised/criticised.** Criticism: forced right-side bookmarks/thumbnails [7]; "no suspects" results that do not match visible errors (about 70% of cases for one user) [2]; corrected text not appearing unless output style is changed [2]; manual suspect review impractical in big batches [2].
- **Takeaway.** Suspect model (box on the image, editable field, Accept = commit + auto-advance) is right; the failure is trusting it exclusively. Provide "next uncertain" and "next unreviewed" separately.

### ABBYY FineReader PDF
- **Verify Text [3][S].** Dialog reached via Recognize > Verify Text (FineReader 14/15), via Tools > Verification (12), and via the Document tab's Recognize and Verify (16, per search summary). It lists words containing low-confidence characters, lets the user pick a suggested replacement, edit, skip, or add to the user dictionary.
- **Text pane [3][S].** Next/previous buttons jump to the next/previous low-confidence word or character; if low-confidence characters are not highlighted, a toolbar button at the top of the Text window turns highlighting on. Highlight is a user option.
- **Settings [3][S].** Verification thresholds for low-confidence characters live in the Options dialog; that tab is available only in the OCR Editor. Not confirmed from a full page: whether the Verify dialog itself highlights characters in the image.
- **Enterprise sibling.** FlexiCapture has a field verification window and hotkeys to jump between low-confidence characters [11] (unverified; not re-checked).
- **Criticism.** ABBYY's tutorial says verification will not catch all errors [3].
- **Takeaway.** Character-level highlight inside the text, with explicit next/previous-uncertain buttons, tells the user which letter to look at; important for Turkish ı/İ, ş, ğ confusions (Evrakçı inference).

### Adobe Scan, Kofax/Tungsten Power PDF, PaperPort, Readiris
No primary source read. General knowledge (unverified): Adobe Scan is a phone app with auto-capture and edge detection; Power PDF and PaperPort are ribbon-based; Readiris is a ribbon app with one-click output. None offers a keyboard-first 100–800 page timeline; this gap is Evrakçı's niche.

### NAPS2 (open source) [9]
- **Toolbar labels [F, UiStrings.resx].** Scan, Batch Scan, Import, Save PDF, Save Images, Save All / Save Selected, Email PDF, Print, OCR, Profiles, Settings; edit commands Rotate, Reorder, Delete, Crop, Flip, Deskew; menus Image, View, Tools, Help, Share; Undo / Redo with action names ("Undo {0}"); "Customize Toolbar" and a separate "Profiles toolbar" exist.
- **Shortcuts [F][S].** A "Keyboard Shortcuts" settings page with a Shortcut / Action / Assign / Unassign table, plus "Scan With Profile {0}" and "Scan With Default Profile" actions, so each profile can have a hotkey. Changelog mentions Ctrl+A select all thumbnails, Ctrl+S, Ctrl+O, Ctrl+Enter; the maintainer says the app has no help screen and shortcuts would be listed in Settings (GitHub issue 286).
- **Profiles [S].** A profile stores the scanner device and all scan settings; the CLI selects one with `-p`, default is the last used. Batch Scan sits under the Scan menu (since 4.6.0), with automatic, manual and duplex modes.
- **Thumbnails [S].** Scanned pages show as thumbnails in the main window; select and use menu buttons to rotate, flip, reorder, delete (Getting Started guide, old).
- **OCR [F][S].** Tesseract; GPL 2.0+; each OCR language is downloaded on demand ("Using OCR requires you to download each language", with estimated size shown); options "Automatically run OCR after scanning" and "Pre-emptively run OCR after scanning"; language and mode selectors. Correction: OCR is free/open source, the earlier "reports conflict" is resolved.
- **Platforms [F].** Windows 7+, macOS 10.15+, Linux; WIA, TWAIN, SANE, ESCL scanners.
- **Takeaway.** Named profiles with hotkeys, a customisable flat toolbar, and a visible "OCR after scanning" switch suit Yükle. Note NAPS2 has no built-in help and no discoverable shortcut list; Evrakçı should avoid that.

## 2. Photo culling: Lightroom Classic [1]
- **Views [S, Adobe shortcuts page].** E = Loupe, G = Grid, C = Compare, N = Survey; Space or E moves Grid to Loupe; G or Esc returns to Grid. Ctrl+Alt+1 opens Library. Ctrl+A selects all; Ctrl+Alt+A selects flagged photos.
- **Flags [S].** With a photo selected in Grid or Filmstrip: P = Pick, X = Reject, U = unflag.
- **Ratings and labels [S].** 1–5 set stars, 0 removes rating; 6–9 set colour labels (red, yellow, green, blue).
- **Auto-advance [S].** Adobe's table lists Shift+P, Shift+X, Shift+U and Shift+1–5 / 6–9 as "set and go to next photo". Correction: the first draft said Caps Lock; no Adobe page in the search mentioned Caps Lock, and no "Photo > Auto Advance" menu was confirmed, so both are (unverified). Community lore that Caps Lock toggles auto-advance is common but not confirmed here.
- **Localisation fragility [1].** A Spanish, Italian and Swedish bug made Shift+P stop picking and advancing because a Rotate Left default clashed. Lesson: shifted letters are fragile on non-US layouts; test on a Turkish layout.
- **Filmstrip/Workspace.** The Filmstrip is available in all modules (Adobe workspace page, summary) and filter bars filter by flag (unverified in detail).
- **Why it fits Kontrol.** Culling 800 images is the same task as checking 800 page thumbnails. Key properties: (a) single unshifted decision keys, (b) a separate "set and advance" variant, (c) persistent current-item highlight, (d) filmstrip visible while zoomed, (e) filters on flag state.

## 3. Office: ribbon, Backstage, Quick Access, Fluent refresh
- Microsoft's visual refresh simplified the ribbon, collapsed it by default in some apps and hid the Quick Access Toolbar [6]. After feedback Microsoft reversed it in 2023 and the QAT is on by default in the Microsoft 365 refresh [6].
- **Ribbon behaviour [15][S].** Ctrl+F1 expands/collapses the ribbon; double-click a tab or right-click > Collapse the Ribbon also works; the ribbon display options menu offers Show Tabs and Commands to keep it always visible. QAT is customised under File > Options > Quick Access Toolbar on Windows (Preferences on Mac). Keyboard access via Alt key tips is documented on Microsoft's ribbon keyboard page (not read in detail).
- **Backstage.** Could not be confirmed; no Microsoft page in the searches described it. (unverified)
- **Excel data validation [14][S].** Three parts: (1) an *input message*, shown when the cell is selected, title plus text up to 225 characters, intended to be switched off once users know the sheet; (2) an *error alert* with three styles: Stop (Retry/Cancel, blocks), Warning (user may accept, edit or remove), Information (user may accept or reject); (3) "Circle Invalid Data" (Data > Data Validation) which draws a red circle around existing invalid cells. Validation only fires on typed entry: paste, fill, formulas and macros bypass it. Error-checking indicators are green corner triangles on cells (detect-formula-errors page, summary only).
- **Takeaway.** Use the graded severity model (block / warn / inform) deliberately: Evrakçı should block only truly impossible export states, warn on uncertain values, inform on suggestions. The "bypass on paste" caveat means validation must also run on batch operations (accept-all) and at export. Keep a persistent top strip for Geri Al, Yinele, Sonraki şüpheli.

## 4. Document management: Paperless-ngx and DEVONthink [12]
- **Dashboard [F].** Shows no documents by default; the user adds saved views; upload button; drag files anywhere to consume.
- **Document list [F, source].** Filters (tags, correspondents, types), selection starts bulk-edit mode; click toggles selection, Shift-click selects a range; default display mode of a saved view is small cards (table and large cards also exist, template not read). Hotkeys: A select all, P select page, O open first selected (or first in list), Escape clears selection first then resets filters, Ctrl+Left/Right previous/next page.
- **Bulk editor bar [F, source].** A horizontal bar that wraps; left group "Edit:" with filterable dropdowns for Tags, Correspondent, Document type, Storage path, Custom fields (with Set values), and Permissions; right group (pushed right) Actions (Reprocess, Rotate, Merge, Merge as versions), Send (share link bundle, email), Download with options (archived, original, formatted filename), and a red Delete button. Items are shown only if permitted and enabled only with valid selection.
- **Document detail [F, source].** Tabs: Details, Content, Metadata, Preview, Notes, Permissions, History, Duplicates (some conditional). Hotkeys: Ctrl+Right/Left next/previous document, Esc close, Ctrl+S save, Ctrl+Shift+S save and go to next (or close if none). This "save and next" is a direct model for Değerler.
- **Inbox [F].** Docs have no dedicated inbox section: an inbox tag is assigned to new documents and removed after processing; suggestions are fetched automatically when opening a document that still has the inbox tag (can be disabled in Settings > Documents). The sidebar inbox count fix is from release notes (unverified, not re-read).
- **Help and search [F].** Shift+? opens a help dialog listing only hotkeys valid for the current area. Global search covers documents, tags and workflows.
- **DEVONthink.** A forum thread asks for keyboard-only inbox tagging [13] (unverified beyond title).
- **Takeaway.** "Inbox" semantics via a badge; bulk-edit as a sticky bar; context-sensitive shortcut help (Shift+?) reachable on every screen; "save and next" as one key.

## 5. Intelligent document processing validation screens
- **Rossum.** Top bar (zoom, search), customisable left sidebar; fields with low confidence do not get the tick icon; confidence stored per field; shortcuts for header, tables, search; Tab to next field [5].
- **Google Document AI HITL (deprecated after 2025-01-16).** Rows below threshold yellow; low-confidence sorted first; missing required fields red; hovering a field on the page highlights the matching row; confidence 0–100 with thresholds [4].
- **UiPath / Docupath / Docsumo.** Dual-pane review [5]; "n" for next field (UiPath); Docsumo Cmd+Shift+Enter confirm and save, Cmd+Shift+E edit fields, Tab next, Shift+S split screen [5].
- **Nanonets, Hypatos, Docparser.** Routing rules for low-confidence documents; no on-screen detail verified [4].
- **Takeaways.** (1) Three-state status per value. (2) Tick means a human accepted. (3) Sort/filter uncertain first but keep original order available. (4) Link table row and image region both ways.

## 6. Design-system and pro-tool layouts
- **Adobe Spectrum tokens [8][F].** The repository `adobe/spectrum-tokens` is now a redirect; tokens live in `adobe/spectrum-design-data` (`packages/tokens/src/*.json`). Values below are read from those files; desktop vs mobile ("scale sets") is the platform axis, compact/regular/spacious the density axis. The Spectrum site states spacing values are static and do not change with platform scale, and that the desktop scale covers UWP, macOS and web desktop while the mobile scale covers iOS, Android and web mobile [8][S].

| Token | Desktop | Mobile |
|---|---|---|
| component-height-50 | 20 | 26 |
| component-height-75 | 24 | 30 |
| component-height-100 | 32 | 40 |
| component-height-200 | 40 | 50 |
| component-height-300 | 48 | 60 |
| font-size-50 / 75 / 100 / 200 / 300 | 11 / 12 / 14 / 16 / 18 | 13 / 15 / 17 / 19 / 22 |
| line-height for those sizes | 14 / 16 / 18 / 20 / 22 | 16 / 20 / 22 / 24 / 26 |
| line-height multipliers | 1.3 and 1.5 | same |
| spacing-50, 75, 85, 100, 200, 300, 350, 400, 500, 600 | 2, 4, 6, 8, 12, 16, 20, 24, 32, 40 | same (static) |
| list-view minimum height | 40 | 50 |
| list-view minimum width | 200 | 240 |
| table-section-header-row-height S / M / L / XL | 24 / 32 / 40 / 48 | 30 / 40 / 50 / 60 |
| thumbnail-size-50 ... 1000 | 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 64 | 20 ... 72 |

  Table row heights (desktop px; mobile is about 1.25x):

| Size | Compact | Regular | Spacious |
|---|---|---|---|
| Small | 24 | 32 | 40 |
| Medium | 32 | 40 | 48 |
| Large | 40 | 48 | 56 |
| Extra large | 48 | 56 | 64 |

  Compact row heights are aliases of component-height tokens (small-compact = component-height-75, medium = 100, large = 200, XL = 300). Tab items follow the same pattern (compact medium tab = component-height-100 = 32 px; regular medium tab = component-height-300 = 48 px). Edge-to-text padding at desktop: 8 / 9 / 12 / 15 / 18 px for sizes 50 to 300; spacing between tab items 21–30 px; tab focus indicator gap 7–10 px. The previously quoted `accordion-small-top-to-text-spacious` 9/12 px was not re-verified (unverified). The first draft's statement that Spectrum "ships medium for desktop, large for touch" is better stated as: one token set with a desktop value and a mobile value (about 1.25x).
  Third-party analysis (EightShapes) argues density is not size and a library needs two, at most three, sizes [8].
- **DaVinci Resolve.** Workspaces as pages; Cut page has one viewer and two timelines (upper overview, lower precision) [10] (not re-checked).
- **Final Cut, Figma (unverified).** Inspector contextual to selection.
- **Takeaway.** Overview strip above detail view for Kontrol; right-hand inspector that shows facts and actions for the selected page.

## 7. Pattern library: pattern, where seen, how Evrakçı should use it

### Yükle (jobs and scan batches)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Flat toolbar with saved scan profiles that hold device and settings | NAPS2 [9][F][S] | Big "Tara" and "İçe Aktar" buttons, profile dropdown; no settings dialog for daily work |
| Hotkey per profile ("Scan With Profile n") | NAPS2 shortcuts page [9][F] | Number keys start the matching profile; visible in the profile list |
| Visible "OCR after scanning" switch with language chosen once | NAPS2 OCR setup [9][F] | Per-job OCR toggle and language shown in the job row |
| Batch to one file | NAPS2 Batch Scan [9][S] | Whole job is one batch; splitting happens later in Kontrol |
| Drop files anywhere to start consumption | Paperless-ngx dashboard [12][F] | Whole window is a drop target; job appears at once |
| Inbox badge for unprocessed items | Paperless-ngx [12] | Job rows show "x sayfa kontrol bekliyor" |
| Per-job progress with named stage | Acrobat Enhance scans (unverified), Resolve Deliver (unverified) | Row-level progress bar with stage text and page count |
| Customisable toolbar, shortcuts table with Assign/Unassign | NAPS2 [9][F] | Remappable shortcuts in Ayarlar; plus a built-in help list (NAPS2 lacks one) |

### Kontrol (page-thumbnail timeline)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Grid to loupe in one key (Space/E), G or Esc back, filmstrip stays | Lightroom [1][S] | Space toggles large preview; Esc returns; strip never disappears |
| Single unshifted decision keys plus a "set and advance" variant | Lightroom P/X/U and Shift+key [1][S] | One key marks "belge burada başlıyor", one removes a cut; Shift variant advances; visible Auto-advance state |
| Ratings 0–5 and colour labels 6–9 on number keys | Lightroom [S] | Optional: number keys for page tags (e.g. boş sayfa, ayırıcı) |
| Overview timeline over detail timeline | Resolve Cut page [10] | Compact whole-job strip (colour per document) above working thumbnails |
| Filter by state | Lightroom flag filters (unverified) | Filters: "ayırıcısı olmayan", "şüpheli", "elle kesilen" |
| Inspector for selection | Final Cut, Figma (unverified) | Right panel: page number, why split here (QR / filtre / elle), undo history |
| Highlighted box on the image, edit, Accept = commit and jump to next | Acrobat suspects [2][S] | "Sonraki şüpheli" jumps; confirming advances automatically |
| Hover actions on thumbnails, plus icons between thumbnails for insert | Acrobat Organize Pages (web) [7][S] | Hover: döndür / sil; "+" or scissors between thumbnails to add a cut |
| Blue checkbox on selected thumbnails; Undo in top bar | Acrobat Organize Pages [7][S] | Multi-select with visible check; Geri Al in the persistent strip |
| Cannot delete everything | Acrobat desktop [S] | Disallow removing the last page of a document |
| Click selects, Shift-click range, A all, Esc clears selection first | Paperless-ngx list [12][F] | Same selection model for page thumbnails |
| Bulk bar appears when selection exists | Paperless-ngx [12][F] | Sticky bar with bulk actions (birleştir, sil, döndür) when pages are selected |
| Thumbnails with rotate / flip / reorder / delete buttons | NAPS2 [9][S] | Keep standard verbs and icons |

### Şablonlar (template editor)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Draw box on example page, named field list beside it | Rossum/Docsumo "Edit Fields" [5] | Canvas left, field list right; selecting either highlights the other |
| Contextual inspector | Figma (unverified) | Numeric position/size fields, arrow-key nudging |
| Tabbed detail with conditional tabs | Paperless-ngx document detail [12][F] | Show only the tabs that apply (alanlar, test, geçmiş) |
| Test on other pages | IDP training UIs | "Başka sayfada dene" showing the box on 3 sample pages |

### Değerler (review table)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Uncertain first, yellow highlight, missing in red | Document AI [4] | Filter chip "Sadece belirsizler"; never colour alone, add icon and text |
| Dual-pane data and source with two-way hover linking | Document AI, Docupath, UiPath [4][5] | Table left, page crop right; selecting a cell scrolls the crop to its box |
| Tab / `n` next field | Rossum, UiPath, Docsumo [5] | Tab = next value, Enter = accept, plus "Sonraki belirsiz" key |
| "Recognized as" editable field plus Accept that auto-advances | Acrobat Correct recognized text [2][S] | Edit-in-place cell; Enter accepts and jumps to next uncertain |
| Save and go to next (Ctrl+Shift+S), Ctrl+Left/Right previous/next | Paperless-ngx detail [12][F] | Same pair in Değerler: "kaydet ve sonrakine geç" |
| Suggestions with skip / add to dictionary | ABBYY Verify Text [3][S] | Per-cell suggestions; "sözlüğe ekle" for names |
| Character-level highlight with next/previous-uncertain buttons and toggle | ABBYY Text pane [3][S] | Underline uncertain characters in the cell text; toggle the highlight |
| Thresholds in settings, not in the work screen | ABBYY Options [3][S] | "Belirsizlik eşiği" in Ayarlar only |
| Input message on focus, graded alerts Stop / Warning / Information | Excel data validation [14][S] | Format hint on cell focus (e.g. tarih GG.AA.YYYY, max about 225 chars); block impossible, warn doubtful, inform suggestion |
| "Circle invalid data" report across the sheet | Excel [14][S] | Button "Tüm hatalı değerleri işaretle" before export |
| Validation bypassed by paste/fill | Excel [14][S] | Run the same checks after accept-all / paste-column and at export |
| Tick means a human accepted | Rossum [5] | Status column: Önerildi / Onaylandı / Düzeltildi / Eksik |
| Suggestions fetched when opening an item that is still in inbox | Paperless-ngx [12][F] | Compute suggestions lazily on opening an unreviewed row |
| Context-sensitive shortcut dialog (Shift+?) | Paperless-ngx [12][F] | "?" shows only the keys valid for the current tab |
| Do not trust confidence alone | Acrobat 70% report [2], ABBYY [3] | "Tümünü gözden geçir" mode and random spot-check of confirmed rows |

### Dışa Aktar (export)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Pre-flight summary before the irreversible step | Resolve Deliver (unverified), Office Backstage (unverified) | Checklist: x belge, y adsız, z belirsiz değer; export disabled or warned if unresolved |
| Output profile / saved settings | NAPS2 profiles [9][S] | Saved naming scheme and Excel columns |
| Download options as checkbox menu (archived / original / formatted filename) | Paperless-ngx bulk bar [12][F] | Checkbox options next to the export button |
| Red destructive button only when allowed | Paperless-ngx [12][F] | Only one red button on screen; overwrite requires confirmation |
| Progress with cancel and per-file result | Paperless-ngx consumption (unverified) | List of written files with open-folder link |

### Rehber (scanning guide)
| Pattern | Where seen | Use in Evrakçı |
|---|---|---|
| Contextual help from the main task | Paperless-ngx Shift+? dialog [12][F] | "?" opens the relevant Rehber section and the tab's shortcut list |
| Input message that can be switched off once learned | Excel [14][S] | Hints dismissible per user ("bir daha gösterme") |
| Checklist with scan settings | Scanner profiles [9] | Rehber ends with "Bu ayarı profil olarak kaydet" |

## Rules we should adopt for Evrakçı
1. Kontrol must have a one-key toggle between grid and large preview (Space), with Esc to return, and the thumbnail strip must remain visible in both states (Lightroom G/E/Space [1][S]). Test: from grid, one key press shows the loupe and the strip is still on screen.
2. Decision keys must be single, unshifted, remappable keys that work on a Turkish Q keyboard; "set and advance" is a separate, visible variant (Lightroom P/X/U versus Shift+key [S]). Because shifted letters broke in Spanish, Italian and Swedish builds [1], no shortcut may rely on a shifted letter alone. Test: run the shortcut table on tr-TR layout.
3. Provide an Auto-advance toggle with visible on/off state in the toolbar. Default off for destructive actions, on for "confirm". (Lightroom's Caps Lock mechanism is not confirmed; do not copy it.)
4. Provide two separate jump commands: "Sonraki şüpheli" (machine flagged) and "Sonraki incelenmemiş" (human has not looked) [2].
5. Every value and split has a visible state from {önerildi, onaylandı, düzeltildi, eksik}; "onaylandı" is set only by a human action [5]. Export warns on any önerildi or eksik item.
6. Değerler uses a dual-pane layout with two-way linking (select cell scrolls crop; click box selects cell) [4][5].
7. Uncertain values are marked with icon plus text plus colour, sortable/filterable to top; missing required values are visually distinct (Document AI [4]).
8. In Değerler, Tab = next value, Enter = accept and move on to the next uncertain value (Acrobat Accept [2][S]), Esc reverts, a "save and next" key pair exists (Paperless Ctrl+Shift+S [12][F]); "?" shows only the shortcuts valid on the current tab (Paperless Shift+? [12][F]).
9. Show uncertain characters inside a value (underline or tint) with next/previous-uncertain-character keys and a highlight toggle (ABBYY [3][S]).
10. Provide "tümünü incele" mode and a random spot-check of N confirmed rows before export [2][3].
11. Keep a persistent top strip with Geri Al, Yinele, Sonraki şüpheli; never hide or collapse it by default (QAT reversal [6]); offer Ctrl+F1-style collapse only as an option the user chooses [15][S].
12. Do not relocate panels between releases; let users keep panel positions [7].
13. Define exactly three density levels with measured row heights following Spectrum's table model, e.g. Sıkı 32 px, Normal 40 px, Geniş 48 px for table rows at medium size (Spectrum compact/regular/spacious [8][F]); text scales separately from row height; spacing tokens stay fixed. Default for this audience is Normal or Geniş, not Sıkı. Test: row heights match the table at each density.
14. Yükle uses named scan profiles (stored device + settings), one hotkey per profile, a flat toolbar of at most about 8 buttons (NAPS2 has 8–10) and a "Customize toolbar" option [9][F].
15. Show an overview strip of the whole job above the working thumbnails, documents colour-coded, viewport indicated [10].
16. Show progress per job and stage with a count (page x of y); long operations never block the window.
17. Dışa Aktar opens with a pre-flight summary (belge, belirsiz, eksik) before any file is written.
18. Use graded severity in checks: block (export impossible), warn (uncertain value, user may continue after confirming), inform (suggestion); every check must also run after bulk operations and at export, because validation that runs only on typed entry is bypassed by paste/fill [14][S].
19. Provide a selection model like Paperless-ngx: click toggles, Shift-click ranges, A selects all, Esc clears selection first, then filters; a bulk bar appears only while a selection exists [12][F].
20. Never allow a state that removes every page of a document silently (Acrobat blocks deleting all pages [S]); show an inline message instead.
21. Provide a built-in shortcut list reachable from every tab; do not repeat NAPS2's gap of having no in-app list [9][S].

## Qt/PySide6 feasibility notes
- Grid/loupe/filmstrip: `QListView` in `IconMode` with a custom `QStyledItemDelegate` and lazily loaded thumbnails (`QThreadPool` + `QPixmapCache`) handles hundreds of items; the loupe is a `QGraphicsView` or custom widget (general knowledge).
- Overview strip: a custom-painted `QWidget`; cheap to draw as coloured rectangles for 800 pages.
- Dual-pane review: `QSplitter` with `QTableView` (model/delegate for state icons) and a `QGraphicsView` crop; two-way linking via selection model signals.
- Shortcuts: `QShortcut`/`QAction` with `Qt.WidgetWithChildrenShortcut`; test on tr-TR layout; user remapping in `QSettings`, with an Assign/Unassign table like NAPS2.
- Density tokens: a small token dictionary (size, density) generating a stylesheet; row heights set via `QHeaderView.setDefaultSectionSize` and delegate `sizeHint`. Qt has no built-in density axis.
- Per-character highlight inside table cells: custom delegate with `QTextLayout` formats.
- Input message / graded alerts: `QToolTip` or an inline label under the editor, `QValidator` for block level; warn level via a delegate flag, not a modal dialog.
- Bulk bar: a `QToolBar` or `QFrame` inside a `QStackedLayout` shown on non-empty selection.

## Open verification items
Still (unverified) because hosts were unreachable via WebFetch: Lightroom Caps Lock / Photo > Auto Advance; Filmstrip and flag filter specifics; exact Acrobat dialog layout and pixel sizes; ABBYY Verify Text window layout and whether the dialog marks characters in the image; ABBYY FlexiCapture hotkeys; Backstage; Spectrum site text on density (tokens verified, prose not); `accordion-small-top-to-text-spacious` values; Paperless-ngx table view and inbox-count behaviour; Rossum shortcut table; Resolve and Final Cut specifics; NN/g guidance on density, keyboard and confirmations (searches only returned sticky-header and table articles). Re-run once helpx.adobe.com, help.abbyy.com, learn.microsoft.com, spectrum.adobe.com and nngroup.com resolve from WebFetch.

## Verification log
Date 2026-11-12. Method: WebFetch on github hosts (full read), WebSearch restricted to vendor domains (summary only).
- **Network:** helpx.adobe.com, help.abbyy.com, docs.paperless-ngx.com, spectrum.adobe.com, learn.microsoft.com failed DNS (`ENOTFOUND`) in WebFetch although the task said they were allowed; github.com and raw.githubusercontent.com worked. The `mcp__github__*` tools refused repos other than zackharonoriginal/evrakci.
- **Confirmed [F]:** Spectrum heights, fonts, spacing, table row heights by density, tab, list-view and thumbnail tokens (adobe/spectrum-design-data); Paperless-ngx docs/usage.md, document-list and document-detail component sources, bulk-editor template; NAPS2 README and UiStrings.resx.
- **Confirmed [S]:** Lightroom views, flags, ratings, labels, Shift auto-advance; Acrobat new layout, Organize Pages (web and desktop), Enhance scans, Correct recognized text; ABBYY Verify and Text pane controls; Excel data validation; ribbon Ctrl+F1; NAPS2 profiles, shortcuts, batch scan; NN/G sticky headers/tables.
- **Corrected:**
  1. Lightroom auto-advance: Shift+P/X/U (and Shift+number) per Adobe; Caps Lock claim downgraded to (unverified). Resolved the "Shift behaviour conflicts" note.
  2. Acrobat: "Find Next Suspect" button not in current help; Accept auto-advances; right rail zoom/view-options claim dropped; Organize Pages is under Edit in All Tools.
  3. Spectrum: replaced vague density description with exact token values; noted `spectrum-tokens` repo is a redirect to `spectrum-design-data`; "medium desktop / large touch" restated as desktop/mobile token sets (about 1.25x); spacing is static.
  4. NAPS2: OCR is Tesseract, GPL, languages downloaded on demand (conflict resolved); added full toolbar label list, customizable toolbar, shortcut table, profile hotkeys.
  5. Paperless-ngx: confirmed there is no dedicated inbox UI in the docs, only a tag; added hotkeys, bulk bar layout, detail tabs, Shift+? help.
  6. Excel: replaced "red-triangle corner marks" claim with the documented model (input message, three alert styles, red circles for invalid data; green triangles belong to error checking).
- **Added:** rules 18–21, density row-height table, Excel/Paperless/NAPS2 patterns in every tab's pattern table, selection model and bulk bar.
- **Not verified / still open:** see "Open verification items".

## Sources (accessed 2026-11-12; [F] full read, [S] search summary of the vendor page, otherwise first-pass summary)
1. Lightroom Classic shortcuts and flagging [S]: https://helpx.adobe.com/lightroom-classic/desktop/introduction-to-lightroom-classic/keyboard-shortcuts.html ; https://helpx.adobe.com/lightroom-classic/help/flag-label-rate-photos.html ; https://helpx.adobe.com/lightroom-classic/desktop/workspace/workspace-basics.html ; shortcut guides https://fstoppers.com/lightroom/keyboard-shortcuts-actually-speed-lightroom-classic-718346 ; https://photofocus.com/photography/lightroom-shortcuts-for-faster-culling/ ; Shift+P localisation bug https://community.adobe.com/t5/lightroom-classic-discussions/shift-p-no-longer-picks-and-advances-in-es-it-and-sv/m-p/13011266
2. Acrobat OCR and suspects [S]: https://helpx.adobe.com/acrobat/desktop/create-documents/scan-documents-to-pdfs/fix-scanned-text.html ; https://helpx.adobe.com/acrobat/desktop/create-documents/scan-documents-to-pdfs/recognize-text.html ; https://helpx.adobe.com/acrobat/desktop/create-documents/scan-documents-to-pdfs/enhance-scans.html ; https://blog.adobe.com/en/publish/2016/03/08/correcting-ocr-errors ; https://community.adobe.com/questions-18/correct-recognized-text-finds-no-suspects-only-in-random-files-593178
3. ABBYY checking text [S]: https://help.abbyy.com/en-us/finereader/14/user_guide/checkingtext/ ; https://help.abbyy.com/en-us/finereader/15/user_guide/checkingtext ; https://help.abbyy.com/en-us/finereader/16/user_guide/checkingtext
4. Google Document AI human review: https://docs.cloud.google.com/document-ai/docs/hitl/complete-review-task ; https://docs.cloud.google.com/document-ai/docs/hitl/whats-new ; Nanonets https://docs.nanonets.com/docs/confidence-scores
5. Rossum https://knowledge-base.rossum.ai/docs/keyboard-shortcuts ; Docupath https://intercom.help/docupath/en/articles/15810167-using-the-dual-pane-review-screen ; UiPath https://docs.uipath.com/activities/other/latest/document-understanding/compact-validation-station ; Docsumo https://support.docsumo.com/docs/what-are-the-keyboard-shortcuts-that-i-can-use-on-the-edit-and-review-screen
6. Microsoft Office visual refresh and QAT: https://techcommunity.microsoft.com/blog/microsoft365insiderblog/quick-access-toolbar-on-by-default/4219349 ; https://betanews.com/2023/04/09/microsoft-bows-to-feedback-and-reverses-quick-access-toolbar-changes-in-office ; https://medium.com/microsoft-design/behind-the-design-refreshing-the-office-apps-for-windows-11-b9bfef5b9d3e
7. New Acrobat experience and Organize Pages [S]: https://helpx.adobe.com/acrobat/using/new-acrobat-experience.html ; https://helpx.adobe.com/acrobat/desktop/get-started/learn-the-basics/workspace.html ; https://helpx.adobe.com/acrobat/web/edit-pdfs/organize-documents/organize-pages.html ; https://helpx.adobe.com/acrobat/desktop/edit-documents/organize-pages/extract-pages.html ; https://helpx.adobe.com/acrobat/desktop/edit-documents/organize-pages/delete-pages.html ; complaint thread https://community.adobe.com/t5/acrobat-discussions/quot-new-acrobat-quot-bookmarks-thumbnails-now-forced-to-right-side-why/m-p/14030305
8. Adobe Spectrum: [F] https://raw.githubusercontent.com/adobe/spectrum-design-data/main/packages/tokens/src/layout.json ; .../typography.json ; .../table.json ; .../tabs.json ; .../list-view.json ; .../thumbnail.json ; https://github.com/adobe/spectrum-tokens (redirect notice). [S] https://spectrum.adobe.com/page/spacing/ ; https://spectrum.adobe.com/page/design-tokens ; https://spectrum.adobe.com/page/coach-mark/ ; EightShapes https://eightshapes.com/articles/size-in-design-systems/
9. NAPS2: [F] https://github.com/cyanfish/naps2 ; https://raw.githubusercontent.com/cyanfish/naps2/master/README.md ; https://raw.githubusercontent.com/cyanfish/naps2/master/NAPS2.Lib/Lang/Resources/UiStrings.resx . [S] https://www.naps2.com/doc/getting-started ; https://www.naps2.com/doc/command-line ; https://github.com/cyanfish/naps2/blob/master/CHANGELOG.md ; https://github.com/cyanfish/naps2/issues/286 ; https://www.naps2.com/doc/batch-scan
10. DaVinci Resolve Cut page: https://mixinglight.com/color-tutorial/overview-resolve-16-cut-page ; https://forum.blackmagicdesign.com/viewtopic.php?p=735564 ; https://documents.blackmagicdesign.com/UserManuals/DaVinci-Resolve-17-Editors-Guide.pdf
11. ABBYY FlexiCapture: https://docs.abbyy.com/flexi-capture/interface/verificator-field-win ; https://help.abbyy.com/en-us/flexicapture/12/web_capture_station/hotkeys
12. Paperless-ngx [F]: https://raw.githubusercontent.com/paperless-ngx/paperless-ngx/dev/docs/usage.md ; https://raw.githubusercontent.com/paperless-ngx/paperless-ngx/dev/src-ui/src/app/components/document-list/document-list.component.ts ; https://raw.githubusercontent.com/paperless-ngx/paperless-ngx/dev/src-ui/src/app/components/document-detail/document-detail.component.ts ; https://raw.githubusercontent.com/paperless-ngx/paperless-ngx/dev/src-ui/src/app/components/document-list/bulk-editor/bulk-editor.component.html ; releases https://www.github.com/paperless-ngx/paperless-ngx/releases?page=2
13. DEVONthink forum: https://discourse.devontechnologies.com/t/inbox-tagging-only-keyboard/53168
14. Excel data validation [S]: https://support.microsoft.com/en-us/excel/get-started/apply-data-validation-to-cells ; https://support.microsoft.com/en-us/excel/display-or-hide-circles-around-invalid-data ; https://support.microsoft.com/en-us/excel/more-on-data-validation ; https://learn.microsoft.com/en-us/office/vba/api/excel.xldvalertstyle
15. Ribbon and QAT behaviour [S]: https://support.microsoft.com/en-us/office/foundations-experiences/customize-the-ribbon-in-office ; https://support.microsoft.com/en-us/accessibility/excel/keyboard-shortcuts-in-excel ; https://support.microsoft.com/en-us/accessibility/windows/use-the-keyboard-to-work-with-the-ribbon
16. NN/G [S]: https://www.nngroup.com/articles/data-tables/ ; https://www.nngroup.com/articles/sticky-headers/ ; https://www.nngroup.com/articles/mobile-tables/
