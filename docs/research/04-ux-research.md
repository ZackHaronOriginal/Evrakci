# 04 - UX research and usability evidence for Evrakçı

Scope: usability evidence applicable to a dense, keyboard-heavy, Turkish-language Qt desktop tool used in long sessions by older, non-technical staff.

**Verification note.** The research session's network allowlist blocked direct fetches of nngroup.com and w3.org (DNS failure). Only one web search succeeded (WCAG 2.5.8, via secondary sources). Everything else below is from well-established published guidance known to the author, cited to its primary source URL but **not re-fetched on the access date**. Items where I am unsure of exact numbers are marked "(unverified)". The access date for all sources is 2026-11-12 (search only for [5]); a follow-up pass should re-fetch the primary pages once nngroup.com and w3.org are allowed.

## TL;DR

- Response time: 0.1 s feels instant, 1 s keeps the flow of thought, 10 s is the attention limit. Over 1 s show feedback; over ~10 s show a determinate progress bar with time remaining and allow cancel [1].
- WCAG 2.2 AA pointer targets: at least 24x24 CSS px (or spacing so a 24 px circle does not overlap neighbours) [5]. For older users aim much higher (about 32-40 px on desktop for primary controls; AAA 2.5.5 says 44 px) [2][6].
- Fitts's law: time grows with distance/size ratio; large, near, edge-anchored targets win. Keep frequent actions big and close to where the eye/hand already is [7].
- Hick's law: choice time grows logarithmically with the number of options; show few primary actions, push rare ones into menus [7].
- Automation UX: staff reviewing machine output suffer complacency and automation bias. Mark uncertain OCR values visibly, make review exception-based but with sampling of "confident" items, and never auto-accept silently [8][9].
- Prefer undo over confirmation dialogs; use confirmation only for irreversible actions, with specific verbs on the buttons [3].
- Keyboard-first: every action reachable by keyboard, visible shortcut hints, logical focus order, no hidden modes, never rely on Turkish-specific characters in shortcuts [10][11].
- Accessibility floor: text contrast 4.5:1, non-text/UI contrast 3:1 (1.4.11), focus never fully hidden (2.4.11 AA), focus indicator at least 2 CSS px perimeter and 3:1 change (2.4.13 is AAA, adopt voluntarily) [4][6].
- Older adults: bigger text, bigger targets, explicit labels, fewer hidden interactions; NN/g found seniors perform measurably worse on tasks with small, ambiguous UIs [2].
- Turkish: casing must be locale-aware (I/ı, İ/i), text grows ~20-30% versus English (rule of thumb), and Turkish Q and F keyboards differ so shortcut letters need care.

## 1. Nielsen's 10 heuristics applied to Evrakçı [12]

1. **Visibility of system status.** Every tab shows job state: scan imported (n/total pages), OCR running (page k of n), split pending review, export complete. A persistent status strip shows the current job, unsaved/saved state and background tasks.
2. **Match with the real world.** Use office vocabulary (evrak, tutanak, dosya, sayfa), not technical terms (OCR, regex, bounding box). The "Değerler" table should mirror the paper form's field names.
3. **User control and freedom.** Undo/redo in Kontrol exists; extend to Değerler edits and template changes. Always provide a way out of a modal state (Esc).
4. **Consistency and standards.** Same shortcut and same verb for the same action across tabs; follow Windows conventions (Ctrl+Z, F2 to edit cell, Enter to commit, Esc to cancel, F6 for pane switching).
5. **Error prevention.** Block export while unresolved items remain, or state the count; prevent duplicate names; disable impossible actions rather than erroring.
6. **Recognition rather than recall.** Show the page image next to the value being verified; show shortcut hints in tooltips and button labels; the Rehber is available contextually, not just as a tab.
7. **Flexibility and efficiency.** Mouse path for novices plus keyboard accelerators for experts; "next uncertain item" command.
8. **Aesthetic and minimalist design.** Dense does not mean cluttered: only show data relevant to the decision at hand (see section 10).
9. **Help users recognize, diagnose, recover from errors.** Plain Turkish messages: what happened, why, what to do; no codes as the primary message.
10. **Help and documentation.** Task-oriented Rehber, searchable, with images; contextual "?" per tab.

