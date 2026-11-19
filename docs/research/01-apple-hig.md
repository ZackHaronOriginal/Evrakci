# 01 — Apple Human Interface Guidelines: what transfers to Evrakçı

Scope: Apple HIG (current, change-logged through 2026), read from Apple's own JSON content endpoints for each HIG page [1]–[13] plus the WWDC25 design-system talks [14][15]. Everything marked "(unverified)" could not be confirmed from a primary page in this session.

## TL;DR

- Apple's macOS default text size is **13 pt**, minimum **10 pt**; macOS has no Dynamic Type [1][2]. For Evrakçı's older users, treat 13 pt as a floor for body text, not a target, and let the user scale.
- Apple's contrast floor: **4.5:1** for text up to 17 pt, **3:1** for 18 pt+ or bold; in Dark Mode Apple says aim for **7:1** on small text [2][10].
- Mac controls: default hit size **28x28 pt**, minimum **20x20 pt**; iOS is 44x44 pt [2][3]. Space bezeled controls ~**12 pt** apart, unbordered ones ~**24 pt** [2].
- Dense desktop layout = sidebar (max 2 levels) + content list + detail/inspector in a split view, with thin **1 pt** dividers, hideable panes and sane min/max pane widths [4][5].
- One or two prominent (accent-filled) buttons per view; distinguish the preferred choice by style, never by size; never make a destructive button the primary/default [3].
- Alerts only for actionable or irreversible things. Common undoable actions get **undo, not a confirmation**. Undo must be unlimited-ish, labelled ("Undo Typing"), and must show/scroll to the result [6][7].
- Determinate progress whenever possible, never stationary, with Cancel (and Pause if cancel loses work) and an even pace [8].
- Never rely on colour alone; add text/glyph/shape. Use semantic colours and supply light, dark and increased-contrast variants [9][10].
- Liquid Glass (2025) is for the floating navigation/control layer only; not for content such as tables. For a Qt app the transferable part is the layering discipline and concentric geometry, not the blur [11][14][15].
- Avoid light font weights (Ultralight/Thin/Light); prefer Regular, Medium, Semibold, Bold [1].

## 1. Design principles and Liquid Glass

**Older framing.** Clarity, deference, depth (iOS 7–era). Still visible in the current text: content comes first and controls recede.

**2025 framing.** The WWDC25 "Get to know the new design system" talk presents a design system built on hierarchy, harmony and consistency, where every element "from the tiniest control to the largest surface" is "considered in relation to the whole" [14]. The "hierarchy / harmony / consistency" triad is my summary of that talk's headings (unverified wording). Concretely it adds:

- **Liquid Glass** is a dynamic material forming a "distinct functional layer for controls and navigation elements — like tab bars and sidebars — that floats above the content layer" [11]. Two variants: *regular* (blurs and adjusts luminosity; use when there is a lot of text, e.g. alerts, sidebars, popovers) and *clear* (highly translucent, only over media; add a 35 % dark dimming layer if the content behind is bright) [11].
- **Don't use Liquid Glass in the content layer**; use standard materials there. Use it sparingly even on custom controls [11].
- Colour on glass: apply accent colour to the **background** of a primary action rather than to its label; never tint the background of many controls [9].
- **Concentricity.** Three shape types: fixed radius, capsule (radius = half the container height), and concentric (radius = parent radius minus padding). Nested shapes should share a centre, so inner radius = outer radius − padding [14].
- **Density on macOS.** Mini, Small and Medium controls keep rounded rectangles for "compact, high-density layouts like inspector panels"; Large controls become capsules and a new X-Large size exists for emphasis in spacious areas [14].
- Apple's typography note: type is "now bolder and left-aligned" in alerts and onboarding [14].

**Relevance for Qt.** Real-time background blur/refraction is expensive and unreliable in QtWidgets and Qt Quick across Windows/Linux, and it harms legibility for older users. Reject the glass effect; keep the *structure*: a quiet content layer (page thumbnails, tables) and a distinct, flat control layer (toolbar, sidebar), separated by a hairline or a subtle tone step, not by translucency. Apple itself falls back to more opaque glass when Reduce Transparency/Increase Contrast is on [11] — a flat opaque surface is the accessible baseline.

## 2. Layout and spacing

What Apple publishes (layout page [4], split views [5], sidebars [12], toolbars [13]):

