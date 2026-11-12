# 03 — Fluent 2 / Windows 11 and the big enterprise design systems

**Access caveat.** Direct page fetches failed in this session: learn.microsoft.com, carbondesignsystem.com and others did not resolve (host not in the session's allowed network domains). Only WebSearch snippets were available. Everything marked **[verified]** was confirmed in a search snippet of an official source. Everything marked **(unverified)** is from memory of the published specs and must be re-checked before it goes into the final prompt. To close the gaps, allow learn.microsoft.com, fluent2.microsoft.design, carbondesignsystem.com, sap.com, primer.style, atlassian.design, polaris.shopify.com and lightningdesignsystem.com, then re-run.

## TL;DR

- Windows 11 body text is Segoe UI Variable 14/20 [1]. Caption is 12/16 and the dense-UI floor. For long sessions with older users, treat 14 px as the minimum for data and 12 px only for secondary hints.
- Windows 11 uses a 4 px grid. Standard controls are 32 px tall. Corner radii are 4 px for in-page controls and 8 px for top-level containers (flyouts, dialogs, cards) (unverified).
- Focus visual: 2 px outer (primary) plus 1 px inner (secondary) border, with contrasting colours so it shows on any background [2]. Adopt it unchanged. It is the single best accessibility pattern to copy.
- Mica and Acrylic are optional chrome. Never put either behind data tables or thumbnails; a plain solid layer is better for reading density.
- Every dense enterprise system offers two or more density modes. SAP's guidance is "compact" for mouse-and-keyboard desktops, "cozy" (44 px touch area) for touch. Never mix the two in one page [3].
- Carbon table rows come in five sizes (xs–xl). Older documented heights are 24 / 32 / 48 / 64 px [4]. The toolbar height must equal the row height.
- Table rows must have uniform height for stable scrolling [3]. This matters for our thumbnail timeline and Değerler table.
- Status must never be colour-only. Pair colour with an icon and a text label (rule in every system; see Rules).
- Qt 6 has a native "windows11" style (6.7+) and DWM attributes work from PySide6 via ctypes, but Mica and Segoe UI Variable are Windows-only. Linux and macOS need a fallback font and a flat layer.

## 1. Fluent 2 / Windows 11

### 1.1 Principles
Fluent 2 and Windows 11 design emphasise: natural on every platform, built for focus, one for all and all for one (accessible to everyone), and "delightful" through motion and material (unverified wording; the principle names are from Fluent 2's site [5]). The takeaway for a work tool: calm neutral surfaces, one accent colour, content first, depth conveyed by subtle layers and not by heavy chrome.

### 1.2 Type ramp (Segoe UI Variable, WinUI)
Windows 11 UI uses Segoe UI Variable, which has optical sizes (Small, Text, Display) [1][6]. Search-confirmed values: Small/Caption 12/16, Text/Body 14/20, Subtitle 20/28, Title 28/36, Display 68/92 [1]. The rest comes from memory of the WinUI ramp (unverified):

| Style | Weight | Size / line height (px) |
|---|---|---|
| Caption | Regular | 12 / 16 [verified] |
| Body | Regular | 14 / 20 [verified] |
| Body Strong | SemiBold | 14 / 20 (unverified) |
| Body Large | Regular | 18 / 24 (unverified) |
| Subtitle | SemiBold | 20 / 28 [verified] |
| Title | SemiBold | 28 / 36 [verified] |
| Title Large | SemiBold | 40 / 52 (unverified) |
| Display | SemiBold | 68 / 92 [verified] |

Segoe UI Variable text uses "Text" optical size at 14 px and below, "Display" at 20 px and above (unverified detail). Turkish glyphs (ç, ğ, ı, İ, ö, ş, ü) are supported by Segoe UI.

### 1.3 Spacing and sizing
- 4 px grid; common gaps 4, 8, 12, 16, 24 (unverified).
- Standard control height 32 px (buttons, text boxes, combo boxes); WinUI has no official compact mode in the controls themselves, but WinUI 2 had "compact" resources at 24 px (unverified). Touch target guidance is 40 × 40 px minimum for touch and 44 px recommended (unverified).
- Corner radius: 4 px for controls, 8 px for overlays, cards and windows (unverified, widely documented in the Windows 11 geometry page).

### 1.4 Materials and elevation
- Mica: an opaque, wallpaper-tinted material for the window's base layer and title bar; cheap (sampled once) and for long-lived windows. Acrylic: translucent, blurred, for transient surfaces (flyouts, context menus, light-dismiss). Both fall back to a solid colour when the system turns off transparency, on battery saver, or when the window is inactive (Mica) [7] (unverified details).
- Layering: base (Mica) → "layer" content area (lighter/darker translucent card with 8 px top-left radius) → cards → flyouts. Elevation shadows are soft: a 2 px blur for cards, 8 px blur for flyouts, 32 px blur for dialogs (unverified exact values).
- Do not stack Acrylic on Acrylic. For Evrakçı: use a solid layer behind page thumbnails, because translucency changes the apparent colour of scanned pages.

### 1.5 Colour
- Neutral layers: Light mode base ~#F3F3F3, content layer ~#FFFFFF at 50% opacity; dark mode base ~#202020 (unverified hex values from the WinUI theme resources).
- One accent colour drawn from the user's Windows accent (default blue ~#0067C0 light / #60CDFF dark). Accent is for primary buttons, selection, focus and links only.
- Semantic colours: success green, caution amber, critical red, informational blue, each with a filled-icon form (unverified hexes: critical ~#C42B1C, success ~#0F7B0F, caution ~#9D5D00 light mode).
- High contrast themes: use system colour keywords only (Window, WindowText, GrayText, Highlight, HighlightText, Hotlight, ButtonFace, ButtonText). Do not use custom colours; the OS provides four themes (Aquatic, Desert, Dusk, Night sky) [8] (unverified).

### 1.6 Iconography
Fluent System Icons come in 12, 16, 20, 24, 28, 32, 48 px sizes, in Regular and Filled styles [9] (unverified). Use Regular for default state and Filled for selected or emphasised. Segoe Fluent Icons is the Windows font equivalent. Inline icons next to 14 px text are 16 px.

### 1.7 Controls worth copying
- **Button**: 32 px tall, 4 px radius, horizontal padding 11 px, 1 px border; accent filled for the single primary action. Disabled uses lower-contrast text (unverified).
- **CommandBar**: a row of icon-plus-label buttons with overflow "…" menu; labels on the right of icons; 48 px tall in WinUI, 40 px compact (unverified).
- **NavigationView**: left pane 320 px expanded, 48 px compact, items 40 px tall; top mode suits up to ~5–7 items. Our six tabs fit a top NavigationView or tab strip.
- **TabView**: tabs 32–40 px, closable, reorderable. Only useful if tabs are documents.
- **InfoBar**: inline, persistent message with a severity icon, title, message, optional action and close; four severities. Use instead of toasts for anything staff must not miss.
- **TeachingTip**: anchored, dismissible popover for first-run guidance; useful for Rehber.
- **ProgressRing / ProgressBar**: determinate when a percentage is known; indeterminate only otherwise.
- **DataGrid**: WinUI has no first-party grid; the Community Toolkit DataGrid uses 32 px rows by default (unverified).

### 1.8 Focus visuals
Primary border 2 px, secondary border 1 px inside it, in opposing colours (dark + white) so focus is visible on any background. These are the `FocusVisualPrimaryThickness=2` and `FocusVisualSecondaryThickness=1` properties [2]. "Reveal focus" adds a glow outside the primary border [2]. Focus must be shown for keyboard and gamepad only by default (`UseSystemFocusVisuals`), not on mouse click (unverified).

### 1.9 Keyboard: access keys and accelerators
Windows apps support access keys (Alt then a letter, shown as key tips) and accelerators (Ctrl+letter, shown in menu item text right-aligned). Menus show the shortcut in a dim secondary text column. F6 cycles major regions, Tab moves within, arrows move inside a composite control; Esc dismisses; Enter activates the default; Space toggles. Keep standard Windows shortcuts intact: Ctrl+Z / Ctrl+Y undo and redo, Ctrl+S, Ctrl+F, F1 help.

### 1.10 High-contrast mode
In high contrast, Windows replaces colours with system keywords; borders become essential because shadows and fills vanish. Never rely on subtle fills for state. Selected = Highlight/HighlightText; disabled = GrayText; links = Hotlight. In Qt, `QPalette` follows the system high-contrast palette if the app doesn't override it, so custom QSS that hard-codes colours will break it. Provide a "use system colours" switch and test with Windows' Alt+Left Shift+PrtScn toggle.

## 2. Dense-productivity systems compared

| System | Grid / base | Type (body) | Density modes | Table row heights |
|---|---|---|---|---|
| IBM Carbon | 2x grid; 8 px mini unit, 16 col | IBM Plex Sans; productive body-01 14/18, expressive body-compact | "Productive" (dense, tools) vs "Expressive" (marketing) | xs–xl; documented 24 / 32 / 48 / 64 px in older versions [4] |
| SAP Fiori | 0.5rem steps | 72 font, 14 px base | Cozy (44 px touch) vs Compact (rows/toolbars 32 px); Condensed for tables only [3] | cozy 44 px, compact 32 px, condensed smaller [3] |
| Atlassian | 8 px base, 4 px half-steps | 14 px body | Compact vs default spacing option (unverified) | ~32–40 px (unverified) |
| GitHub Primer | 8 px | 14 px body, line-height 20 | "condensed", "normal", "spacious" density in lists (unverified) | 32–40 px (unverified) |
| Shopify Polaris | 4 px tokens (space-100 = 4 px, etc.) | 13–14 px body | Small / medium table cells (unverified) | ~36–44 px (unverified) |
| Salesforce Lightning | 4 px; 0.75–1 rem tokens | 13 px base | "Comfy" vs "Compact" density setting per user | compact rows ~32 px (unverified) |

Findings I could confirm:
- **Carbon**: row size set is extra small to extra large; toolbar, batch action bar and pagination heights should match row height; extra-large rows are recommended only for two-line cell content [4].
- **SAP**: compact for keyboard-and-mouse desktop; whole app uses one density, never mixed; all line items must share one height [3].

### What makes data-dense enterprise UIs work (synthesis)
1. **A density switch, defaulted by input device.** Desktop keyboard users get compact; give older users an easy "Comfortable" option.
2. **Uniform row heights** with truncation plus tooltip, instead of wrapping, so scroll position is predictable.
3. **Aligned columns**: text left, numbers right, header aligned with its data; sticky header.
4. **Inline editing** with an obvious edit state: Enter or F2 to edit, Enter to commit, Esc to revert, Tab to move to the next cell; a changed-cell marker until confirmed. Carbon, SAP and Lightning all follow this pattern (unverified for details).
5. **Status as icon + word + colour**, in a dedicated narrow column, with the same vocabulary everywhere.
6. **Zebra or thin row separators**, not both; 1 px separators with a hover and a clearly different selected row.
7. **Batch toolbar that replaces the normal toolbar** when rows are selected (Carbon) [4].
8. **Persistent, quiet chrome** so content has the contrast budget.

## Rules we should adopt for Evrakçı

1. Base UI font 14 px / 20 px line height (Body). Nothing in the working area below 12 px; 12 px only for captions and secondary hints. Offer a text-size setting of 100 / 115 / 130 %.
2. Use Segoe UI Variable on Windows (fall back to Segoe UI, then Noto Sans/Inter on Linux, system font on macOS). Test every Turkish diacritic including dotted İ and dotless ı.
3. Layout on a 4 px grid; gaps drawn only from 4, 8, 12, 16, 24 px.
4. Controls: 32 px tall in "Normal", 28 px in "Compact", 40 px in "Comfortable" (we choose these; only 32 is a Windows number). Table row heights 32 / 28 / 40 px respectively, uniform within a table.
5. Radii: 4 px on controls, 8 px on cards, dialogs and popups. No other radii.
6. Focus ring on every focusable element: 2 px outer in accent-contrast colour plus 1 px inner in the opposite (white or black) colour; visible on keyboard focus, never removed.
7. Single accent colour for primary button, selection and focus. At most one primary button per view.
8. Opaque, flat surfaces behind data (tables, thumbnails). Mica is optional on the title bar and sidebar only, and must degrade to a solid fill.
9. Status uses icon + text + colour; never colour alone. Same four severities everywhere: info, success, warning, error.
10. Persistent problems use an inline InfoBar-style banner at the top of the page; toasts only for completed, non-critical events.
11. Every action reachable by keyboard; show accelerators in menus and tooltips; Alt access keys for the six tabs; F6 cycles regions; undo/redo Ctrl+Z / Ctrl+Y.
12. Editable tables: Enter/F2 edit, Enter commit, Esc cancel, Tab next cell; edited-but-unconfirmed cells carry a visible marker.
13. Toolbar height equals the row height of the density mode; a selection toolbar replaces the normal one when items are selected.
14. Honour the OS high-contrast palette: when active, drop custom colours and use palette roles only; borders (1 px) must carry state, not fills.
15. Do not mix density modes on one screen; density is an app-level setting.

## Qt/PySide6 feasibility notes

- **Qt 6 "windows11" style**: Qt 6.7 added a Windows 11 style (`QApplication.setStyle("windows11")`) with 4 px-rounded controls and accent-aware colours; it is on Windows 11 only and falls back to "windowsvista" elsewhere (unverified; check release notes). Qt 6.8+ also follows the system light/dark scheme through `QStyleHints.colorScheme()` (unverified).
- **Mica from PySide6**: call `DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE=38, value=2 /*Mica*/ )` through `ctypes.windll.dwmapi` on Windows 11 build 22621+; for dark title bar use attribute 20 (`DWMWA_USE_IMMERSIVE_DARK_MODE`). The window must have `WA_TranslucentBackground` and the content widgets paint transparent where Mica should show through; extending the frame (`DwmExtendFrameIntoClientArea`) may be needed. Wrap in a version check and try/except; no Mica on Windows 10 or other OSes (unverified numeric constants; verify against the Windows SDK).
- **Segoe UI Variable**: ships with Windows 11 only (not Windows 10 unless updated), and is not redistributable as a file we can bundle. Use a font-family list: "Segoe UI Variable Text", "Segoe UI", sans-serif. Qt does not select optical sizes automatically, so choose "Segoe UI Variable Text" for 14 px and below and "Segoe UI Variable Display" for headings (unverified family names).
- **QSS limits**: QSS cannot do box-shadow, backdrop blur, transitions, or a two-ring focus (outline is unsupported); `border-radius` and `border` work. Build the double focus ring with a custom `QProxyStyle` or a painted overlay, or approximate with a 2 px accent border plus an inner 1 px white via nested widgets. Use QSS only for colours and radii; use `QPalette` for system integration so high contrast keeps working. Prefer a small custom `QStyle` or `QProxyStyle` over deep QSS for a consistent look and for density tokens.
- **Fonts and DPI**: Qt 6 enables high-DPI scaling by default; use `QFontMetrics` and logical px, avoid hard-coded pixel icons; render icons as SVG (Fluent System Icons are available as SVG) at 16/20/24 px.
- **Cross-platform**: on Linux and macOS keep the same layout tokens, with a flat solid background and the platform font.

## Sources (all accessed 2026-11-12 via search snippets only; direct page fetches were blocked)

1. Typography in Windows 11 — https://learn.microsoft.com/windows/apps/design/signature-experiences/typography
2. Guidelines for visual feedback / focus visuals — https://learn.microsoft.com/windows/apps/develop/input/guidelines-for-visualfeedback ; FocusVisualSecondaryThickness — https://learn.microsoft.com/windows/windows-app-sdk/api/winrt/microsoft.ui.xaml.frameworkelement.focusvisualsecondarythickness
3. SAP Fiori content density (cozy and compact) — https://www.sap.com/design-system/fiori-design-web/v1-120/foundations/visual/cozy-compact ; Grid table usage — https://www.sap.com/design-system/fiori-design-web/v1-96/ui-elements/grid-table/usage
4. Carbon data table style — https://carbondesignsystem.com/components/data-table/style ; v10 — https://v10.carbondesignsystem.com/components/data-table/style ; issue on row heights — https://github.com/carbon-design-system/carbon/issues/8875
5. Fluent 2 — https://fluent2.microsoft.design/typography
6. Why use Segoe UI Variable? — https://tigeroakes.com/posts/segoe-ui-variable
7. Materials in Windows apps — https://learn.microsoft.com/windows/apps/design/signature-experiences/materials (not fetched; unverified)
8. Windows contrast themes — https://learn.microsoft.com/windows/apps/design/accessibility/high-contrast-themes (not fetched; unverified)
9. Fluent System Icons — https://github.com/microsoft/fluentui-system-icons (not fetched; unverified)