## 2. Response-time limits and progress indicators

NN/g (after Miller 1968 and Card et al. 1991) gives three limits [1]:
- **0.1 s**: feels like direct manipulation; no feedback needed other than the result itself. Target for selection highlight, focus move, cell edit echo, thumbnail selection.
- **1.0 s**: the user's flow of thought is unbroken but the delay is noticed; no special indicator needed up to ~1 s.
- **10 s**: limit for keeping attention. Beyond this, users switch tasks; show a percent-done indicator, an estimate of remaining time, and a cancel/stop option.

NN/g's practical progress-indicator guidance (unverified exact wording): under ~1 s no indicator; 2-10 s a looping spinner or busy indicator; over 10 s a determinate progress bar (percent or "k of n"). For batch work of 100-800 pages (OCR, export), show "page 143 / 612", elapsed and estimated remaining time, allow cancel and allow the user to keep reviewing finished pages while the rest processes (skeleton content, not blocking).

Qt note: never do OCR or PDF work in the GUI thread; move work to QThreadPool/QThread and emit progress signals. A blocked GUI thread beyond ~100 ms is perceived as lag and Windows will mark the window "Not responding" after ~5 s.

## 3. Fitts's law and Hick's law

- **Fitts's law** (Fitts 1954; MacKenzie 1992 Shannon form): MT = a + b * log2(D/W + 1) [7]. Larger and closer targets are faster. Screen edges and corners behave as effectively infinite-size targets on a desktop, hence menu bars/toolbars at the window edge are fast, but floating toolbars in the middle are not.
- Implications: primary actions (Accept, Next, Split here) should be large (not tiny icons), placed near the content the user is looking at, and adjacent to each other only when they are not mutually destructive. Separate destructive buttons by space (not just color). Do not shrink buttons to fit more on a 1366x768 screen; instead reduce secondary chrome.
- **Hick's law** (Hick 1952, Hyman 1953): decision time T = b * log2(n + 1) [7]. Fewer visible choices at one level speeds choice, but only helps when choices are unordered; with ordered, familiar items (menus users know) the effect is smaller. Practical rule: at most about 5-7 primary actions per toolbar group; group and label the rest.
- Do not misuse "7 plus or minus 2" as a hard limit on menu items; it concerns short-term memory, and recent estimates are lower (about 4 chunks, Cowan 2001) [13].

## 4. Cognitive load and working memory in repetitive verification