- Order by importance: most important at top and leading side. Align to make things scannable; indent to show subordination; group by whitespace, containers or separators; use progressive disclosure (disclosure triangles, menus, nested views) [4].
- macOS: **avoid controls or critical information at the bottom of a window or of a sidebar**, because users move windows partly off-screen [4][12]. (Relevant to 1366x768 PCs with a taskbar; keep primary actions top or right/trailing.)
- Large displays let you "present more content in fewer nested levels and with less need for modality, while maintaining a comfortable information density" [16].
- Let people resize, hide and show panes; offer menu + shortcut + toolbar button to restore hidden ones [5][16].
- Apple does **not** publish a numeric macOS margin/spacing grid in the HIG text I read (only tvOS safe areas 60/80 pt, visionOS 60 pt centres). Common practice of 8 pt multiples and a 20 pt window margin is general knowledge (unverified).

**Split views [5].** Persistently highlight the selection in every pane leading to the detail. Allow drag-and-drop between panes. Set reasonable **min and max pane sizes so the divider stays visible**. **Prefer the thin divider, 1 pt wide.** Keynote is Apple's example of a dense layout: slide navigator, presenter notes and inspector surround the canvas, each hideable.

**Sidebars [12].** No more than **two levels** of hierarchy; deeper data → add a content list column between sidebar and detail. Let users hide it (button or View-menu command) and don't hide it by default (discoverability). Sidebar row height, text and glyph size come in **small / medium / large** (user setting). Icons use the accent colour by default; fixed colours sparingly and only where colour carries meaning. Group with disclosure controls; allow customisation.

**Toolbars [13].** Group items by logical section; choose items deliberately to avoid overflow; overflow menu is automatic, don't add one; "More" menu for rarely used actions; allow customisation in apps used for long sessions. Prefer symbols over text except for words like Edit. Window titles: concise, **under ~15 characters**, never the app name. Reduce toolbar backgrounds and tints.

**Pro-app pattern (Final Cut Pro, Logic, Pages/Numbers/Keynote, Preview, Photos).** Verified only for Keynote [5]. The others follow the same three-zone pattern as general knowledge (unverified in this session): source/navigation sidebar on the left → large content canvas/list/timeline in the centre → contextual inspector on the right (Pages/Numbers/Keynote "Format" pane; Final Cut and Logic inspectors; Preview and Photos sidebar + content), with toolbar on top, optional status/info strip at the bottom. Inspector content swaps with the selection; panels hide with a keyboard shortcut.

## 3. Typography

**Face.** SF Pro is the macOS system font (variable, with dynamic optical sizes); NY (serif) is not for macOS-native apps. Avoid embedding system fonts; minimise the number of typefaces [1]. Prefer Regular / Medium / Semibold / Bold; avoid Ultralight, Thin, Light [1].

**Defaults and minimums [1][2]:**

| Platform | Default | Minimum |
|---|---|---|
| macOS | 13 pt | 10 pt |
| iOS/iPadOS | 17 pt | 11 pt |
| visionOS | 17 pt | 12 pt |
| watchOS | 16 pt | 12 pt |
| tvOS | 29 pt | 23 pt |

**macOS built-in text styles [1]** (size / line height in pt; default weight → emphasised weight):

| Style | Weight | Size | Line height | Emphasised |
|---|---|---|---|---|
| Large Title | Regular | 26 | 32 | Bold |
| Title 1 | Regular | 22 | 26 | Bold |
| Title 2 | Regular | 17 | 22 | Bold |
| Title 3 | Regular | 15 | 20 | Semibold |
| Headline | Bold | 13 | 16 | Heavy |
| Body | Regular | 13 | 16 | Semibold |
| Callout | Regular | 12 | 15 | Semibold |
| Subheadline | Regular | 11 | 14 | Semibold |
| Footnote | Regular | 10 | 13 | Semibold |
| Caption 1 | Regular | 10 | 13 | Medium |
| Caption 2 | Medium | 10 | 13 | Semibold |

Line height / size ≈ 1.23 for body (16/13). For long passages Apple recommends looser leading; for 3+ lines never use tight leading [1].

**Tracking (macOS SF Pro, per 1/1000 em) [1]:** 10 pt +12, 11 pt +6, 12 pt 0, 13 pt −6 (−0.08 pt), 14 pt −11, 15 pt −16, 16 pt −20, 17 pt −26, 20 pt −23, 22 pt −12, 24 pt +3. Small sizes get *positive* tracking (looser), mid sizes slightly negative. A running Mac app applies this automatically; replicate only in mockups or when using a non-system font. Qt: `QFont.setLetterSpacing(PercentageSpacing/AbsoluteSpacing)` can mimic it, but with a different face (Segoe UI Variable / Inter) don't copy SF's values.

**Dynamic-type behaviour worth copying.** Keep hierarchy when text scales; "prioritize important content" — enlarge content text, not tab titles; keep truncation minimal; reduce columns and stack inline items when text is large; keep primary elements at top [1]. Accessibility guidance: let people enlarge text by **at least 200 %** [2].

**Weight use.** Regular for body; Medium/Semibold for emphasis and column headers; Bold sparingly; one emphasised level per row. Numerals: SF has tabular figures (use for value columns) (unverified in this session).

## 4. Colour and Dark Mode

- Use **semantic** dynamic colours (label, secondary/tertiary/quaternary label, separator, window background, control background, alternating row backgrounds, selected-content background vs. *unemphasised* selected-content background for non-key windows, keyboard-focus ring, link, placeholder) rather than hard-coded values; Apple warns documented RGB values change between releases [9]. Don't repurpose a label colour as a background or vice versa [9].
- Primary/secondary/tertiary background levels = overall view / grouped content / content within grouped content [9].
- **Accent colour** tints buttons, selection highlight and sidebar icons; the user can override it in system settings; fixed-colour sidebar icons are the exception [9]. Don't use the same colour for different meanings (e.g. brand colour for both interactive and non-interactive text) [9].
- Provide **light, dark and increased-contrast** variants of every custom colour, with the increased-contrast variant "significantly" more differentiated [9].
- Don't convey information by colour alone; add labels or glyph shapes; red-green and blue-orange are the problem pairs [9][10].
- Dark Mode: dimmer backgrounds, brighter foregrounds; not simple inversion. Minimum **4.5:1**; for custom small text strive for **7:1** [10]. Soften pure-white content backgrounds so they don't glow. Don't offer an app-specific appearance setting — follow the system [10]. Test Dark + Increase Contrast + Reduce Transparency together; dark text on dark can get *worse* [10].
- Vibrancy: system vibrant colours on materials keep contrast stable; thicker materials give more contrast for fine text, thinner keep context [11].

**For Evrakçı (Windows-first).** No OS equivalent of AppKit semantic colours exists in Qt; define a token palette with the same *roles* (see rules). Qt 6.5+ `QStyleHints.colorScheme()` and `colorSchemeChanged` follow the OS light/dark setting; accent colour is exposed via `QPalette.Accent` in Qt 6.6+ (unverified exact version).

## 5. SF Symbols (icons)

Rules [15b: SF Symbols page]:
- Nine weights matching the nine SF font weights; three scales (small, medium default, large) defined relative to SF cap height. Use the same weight as the adjacent text; use scale to change emphasis without breaking weight matching.
- Four rendering modes: monochrome (one colour), hierarchical (one colour, per-layer opacity), palette (2+ colours), multicolor (intrinsic colours). Check legibility per size/background; use system colours so accessibility adaptations apply.
- Variants: outline in toolbars/lists next to text; fill for selection/emphasis; enclosed shapes (circle/square) improve legibility at small sizes; slash = unavailable.
- Variable colour communicates a changing value (capacity, strength), not depth; use hierarchical mode for depth.
- Increase symbol size when font size increases [1].
- Sidebar icons: familiar symbols; custom icons should be vector symbols, not bitmaps [12]. Image buttons: ~**10 px** padding around the image inside the clickable area [3].
- SF Symbols are licensed for Apple platforms only; the licence forbids use in logos/app icons [15b]. **Not usable in a Windows/Qt app.** Substitute an open icon set with a consistent stroke and matching weights (e.g. Lucide, Phosphor, Material Symbols have weight axes — licences to be verified before adoption).

## 6. Controls

**Sizes.**

| Item | iOS | macOS | Source |
|---|---|---|---|
| Default control size | 44x44 pt | 28x28 pt | [2] |
| Minimum control size | 28x28 pt | 20x20 pt | [2] |
| Hit region rule of thumb | ≥ 44x44 pt (all) | same text, applies "whether … fingertip, a pointer…" | [3] |
| Padding around bezeled controls | ~12 pt | ~12 pt | [2] |
| Padding around unbordered controls | ~24 pt | ~24 pt | [2] |