- Working memory holds about 4 chunks (Cowan 2001) [13]. A reviewer comparing an OCR value to the page image must hold the field name, the printed value and the proposed value. Keep these co-located (same screen area, ideally the page crop displayed directly above or beside the editable cell) so nothing is held in memory (split-attention effect, Sweller's cognitive load theory) [14].
- Repetitive tasks cause vigilance decrement: detection rates decline measurably after roughly 15-30 minutes of monotonous monitoring (Mackworth's clock studies; exact curve varies, unverified for this domain). Mitigate with pacing: progress counter ("183 / 612 kontrol edildi"), natural breakpoints between documents, and reminders for breaks (optional, non-modal).
- Reduce extraneous load: the same layout on every item, stable positions of controls (no layout shift after load), consistent focus landing point after each action (e.g., focus returns to the next unresolved row).
- Use progress and "chunks" (per document, per batch) to give a sense of completion (goal gradient effect).

## 5. Human-in-the-loop and automation UX

Key findings from the automation literature:
- **Automation complacency and bias**: people over-trust reliable automation and detect fewer failures (Parasuraman and Manzey 2010) [8]. Complacency is greatest when the automation is mostly correct and the human has other duties; it is not removed by training alone.
- **Trust calibration**: show the system's confidence and reasons so users can calibrate (Lee and See 2004, "Trust in automation") [9]. Trust should match actual reliability, not be maximised.
- **Showing uncertainty**: low-confidence OCR values should be visually distinct (not only by color: add an icon or label and a sort/filter), with a numeric or three-level confidence (e.g., Yüksek / Orta / Düşük). Do not display raw model scores users cannot interpret; tune thresholds on real data (unverified for Evrakçı; to be measured).
- **Exception-based review**: reviewing only low-confidence items is faster but invites misses on confident-but-wrong values. Mitigations from document-capture practice (e.g., commercial IDP products; unverified specifics): sample a fraction of high-confidence items for audit, run cross-field validation (date formats, ID checksum, duplicates), and require explicit first-pass review of the first N documents of each new template.
- **Alert fatigue**: if too many items are flagged, users stop reading flags (documented in clinical alerting, where override rates for drug alerts are commonly reported high; exact figure unverified). Keep flagged proportion low via calibrated thresholds, and tier severity.
- **No silent acceptance**: "accept all suggestions" must show a count and be undoable; the export step should list unreviewed items and refuse or warn clearly.
- Make correction cheap: accept suggestion = one key; edit = start typing; revert to OCR value = one key.

## 6. Keyboard-first design for expert repetitive work

- Provide a complete keyboard path; visible shortcut hints in menus/tooltips (discoverability); a command palette or searchable shortcut list (Ctrl+K style, optional) [10].
- Predictable focus order (left to right, top to bottom; matches visual order; WCAG 2.4.3 Focus Order and 2.4.7 Focus Visible) [6]. Avoid focus traps; Esc always cancels.
- **Mode errors** (Norman; Raskin "The Humane Interface"): a key meaning different things in different states causes errors. Where modes exist (e.g., "draw box" in Şablonlar), show a persistent, visible mode indicator and use a distinct cursor; escape returns to the neutral mode.
- Single-key shortcuts conflict with typing in editable cells; require them only when focus is not in a text field, or use modifiers (WCAG 2.1.4 Character Key Shortcuts: single-character shortcuts must be remappable/disable-able or active only on focus; level A) [6].
- Typing in a cell should replace/edit predictably (F2 to edit existing, Enter to commit and move down, Tab to move right), as in spreadsheets users know.
- Allow reading speed: auto-advance after accept (move to next row) as a user preference.

## 7. Error prevention, undo vs confirmation

NN/g: confirmation dialogs are a weak form of protection because users habituate and click through; prefer undo, which supports user control and does not interrupt flow [3]. Use a confirmation only for actions that are truly irreversible or costly (delete job from disk, overwrite exported files). When used, label buttons with the specific verb ("Dosyaları sil", "Vazgeç") rather than Yes/No/OK; make the safe option default; state consequence and count ("12 belge silinecek"). Consider a transient "Geri al" toast for 5-10 s (duration is a convention, unverified) for reversible actions. Multi-level undo with a visible history is valuable in Kontrol.

## 8. Older adults and low vision

- NN/g's senior-citizen studies (2002, updated 2013 and later) found older users were slower and succeeded less often than younger users on the same websites and cited small text, small targets, and unclear controls [2]. Exact percentages not verified here.
- Text: avoid text below ~14 px at 96 dpi (about 10.5 pt) for body text; for this audience default to 14-16 px (about 11-12 pt) and allow scaling (unverified guideline; Windows default UI is 9 pt Segoe UI, i.e., 12 px, which is small for weak eyesight). Respect OS DPI scaling and provide an in-app text size setting (e.g., 100/125/150%).
- Contrast: WCAG 1.4.3 requires 4.5:1 for normal text and 3:1 for large text (18 pt or 14 pt bold) [6]. For older users aim for 7:1 (AAA 1.4.6) for body text. Aging eyes need roughly 2-3 times more light/contrast than youth (general vision literature; unverified quantification).
- 1.4.11 Non-text Contrast (AA): UI component boundaries and states, and graphical objects needed to understand content, need at least 3:1 against adjacent colors [6]. This applies to input borders, checkboxes, icon-only buttons, and selection outlines on thumbnails.
- 2.5.8 Target Size (Minimum), AA: pointer targets at least 24x24 CSS px, or a 24 px circle around the target must not overlap other targets; exceptions for inline text links, user-agent controls and equivalents [5]. The enhanced 2.5.5 (AAA) is 44x44 [6]. Recommendation: toolbar buttons at least 32x32 px with 8 px spacing; primary buttons at least 40 px tall.
- 2.4.11 Focus Not Obscured (Minimum), AA: a focused element must not be entirely hidden by author-created content such as sticky headers or toolbars [6]. Relevant to a table with sticky header and a docked panel: scroll the focused row clear of them.
- 2.4.13 Focus Appearance (AAA in WCAG 2.2): focus indicator area at least a 2 CSS px thick perimeter of the component and a 3:1 contrast change between focused and unfocused states [6]. Not required but cheap to adopt; adopt it.
- 1.4.1 Use of Color: never rely on color alone (red/green status must have icon or text) [6]. About 8% of men have color vision deficiency (commonly cited figure; unverified for Turkish population).
- 1.4.4 Resize text to 200% without loss of function [6]; test the layout at 150-200% on a 1366x768 screen.
- Avoid time-limited toasts for essential information (2.2.1).

## 9. Eye strain, long sessions, light vs dark

- Positive polarity (dark text on a light background) is generally associated with better proofreading and reading accuracy in healthy-vision users, partly because of smaller pupil size and greater depth of field (Piepenbrock et al. 2013, 2014; Buchner and Baumgartner 2007) [15]. The advantage is larger for small text and older eyes are not exempt.
- Dark mode can be better for some users with light sensitivity or cataracts and in dark rooms, but astigmatism (about 30-50% of people, figure unverified) can make light text on a dark background bloom (halation) [15]. Office rooms are normally bright, so make light the default and offer a dark theme as option, not the default.
- Avoid pure black on pure white (maximal contrast can cause glare for some); use off-white (e.g., #FAFAFA to #F5F5F5 backgrounds) and near-black text (#1A1A1A to #222) while staying above 7:1 (unverified preference; general practice).
- Digital eye strain (computer vision syndrome) is real but its evidence for specific remedies is mixed; the American Optometric Association recommends the 20-20-20 rule (every 20 min look 20 ft away for 20 s) [16] although controlled evidence of benefit is limited (unverified). Reduce glare, avoid large saturated color fields, avoid small low-contrast text.
- Large bright white areas (e.g., full-screen white page images) in a dark theme create strong contrast with chrome; page thumbnails are mostly white, which argues for a light or mid-neutral chrome for the Kontrol tab.

## 10. Information density, progressive disclosure, onboarding and empty states

- **Density**: for expert tools, evidence (e.g., NN/g on dense vs. sparse pages; Tufte's data-ink argument; Shneiderman's visual information seeking mantra "overview first, zoom and filter, details on demand") favours information-rich layouts when the users are trained and the task is repeated [17]. But density must not reduce target size or contrast. Keep row height and font size within accessibility minimums, and gain density through removing redundant chrome, not by shrinking text.
- Offer a density option (Rahat / Normal / Sıkı) with defaults on the comfortable end for this audience.
- **Progressive disclosure**: show common options, reveal advanced ones on demand (Nielsen) [18]. Advanced template options and rarely used filters belong behind a "Gelişmiş" disclosure; limit disclosure to two levels.
- **Onboarding**: for a task-focused internal tool, prefer a short first-run checklist or a guided sample job over a long modal tour; tours have low retention (unverified). Keep the Rehber accessible and contextual.
- **Empty states** (NN/g, Material guidance): each empty state should say what belongs here, why it is empty, and offer the primary action ("Henüz iş yok. Taranmış sayfaları yüklemek için 'Yükle' düğmesine basın."). Never show a blank table.

## 11. Table design for review work

- **Row height**: dense but readable; for older users prefer at least 32-40 px per row with 14 px text (derived from the 24 px target minimum and 44 px AAA; Material data tables use 52 px default and 36-48 px dense, unverified figures).
- **Zebra striping**: evidence is mixed. Studies (Enders 2008, "Zebra striping: more data, ..."; Jessica Enders in A List Apart) found striping can help or hurt little; light separators work as well; the benefit is small for tables with few columns, larger for wide tables where eyes must track across a row (unverified details) [19]. Use subtle stripes (contrast under 1.2:1 between stripes, not carrying meaning) or thin row dividers; never use stripe color that conflicts with status colors. Keep hover/selection highlight clearly stronger.
- **Number alignment**: right-align numeric columns (or align decimal points); left-align text; headings aligned with their data. Use tabular (monospaced digit) figures for amounts and dates so digits line up. Segoe UI has tabular digits by default in many cases (unverified).
- **Sticky headers**: keep column headers and, for long lists, the first identifying column visible while scrolling; ensure focused row is not covered (2.4.11).
- **Inline editing**: clear affordance (editable cells look like inputs on focus/hover), commit with Enter or Tab, cancel with Esc, validation inline with a message adjacent to the cell, and visible "changed from OCR" marker. Avoid modal edit dialogs for single values. Provide sorting/filtering by status (uncertain, edited, accepted).
- **Row status**: combine icon + text + color; keep the status column in a fixed position.

## 12. Localisation concerns (Turkish)

- **Dotted/dotless I**: Turkish has I/ı and İ/i. Standard ASCII casing ("i".upper() == "I") is wrong. In Python, str.upper()/lower() are locale-independent and give wrong results for Turkish; use Qt's QLocale("tr_TR").toUpper()/toLower() or handle I/İ explicitly [20]. This matters for sorting, search (case-insensitive matching "ISPARTA" vs "ısparta"), and "ALL CAPS" label styling. Avoid CSS-like uppercase transformations of labels. File name normalisation must be explicit about Turkish characters.
- **Sorting**: use QCollator with the tr_TR locale (ç, ğ, ı, ö, ş, ü sort after c, g, h, o, s, u in Turkish alphabet order).
- **Text expansion**: Turkish is agglutinative, so words are long; typical UI string expansion from English is about 20-30% for many languages (W3C i18n and IBM guidelines suggest up to 30-40% for short strings, unverified for Turkish specifically). Design buttons with flexible width and test with the longest strings; avoid fixed-width labels, avoid truncating essential words.
- **Keyboard layouts**: Turkish users have either Turkish-Q (the majority) or Turkish-F layouts (the F layout is used by some professional typists; share unverified). Shortcut letters are mapped by key position on Q; on F the same letter appears elsewhere. Qt's QKeySequence uses the produced character, so mnemonic letters differ per layout: do not design shortcuts around mnemonic letters only; prefer Ctrl+digits, F-keys, arrows and Enter/Tab/Esc, which are layout-independent. Avoid shortcuts needing characters such as Ç, Ş, Ğ, İ that are awkward on non-Turkish keyboards. Note AltGr combinations (Ctrl+Alt) are produced by AltGr on Turkish keyboards and can collide with character input (e.g., AltGr+Q = @); avoid Ctrl+Alt+letter shortcuts [21] (unverified specifics).
- **Dates, numbers**: Turkish uses dd.MM.yyyy and decimal comma with thousands dot (1.234,56). Use QLocale for formatting and validate typed input in this format.
- **Fonts**: choose fonts that support Turkish glyphs including İ, ı, Ş, ğ with correct diacritics; Segoe UI on Windows does.

## Rules we should adopt for Evrakçı

1. Any action taking over 1 s shows feedback within 100 ms; over 10 s shows a determinate progress bar with "k / n", time remaining and a Cancel button; the UI stays responsive (no GUI-thread blocking above 100 ms).
2. Interactive control hit areas are at least 32x32 px (hard floor 24x24 per WCAG 2.5.8); primary buttons at least 40 px tall; at least 8 px between adjacent targets; destructive buttons separated from primary ones.
3. Body text default is at least 14 px (about 11 pt); table text at least 14 px; no text under 12 px anywhere; in-app UI scale of 100/125/150/200% with no clipped content on 1366x768 at 150%.
4. Text contrast at least 4.5:1 everywhere, 7:1 for body text and table values; UI boundaries/icons/focus/selection at least 3:1 against neighbours.
5. Focus indicator at least 2 px, 3:1 against both the element and the background, visible on every focusable control; the focused row/cell is never hidden by sticky headers or docked panels.
6. Meaning is never conveyed by color alone: every status has an icon plus a Turkish text label.
7. OCR values carry a three-level confidence marker (icon + label) and the table is sortable/filterable by it; "Next uncertain item" has a keyboard shortcut.
8. No silent acceptance: bulk accept shows a count and is undoable; export lists unreviewed/uncertain items and requires an explicit decision.
9. Review includes an audit sample of high-confidence values (configurable, e.g., 5%; value to be tuned) and cross-field validation flags; first N documents per new template are fully reviewed.
10. The page crop for the field being verified sits within the same view as its editable value, with no scrolling or tab switch needed to compare them.
11. Prefer undo over confirmation. Confirmation dialogs only for irreversible actions, with verb-labeled buttons, the safe option as default and the affected count in the message. Undo/redo covers Kontrol, Değerler edits and template edits.
12. Every function has a keyboard path; shortcuts appear in tooltips/menus; a shortcut cheat sheet opens with F1 or Ctrl+/ (test).
13. Shortcuts use layout-independent keys (Ctrl+digit, F-keys, arrows, Enter/Tab/Esc, Ctrl+Z/Y); no shortcut depends on Ç/Ş/Ğ/İ/Ö/Ü, and no Ctrl+Alt+letter shortcuts; single-key shortcuts are inactive while a text field has focus.
14. Modes (draw box, cut mode) display a persistent indicator and a changed cursor, and Esc always returns to neutral.
15. Focus order matches visual order; after accept/commit focus moves to the next unresolved row; Tab and Shift+Tab never trap.
16. Default theme is light with off-white background and near-black text; offer dark and high-contrast themes as options; both themes meet rules 4-5.
17. Tables: right-aligned numerics with tabular digits, sticky header, row height 32-40 px with density option, subtle or no zebra striping (never carrying meaning), inline edit with Enter/Tab/Esc, changed-from-OCR marker.
18. Empty states say what goes here, why it is empty and offer the primary action in Turkish; first run offers a sample job and checklist, not a forced tour.
19. Rare options sit behind one disclosure level ("Gelişmiş"); no more than about 7 primary actions in any toolbar group.
20. Use Turkish-aware casing, sorting and formatting (QLocale tr_TR, QCollator); never use ASCII upper()/lower() on user-visible or matching text; layouts tolerate +40% string length.
21. Show progress for the session ("183 / 612 kontrol edildi") and per-document completion; offer an optional non-modal break reminder (default off).

## Qt/PySide6 feasibility notes

- Threading: QThreadPool + QRunnable or QThread with signals; QProgressBar determinate mode; QProgressDialog has built-in minimum duration (default 4 s) which may hide short ops; set setMinimumDuration deliberately.
- Focus ring: Qt style sheets can style :focus with outline-like borders; QProxyStyle can draw a custom focus rect; test that styled widgets still show a focus indicator, since style sheets often remove it.
- Tables: QTableView with QStyledItemDelegate for inline editors, confidence icons and the changed marker; QHeaderView sticky by default; use setAlternatingRowColors for subtle stripes; setTextAlignment for numerics.
- Sorting: QSortFilterProxyModel with setSortLocaleAware(True) and a tr_TR QCollator-based lessThan.
- Shortcuts: QShortcut/QAction with QKeySequence; use Qt.ShortcutContext.WidgetWithChildrenShortcut and check focus widget for single-key shortcuts. Show them with action text and tooltips.
- Scaling: Qt 6 supports high-DPI by default; for a user text-size setting, scale the application font (QApplication.setFont) and use font-relative sizes (em/pt) in style sheets rather than px.
- Accessibility: Qt exposes UI Automation via QAccessible on Windows; set accessibleName/Description on icon-only buttons.
- Themes: a single QSS template parameterised with colour tokens makes light/dark/high-contrast variants testable; verify contrast programmatically in a test.
- Toasts with undo: a custom overlay widget (QFrame child of the main window) with a QTimer; not natively supported.

## Sources

[1] NN/g, "Response Times: The 3 Important Limits" - https://www.nngroup.com/articles/response-times-3-important-limits/ (not re-fetched; blocked)
[2] NN/g, "Usability for Senior Citizens" and "Seniors as Web Users" - https://www.nngroup.com/articles/usability-for-senior-citizens/ (not re-fetched)
[3] NN/g, "User Control and Freedom" / confirmation dialogs articles - https://www.nngroup.com/articles/user-control-and-freedom/ (not re-fetched)
[4] W3C, Understanding SC 2.4.13 Focus Appearance - https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html (not re-fetched)
[5] Search result summary for WCAG 2.5.8 (accessed 2026-11-12): https://tabnav.com/academy/wcag/success-criterion-2.5.8 and https://dequeuniversity.com/rules/axe/4.8/target-size ; primary: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
[6] W3C, WCAG 2.2 - https://www.w3.org/TR/WCAG22/ (SC 1.4.1, 1.4.3, 1.4.4, 1.4.6, 1.4.11, 2.1.4, 2.4.3, 2.4.7, 2.4.11, 2.4.13, 2.5.5, 2.5.8)
[7] Fitts (1954); MacKenzie (1992) "Fitts' law as a research and design tool in HCI"; Hick (1952); Hyman (1953); overview: https://www.interaction-design.org/literature/topics/fitts-law
[8] Parasuraman and Manzey (2010), "Complacency and Bias in Human Use of Automation", Human Factors 52(3)
[9] Lee and See (2004), "Trust in Automation: Designing for Appropriate Reliance", Human Factors 46(1)
[10] Nielsen, "Usability Engineering" (1993) on accelerators; NN/g "Keyboard shortcuts" articles
[11] Raskin (2000), "The Humane Interface"; Norman, "The Design of Everyday Things" (mode errors)
[12] NN/g, "10 Usability Heuristics for User Interface Design" - https://www.nngroup.com/articles/ten-usability-heuristics/
[13] Cowan (2001), "The magical number 4 in short-term memory", Behavioral and Brain Sciences 24
[14] Sweller (1988), "Cognitive load during problem solving"; split-attention effect literature
[15] Piepenbrock et al. (2013/2014), Ergonomics, on positive vs negative polarity; Buchner and Baumgartner (2007)
[16] American Optometric Association, computer vision syndrome / 20-20-20 guidance - https://www.aoa.org
[17] Shneiderman (1996), "The eyes have it" visual information seeking mantra
[18] NN/g, "Progressive Disclosure" - https://www.nngroup.com/articles/progressive-disclosure/
[19] Enders (2008), "Zebra Striping: Does it Really Help?", A List Apart - https://alistapart.com/article/zebrastripingdoesitreallyhelp/
[20] Qt documentation: QLocale::toUpper/toLower, QCollator; Unicode SpecialCasing (Turkic dotted/dotless i) - https://doc.qt.io/qt-6/qlocale.html
[21] Microsoft, Turkish keyboard layouts (Q and F) documentation (unverified specifics)