macOS control size tiers: **Mini, Small, Medium (regular), Large, X-Large** (the last two new in the 2025 design system; Mini/Small/Medium stay rounded rectangles) [14]. Exact push-button heights are not in the HIG text I read; AppKit values I recall are 16 / 19 / 22 pt for mini / small / regular, 28 pt for large (unverified). Treat 22 pt as Apple's *dense* default and note that Apple's own "default control size" for pointer accessibility is 28 pt [2].

**Buttons [3].**
- Roles: Normal, Primary (default, responds to Return, accent-filled), Cancel, Destructive (red). Never give the primary role to a destructive action.
- **One or two prominent buttons per view.** Distinguish the preferred option by *style*, not size; equal-size buttons signal a coherent set.
- Always provide a press state for custom buttons.
- Push buttons: trailing ellipsis when the button opens further input ("Edit…"). Square (gradient) buttons: symbol-only, adjacent to the view they affect (add/remove row), not in toolbars. At most one help button per window, in a lower corner opposite the dismissal buttons. Tooltips on hover in macOS.
- Labels: verb-led, few words ("Add to Cart").

**Text fields [text-fields page, 17].** Size matches expected content; evenly spaced, vertically stacked, consistent widths; logical tab order; validate on blur for email/numbers (before leaving field for passwords); number formatters locale-aware; expansion tooltip for clipped text; placeholder plus a separate label.

**Tables and lists.** The HIG tables page returned 404 in the JSON endpoint; alternating row backgrounds, grid colour, header text colour and the selected/unemphasised-selected distinction exist as semantic colours [9].

## 7. Feedback, progress, alerts, undo

**Feedback [18].** Match interruption level to importance: passive status in context for routine info, interrupting alert only for data-loss risk. Warn before *unexpected and irreversible* data loss; don't warn when loss is the expected result. Confirm completion only for significant tasks. When a command can't run, say why. Provide feedback in more than one channel (colour + text + sound/haptic).

**Progress [8].**
- Prefer determinate; report accurately; even out the pace ("90 % in 5 seconds and the last 10 % in 5 minutes … feel[s] deceptive").
- Keep it moving; a stationary indicator reads as frozen; if stalled, explain.
- Switch indeterminate → determinate when possible; never switch spinner ↔ bar.
- Show a specific description, not "Loading" or "Authenticating".
- Consistent location. Provide Cancel; add Pause if cancelling loses progress; confirm if cancelling loses progress.
- macOS supports an indeterminate bar as well as a spinner.

**Alerts [6].**
- Sparingly; not for information-only messages, not at launch, not for common undoable actions even if destructive.
- Title: specific, complete, ≤ 2 lines; never "Error" or "Error 329347 occurred"; sentence → sentence case + period; fragment → title case, no period. Message only if it adds value.
- At most **three buttons**; one- or two-word verb titles ("Erase", "Convert"); avoid OK unless purely informational; avoid Yes/No; always "Cancel" for cancel.
- Default button on trailing side (or top of a stack); Cancel on leading side. A Cancel button should not be the default. If you want people to read, make **no** button default.
- Destructive style only when the user did *not* deliberately choose the destructive action; if they chose "Empty Trash", the confirmation button is a normal default so Return confirms.
- Esc or Cmd-. cancels.
- macOS alerts can have an icon, accessory view, and a "Don't ask again" suppression checkbox [6].
- Assistive-Access guidance: "ask for confirmation twice" for hard-to-recover actions like deleting a file [10].

**Undo/redo [7].** People will press undo repeatedly "until something changes" — so (1) name the target in the menu ("Undo Typing", "Redo Bold"), (2) show/scroll to the result, even off-screen, (3) don't limit the number of undos unnecessarily; users expect to undo everything since opening or saving, (4) consider "revert all/batch", (5) only add toolbar undo/redo buttons when necessary, using the system symbols. macOS: top of Edit menu, Cmd-Z and Shift-Cmd-Z.

**Motion [19].** Purposeful, brief and cancellable; avoid motion on frequent interactions; never make users wait for an animation; motion must not be the only channel. No numeric durations published for macOS; Apple gives 30–60 fps as the game target only.

## 8. Accessibility (as Apple states it) [10]

- Text enlargement of at least **200 %** (140 % watchOS) via Dynamic Type or custom UI.
- Contrast minimum (WCAG AA): **up to 17 pt → 4.5:1**; **18 pt → 3:1**; **bold at any size → 3:1**. If you can't meet this by default, at least provide a higher-contrast scheme when Increase Contrast is on. Check both light and dark.
- Don't rely on colour only; use shapes/icons.
- Controls: macOS default 28x28 pt / min 20x20 pt; ~12 pt padding for bezeled elements, ~24 pt for bare ones.
- Full keyboard operation; don't override system shortcuts; test with Full Keyboard Access.
- Cognitive: minimise time-boxed UI (auto-dismiss on a timer is a problem — prefer explicit dismissal); keep interactions simple and consistent.
- **Reduce Motion:** reduce automatic/repetitive animation incl. zooming and scaling; tighten springs, track gestures directly, avoid animating depth, replace x/y/z transitions with fades, avoid animating into/out of blurs.
- Dark Mode: test with Increase Contrast and Reduce Transparency, separately and together [11 / 10].

## Rules we should adopt for Evrakçı

1. **Type scale.** Apple's 13 pt / 10 pt default/minimum are in macOS points (1 pt = 1 px at 1x); on Windows treat that as 13 px = floor. For our older users use **15 px body (my suggestion, not Apple)** as default and **never below 12 px** for any readable text. Provide four user settings: 100 / 125 / 150 / 200 % text scale, and verify every screen at 200 % (Apple's explicit ≥ 200 % target) [2]. Test: all six tabs usable at 200 % on 1366x768 without clipped labels.
2. **Scale mapping** (adapted from Apple's macOS table [1]): Title 22/26, Section 17/22 semibold, Body 13→adopt 15/20, Secondary 12→13/17, Caption ≥ 12/16. Line height ≈ 1.25–1.35x body.
3. **Weights.** Only Regular, Medium, Semibold, Bold. No Light/Thin anywhere [1].
4. **Contrast.** Body and control text ≥ **4.5:1**; target **7:1** for small text in dark theme and for all table text [10]; large/bold ≥ 3:1; non-text UI (icons, borders of inputs, focus ring) ≥ 3:1 (WCAG 1.4.11; consistent with Apple's guidance). Add an automated token-pair contrast test in CI.
5. **Semantic colour tokens**, not raw values: `label/secondary/tertiary`, `surface-window`, `surface-content`, `surface-control`, `row-alt`, `selected` and `selected-inactive` (non-key window), `separator`, `focus-ring`, `link`, `placeholder`, `accent`, `danger`, `warning`, `success`. Each in light, dark and high-contrast sets [9].
6. **One accent colour**, used for primary buttons, selection and focus only; never reuse it for non-interactive text [9]. Max one or two accent-filled buttons per view [3].
7. **Status is never colour-only.** Every status (read OK / needs check / error / accepted) has an icon shape + text label in addition to colour [9][10].
8. **Control sizes.** Minimum hit target **28x28 px** (Apple's Mac default) with **≥ 20x20** only for dense secondary items; primary buttons ≥ 32 px tall; ≥ 12 px between adjacent bezeled controls, ≥ 24 px around borderless icon buttons [2]. Do not shrink controls below this to gain density; gain density with layout (fewer nested levels) instead [16].
9. **Layout skeleton.** Sidebar (tabs/jobs, ≤ 2 levels) | content | optional inspector, with 1 px dividers, min/max widths so the divider never vanishes, and collapse buttons + shortcuts for each side pane [5][12]. Kontrol: thumbnail timeline centre, detail/inspector right. Şablonlar: page canvas centre, box properties right. Değerler: table centre, evidence/page preview right.
10. **No critical controls at the bottom edge** of the window (taskbar overlap on 768 px screens): put Save/Next/Export in the top or right [4][12].
11. **Buttons.** One Primary per view, bound to Enter; never Primary on a destructive action; preferred choice distinguished by style not size; verb labels; trailing "…" if it opens more input [3].
12. **Alerts.** Max 3 buttons; button text states the result ("Sil", "Dışa aktar", never "Evet/Hayır/Tamam" except info-only); Esc cancels; no alert for undoable actions; no alert at launch; title ≤ 2 lines and specific [6].
13. **Undo everywhere.** Every state-changing action in Kontrol/Şablonlar/Değerler is undoable; menu/tooltip names the action ("Geri al: Kesim ekle"); undo scrolls/highlights the affected page/row; no arbitrary stack cap; "Tümünü geri al" for the session [7].
14. **Progress.** Determinate with pages-done/total and time estimate for OCR/split/export; never stationary; message names the step ("Sayfa 212/640 okunuyor"); Cancel always, Pause where cancelling loses work, and confirmation when it would [8].
15. **Motion.** Max one short transition (~150 ms, my suggestion — Apple publishes none) for state changes; no motion on frequent actions (selecting, paging); honour OS "reduce animations" by swapping to instant/fade; no auto-dismissing toasts for anything that requires action [10][19].
16. **Follow system appearance**; no in-app theme setting beyond text size and high-contrast; test dark + high contrast [10].
17. **Icons.** One icon family, outline in toolbars, fill for selected state, stroke weight matched to text weight, sizes 16/20/24 px for text 13/15/17; icon scales up with text scale [5 SF Symbols][1].
18. **Fields.** Placeholder plus persistent label; inline validation on blur; tab order = visual order; tooltip with full text for clipped values; locale-aware numbers/dates (tr-TR decimal comma) [17].
19. **Window titles ≤ 15 characters per tab/window title where possible**; do not repeat app name [13].

## Qt/PySide6 feasibility notes

- Everything above except Liquid Glass/vibrancy/SF Symbols is achievable with QSS + custom `QPalette`/design tokens; use one token dict that generates both the palette and the stylesheet to enforce contrast tests.
- `QSplitter` (`setHandleWidth(1)`, `setChildrenCollapsible(True)`, per-widget `setMinimumWidth`) covers split-view rules; remember to save/restore state with `saveState()`.
- `QUndoStack`/`QUndoCommand.setText()` gives labelled undo/redo for free (`createUndoAction()` text becomes "Undo <text>"), matching [7].
- Text scaling: derive all sizes from one base `QFont` and `devicePixelRatio`; do not use fixed pixel heights for rows; test with `QT_SCALE_FACTOR` and Windows text-size settings.
- `QStyleHints.colorScheme()` follows the OS light/dark; Windows contrast themes need manual handling via `QPalette` (Qt 6.x behaviour varies; unverified).
- Blur-behind and vibrancy are not available cross-platform in Qt; skip them.
- Keyboard focus ring: Qt's default focus rect is faint; implement a 2 px accent focus ring (≥ 3:1) on all focusable custom widgets (thumbnails, table cells).

## Sources (all accessed 2026-11-12)

[1] Typography — https://developer.apple.com/design/human-interface-guidelines/typography (read via https://developer.apple.com/tutorials/data/design/human-interface-guidelines/typography.json; change log shows Dec 16, 2025)
[2] Accessibility — https://developer.apple.com/design/human-interface-guidelines/accessibility
[3] Buttons — https://developer.apple.com/design/human-interface-guidelines/buttons
[4] Layout — https://developer.apple.com/design/human-interface-guidelines/layout
[5] Split views — https://developer.apple.com/design/human-interface-guidelines/split-views
[6] Alerts — https://developer.apple.com/design/human-interface-guidelines/alerts
[7] Undo and redo — https://developer.apple.com/design/human-interface-guidelines/undo-and-redo
[8] Progress indicators — https://developer.apple.com/design/human-interface-guidelines/progress-indicators
[9] Color — https://developer.apple.com/design/human-interface-guidelines/color
[10] Dark Mode — https://developer.apple.com/design/human-interface-guidelines/dark-mode (and Accessibility, [2])
[11] Materials — https://developer.apple.com/design/human-interface-guidelines/materials
[12] Sidebars — https://developer.apple.com/design/human-interface-guidelines/sidebars (change log June 8, 2026)
[13] Toolbars — https://developer.apple.com/design/human-interface-guidelines/toolbars
[14] WWDC25, "Get to know the new design system" — https://developer.apple.com/videos/play/wwdc2025/356/
[15] WWDC25, "Meet Liquid Glass" — https://developer.apple.com/videos/play/wwdc2025/219/
[15b] SF Symbols — https://developer.apple.com/design/human-interface-guidelines/sf-symbols
[16] Designing for macOS — https://developer.apple.com/design/human-interface-guidelines/designing-for-macos (change log Oct 28, 2026)
[17] Text fields — https://developer.apple.com/design/human-interface-guidelines/text-fields
[18] Feedback — https://developer.apple.com/design/human-interface-guidelines/feedback
[19] Motion — https://developer.apple.com/design/human-interface-guidelines/motion

Not verified: exact macOS push-button heights (16/19/22/28), HIG numeric margins for macOS, the iOS Dynamic Type table (tabbed content not extracted), details of Final Cut Pro/Logic/Pages/Numbers/Preview/Photos layouts, Qt version numbers for accent-colour APIs, open icon-set licences.
