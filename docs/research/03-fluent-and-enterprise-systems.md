# 03 — Fluent 2 / Windows 11 and the big enterprise design systems

**Verification status (2026-11-12 pass).** The first draft was written while the network blocked most sources. This pass re-checked every number against primary sources: Microsoft Learn pages, the WinUI source (microsoft/microsoft-ui-xaml), the Fluent UI token package (microsoft/fluentui), Carbon SCSS, Primer primitives, Polaris tokens, SAP theming-base-content, the Salesforce SLDS repo and the Qt docs. Tags: **[verified]** = read in a primary source in this pass (source in brackets); **(unverified)** = still not confirmable. Not reachable from this session even though listed as allowed: experience.sap.com, atlassian.design, fluent2.microsoft.design (hosts did not resolve or were blocked), so SAP prose guidance and all Atlassian values stay (unverified) or are substituted by SAP source tokens. See the Verification log at the end.

## TL;DR

- Windows 11 body text is Segoe UI Variable 14/20 [verified][1]. Caption is 12/16. Microsoft states minimum sizes of 14 px Semibold and 12 px Regular [verified][1]. For long sessions with older users, treat 14 px as the minimum for data and 12 px only for secondary hints.
- Windows 11 geometry: standard controls use a 4 px corner radius (`ControlCornerRadius`), transient overlays (dialogs, flyouts, menus) use 8 px (`OverlayCornerRadius`), ToolTip 4 px, windows 8 px (0 when snapped or maximized) [verified][10][12]. Default WinUI input controls are 32 px tall (TextBox, ComboBox min height); WinUI's own Compact density resource drops them to 24 px [verified][12].
- Focus visual: 2 px primary border outside, 1 px secondary border inside, default margin 1 px, in contrasting colours (light theme: outer #E4000000, inner #B3FFFFFF; dark theme: outer #FFFFFF, inner #B3000000) [verified][2][12]. Adopt unchanged.
- Mica is opaque and is for the long-lived base layer and title bar; Acrylic is for transient surfaces and Microsoft says not to put desktop acrylic on large background surfaces [verified][7]. Never put either behind data tables or thumbnails.
- Every dense enterprise system offers two or more density modes. SAP Horizon: cozy line height 44 px vs compact 32 px (control height 36 vs 26 px) [verified][19]. Never mix the two in one page (SAP guidance, snippet-verified earlier [3]).
- Carbon table rows: xs 24, sm 32, md 40, lg 48 (default), xl 64 px [verified][4]. Toolbar height should match row height.
- Table rows must have uniform height for stable scrolling (SAP guidance [3]). This matters for the thumbnail timeline and the Değerler table.
- Status must never be colour-only. Pair colour with an icon and a text label.
- Qt 6.7 added the native "windows11" style, used by default on Windows 11 from 6.7 [verified][15]. Mica is set via `DwmSetWindowAttribute(DWMWA_SYSTEMBACKDROP_TYPE = 38)` with value 2 (main window = Mica), needs Windows 11 build 22621+ [verified][14]. Mica and Segoe UI Variable are Windows-only; other OSes need a fallback font and a flat layer.

## 1. Fluent 2 / Windows 11

### 1.1 Principles
Fluent 2 and Windows 11 design emphasise: natural on every platform, built for focus, one for all and all for one (accessible to everyone), and "delightful" through motion and material (unverified wording; fluent2.microsoft.design was not reachable [5]). The takeaway for a work tool: calm neutral surfaces, one accent colour, content first, depth conveyed by subtle layers and not by heavy chrome.

### 1.2 Type ramp (Segoe UI Variable, WinUI)
Windows 11 UI uses Segoe UI Variable. It has two axes: weight (Thin 100 to Bold 700; Light 300, Semilight 350, Regular 400, Semibold 600) and optical size (opsz), which is automatic and on by default, scaling from 8 pt to 36 pt [verified][1]. All values below are from the Microsoft Learn typography page and match the WinUI `TextBlock_themeresources.xaml` styles [verified][1][12]:

| Style (XAML key) | Weight | Size / line height (epx = px at 100 %) |
|---|---|---|
| Caption (`CaptionTextBlockStyle`) | Regular | 12 / 16 |
| Body (`BodyTextBlockStyle`) | Regular | 14 / 20 |
| Body Strong (`BodyStrongTextBlockStyle`) | SemiBold | 14 / 20 |
| Body Large (`BodyLargeTextBlockStyle`) | Regular | 18 / 24 |
| Body Large Strong (`BodyLargeStrongTextBlockStyle`) | SemiBold | 18 / 24 |
| Subtitle (`SubtitleTextBlockStyle`) | SemiBold | 20 / 28 |
| Title (`TitleTextBlockStyle`) | SemiBold | 28 / 36 |
| Title Large (`TitleLargeTextBlockStyle`) | SemiBold | 40 / 52 |
| Display (`DisplayTextBlockStyle`) | SemiBold | 68 / 92 |

Further rules from the same page [verified][1]: Bold and Italic are not part of the ramp (use Semibold; italic is excluded for dyslexia legibility); use sentence case for all UI text including titles; align left by default; truncate with ellipsis in most cases. The Fluent 2 web token ramp is different and finer: 10/14, 12/16, 14/20, 16/22, 20/28, 24/32, 28/36, 32/40, 40/52, 68/92 (`fontSizeBase100`–`Hero1000`, `lineHeightBase100`–`Hero1000`), weights 400/500/600/700 [verified][13].

Segoe UI covers Turkish glyphs (ç, ğ, ı, İ, ö, ş, ü) (unverified for Variable; test it).

### 1.3 Spacing and sizing
- 4 px grid is the underlying convention. Fluent 2 spacing tokens: 2, 4, 6, 8, 10, 12, 16, 20, 24, 32 px (`spacingXXS`…`XXXL`) [verified][13].
- Standard control height: 32 px. WinUI sources: `TextControlThemeMinHeight` 32, `ComboBoxMinHeight` 32, `CheckBoxHeight` 32, `TabViewItemMinHeight` 32; Button has no min height, its height comes from padding `11,5,11,6` plus 14 px text, giving about 32 px [verified][12].
- **WinUI Compact density** (`DensityStyles/Compact.xaml`), the only official compact values [verified][12]:

  | Resource | Default | Compact |
  |---|---|---|
  | TextControlThemeMinHeight (TextBox) | 32 | 24 |
  | ComboBoxMinHeight | 32 | 24 |
  | ListViewItemMinHeight | 40 | 32 |
  | TreeViewItemMinHeight | 28 | 24 |
  | NavigationViewItemOnLeftMinHeight | 36 | 32 |
  | ControlContentThemeFontSize | 14 | 14 (unchanged) |

  Compact reduces padding only; font stays 14 px. (The earlier claim "WinUI 2 compact resources at 24 px" is therefore confirmed for input controls, and also true in WinUI 3.)
- Touch target: Microsoft says 7.5 mm square (40 x 40 px at 135 PPI, 1.0x) [verified][23]. The earlier "44 px recommended" is not a Microsoft number; 44 px is Primer's coarse-pointer minimum [verified][16].
- Corner radius: `ControlCornerRadius` = 4 px, `OverlayCornerRadius` = 8 px, global resources overridable in App.xaml [verified][10][12]. 4 px: Button, CheckBox, ComboBox, TextBox, ListView, and bar shapes (ProgressBar, ScrollBar, Slider); 8 px: windows, ContentDialog, Flyout, MenuFlyout, TeachingTip; ToolTip is the 4 px exception; 0 px where straight edges meet (e.g. SplitButton halves) and for snapped or maximized windows [verified][10]. Fluent 2 web radius tokens are 0, 2, 4, 6, 8, 12, 16, 24, 32, 40 px, circular [verified][13].

### 1.4 Materials and elevation
- **Mica**: opaque, built from theme plus desktop wallpaper, for the base layer of long-lived windows; cheap because it samples the wallpaper once; falls back to a neutral colour when the app is inactive [verified][7]. **Mica Alt**: stronger tint, for tabbed title bars (Windows App SDK 1.1+, Windows 11 22000+) [verified][7].
- Mica falls back to a solid colour (`SolidBackgroundFillColorBase` for Mica, `…BaseAlt` for Mica Alt) when: High Contrast is on; Transparency is off in Settings; Battery Saver is on; low-end hardware; the window is deactivated; Windows is below build 22000 [verified][7].
- Layering: Mica as base layer, plus one content layer using `LayerFillColorDefaultBrush` (a low-opacity solid) laid over it; Mica Alt adds a commanding layer (`LayerOnMicaBaseAltFillColorDefaultBrush`) between [verified][7]. The earlier "8 px top-left radius on the content layer" is not stated on the Mica page (unverified).
- **Acrylic**: translucent and blurred, for transient surfaces. Microsoft: do not put desktop acrylic on large background surfaces; do not place multiple acrylic panes edge to edge (visible seam); do not put accent-coloured text or hyperlinks on acrylic (contrast fails at 14 px); use an opaque background for vertical panes that section off content; it is GPU-intensive and auto-disabled in Battery Saver or when Transparency is off [verified][7]. Recipe: background, blur, exclusion blend, tint, noise [verified][7].
- **Elevation values** (Windows 11 layering page): Window 128, Dialog 128, Flyout 32, Tooltip 16, Card 8, Control 2, Layer 1, each with a 1 px stroke [verified][11]. The earlier "2 / 8 / 32 px blur" figures were wrong or unfounded and are removed.
- **Fluent 2 shadow tokens** (web): each shadow is an ambient + key pair [verified][13]:

  | Token | CSS |
  |---|---|
  | shadow2 | 0 0 2px ambient, 0 1px 2px key |
  | shadow4 | 0 0 2px ambient, 0 2px 4px key |
  | shadow8 | 0 0 2px ambient, 0 4px 8px key |
  | shadow16 | 0 0 2px ambient, 0 8px 16px key |
  | shadow28 | 0 0 8px ambient, 0 14px 28px key |
  | shadow64 | 0 0 8px ambient, 0 32px 64px key |

  Light theme ambient/key = rgba(0,0,0,0.12) / rgba(0,0,0,0.14); dark theme = 0.24 / 0.28 (lighter and darker variants exist: light 0.06/0.07 and 0.20/0.24, dark 0.12/0.14 and 0.40/0.48) [verified][13].
- Do not stack Acrylic on Acrylic. For Evrakçı: use a solid layer behind page thumbnails, because translucency changes the apparent colour of scanned pages.

### 1.5 Colour
- **WinUI neutral layers** [verified][12]. Light: `SolidBackgroundFillColorBase` #F3F3F3, Secondary #EEEEEE, Tertiary #F9F9F9, Quarternary #FFFFFF; `LayerFillColorDefault` #80FFFFFF (50 % white, as guessed); `CardBackgroundFillColorDefault` #B3FFFFFF; text primary #E4000000, secondary #9E000000, disabled #5C000000; `ControlStrokeColorDefault` #0F000000; `SurfaceStrokeColorDefault` #66757575. Dark: Base #202020, Secondary #1C1C1C, Tertiary #282828, Quarternary #2C2C2C; `LayerFillColorDefault` #4C3A3A3A; card #0DFFFFFF; text primary #FFFFFF, secondary #C5FFFFFF, disabled #5DFFFFFF.
- **Fluent 2 web neutral tokens (webLightTheme)** [verified][13]: `colorNeutralBackground1` #FFFFFF, Background2 #FAFAFA, Background3 #F5F5F5, Background4 #F0F0F0, Background5 #EBEBEB, Background6 #E6E6E6; hover/pressed/selected for Background1: #F5F5F5 / #E0E0E0 / #EBEBEB; `colorNeutralForeground1` #242424, Foreground2 #424242, Foreground3 #616161, Foreground4 #707070, ForegroundDisabled #BDBDBD; `colorNeutralStroke1` #D1D1D1, Stroke2 #E0E0E0, Stroke3 #F0F0F0, `colorNeutralStrokeAccessible` #616161, StrokeDisabled #E0E0E0; focus strokes `colorStrokeFocus1` #FFFFFF (inner), `colorStrokeFocus2` #000000 (outer). Dark: Background1 #292929, Background2 #1F1F1F, Background3 #141414, Foreground1 #FFFFFF, Foreground2 #D6D6D6, Foreground3 #ADADAD, Stroke1 #666666, Stroke2 #525252.
- **Brand ramp** (`brandWeb`): 70 #115EA3, 80 #0F6CBD (`colorBrandBackground` and `colorCompoundBrandStroke` in light), 90 #2886DE, 100 #479EF5 (dark `colorBrandForeground1` is brand 100), 160 #EBF3FC [verified][13]. WinUI accent: the system accent drives `AccentFillColorDefault`; Windows' default blue is #0078D4 and WinUI's own fallback for light-theme accent fills is #0067C0 [partly verified][12]; for Evrakçı we pick a fixed accent (below), since the system accent may be anything.
- **Semantic colours (WinUI)** [verified][12]. Light: critical #C42B1C (background #FDE7E9), success #0F7B0F (background #DFF6DD), caution #9D5D00. Dark: critical #FF99A4 (background #442726), success #6CCB5F (background #393D1B), caution #FCE100. The earlier "unverified" hexes for light mode were correct.
- **High contrast**: four built-in themes, Aquatic, Desert, Dusk, Night sky; toggle with Left Alt + Left Shift + PrtScn [verified][8]. Use system colour keywords only. Microsoft adds: do not use `GrayText` for secondary or hint text (disabled only), and do not use `Hotlight` except for hyperlinks; hard-coded backgrounds break in contrast themes [verified][8].
- Text contrast: Microsoft requires at least 4.5:1 for visible text (WCAG G18) [verified][26].

### 1.6 Iconography
- **Fluent System Icons** (SVG) ship per icon in sizes from {12, 16, 20, 24, 28, 32, 48}; which sizes exist varies per icon (e.g. Document 16/20/24/28/32/48; Add 12/16/20/24/28/32/48; Save 16/20/24/28/32) [verified][9]. Styles: Regular, Filled, Light, and for some Color [verified][9]. Use Regular by default and Filled for selected or emphasised.
- **Segoe Fluent Icons** (font) recommended sizes: 16, 20, 24, 32, 40, 48, 64 [verified][25]. Microsoft says the font is not meant for inline use with text [verified][25].
- CommandBar: icons are 20 x 20 px in the primary area and 16 x 16 in the overflow menu [verified][22]. Inline icons beside 14 px text: 16 px (convention).

### 1.7 Controls worth copying
- **Button**: about 32 px tall, 4 px radius, padding `11,5,11,6`, accent filled for the single primary action [verified][12]. Fluent 2 web Button heights: small 24, medium 32, large 40 (field heights) [verified][13]; Fluent 2 web Button medium: 14/20 text, min width 96 px [verified][13].
- **CommandBar**: icon buttons with an optional "…" overflow; compact closed height `AppBarThemeCompactHeight` 48 px, expanded `AppBarThemeMinHeight` 64 px (labels below icons) [verified][12]. The earlier "40 px compact" is wrong for the default (40 appears only in media transport controls).
- **NavigationView**: expanded left pane 320 px, compact pane 48 px, item min height 36 px (32 in Compact density) [verified][12]; expanded pane at window width 1008 px or more, compact 641–1007, minimal 640 or less; header area 52 px [verified][21]. Top mode is recommended for 5 or fewer top-level categories [verified][21]; the earlier "5–7" was too generous. Our six tabs are borderline for a top NavigationView; a tab strip or a left compact rail is safer.
- **TabView**: items min height 32 px, close button 24 px [verified][12]. Only useful if tabs are documents.
- **InfoBar**: inline, persistent, app-wide status message with severities, optional action, dismissable; Microsoft suggests a Flyout for non-persistent in-context information [verified][24]. Use instead of toasts for anything staff must not miss.
- **TeachingTip**: anchored, dismissible popover for first-run guidance; 8 px radius [verified][10]. Useful for Rehber.
- **ProgressRing / ProgressBar**: determinate when a percentage is known; indeterminate only otherwise (convention).
- **ListView / TreeView**: ListViewItem min height 40 (32 compact), TreeViewItem 28 (24 compact) [verified][12].
- **ScrollBar**: `ScrollBarSize` 12 [verified][12].
- **DataGrid**: WinUI has no first-party grid; the Community Toolkit DataGrid default row height is 32 px (unverified). Fluent 2 web Table rows: medium 44, small 34, extra-small 24 px, 1 px `colorNeutralStroke2` bottom border [verified][13].

### 1.8 Focus visuals
WinUI "high visibility focus visuals": primary border 2 px thick, running around the outside of a 1 px secondary border; default `FocusVisualMargin` 1 px away from the control bounds; properties `FocusVisualPrimaryThickness=2`, `FocusVisualSecondaryThickness=1`; `UseSystemFocusVisuals` can disable; colours via `FocusVisualPrimaryBrush` and `FocusVisualSecondaryBrush` [verified][2][12]. Colours: light theme outer `FocusStrokeColorOuter` #E4000000, inner `FocusStrokeColorInner` #B3FFFFFF; dark theme outer #FFFFFF, inner #B3000000 [verified][12]. "Reveal focus" (animated border glow) is for the 10-foot / gamepad / keyboard experience [verified][2]. That focus shows for keyboard but not mouse click is the standard behaviour (unverified here). Fluent 2 web uses a 2 px outline in `colorStrokeFocus2` (black in light) plus `colorStrokeFocus1` (white) inner, only on keyboard navigation [partly verified][13].

### 1.9 Keyboard: access keys and accelerators
Access keys are Alt plus mnemonic keys pressed sequentially, with key tips shown [verified][27]. Accelerators (Ctrl+letter) are shown in menu text. Microsoft's standard shortcut table includes Ctrl+Z, Ctrl+F, F3 (next search result), F6 (go to next UI pane) and Shift+F6 (previous pane) [verified][20]. Keep Esc to dismiss, Enter to activate the default, Space to toggle, arrows inside composite controls. Keep standard Windows shortcuts intact: Ctrl+Z / Ctrl+Y undo and redo, Ctrl+S, Ctrl+F, F1 help.

### 1.10 High-contrast mode
In high contrast, Windows replaces colours with system keywords; borders become essential because shadows and fills vanish. Never rely on subtle fills for state. Selected = Highlight/HighlightText; disabled = GrayText only; links = Hotlight only [verified][8]. Fluent web components also switch to `Highlight` borders under `forced-colors` [verified][13]. In Qt, `QPalette` follows the system high-contrast palette if the app doesn't override it, so custom QSS that hard-codes colours will break it. Provide a "use system colours" switch and test with Left Alt + Left Shift + PrtScn.

## 2. Dense-productivity systems compared

| System | Grid / base | Type (body) | Density modes | Control / row heights |
|---|---|---|---|---|
| IBM Carbon | 8 px mini unit, 2x grid (unverified) | IBM Plex Sans; `body-compact-01` 14/18, `body-01` 14/20, `body-compact-02` 16/22, `body-02` 16/24, `label-01` 12/16 [verified][4] | Productive vs expressive type sets; table row sizes xs–xl | Table rows xs 24, sm 32, md 40, lg 48 (default), xl 64 [verified][4] |
| SAP Fiori (Horizon) | rem-based (unverified step) | "72" font, `--sapFontSize` 14 px (0.875rem); small 12, large 16, headers 14/16/20/24/32/48 [verified][19] | Cozy vs Compact | Cozy: element line height 44, control height 36; Compact: 32 and 26 [verified][19]. List item 44 / 32 [verified][19]. Condensed table density (unverified) |
| Atlassian | 8 px base (unverified) | 14 px body (unverified) | (unverified) | (unverified; atlassian.design unreachable) |
| GitHub Primer | 4 px base units (`base.size.4`…) | 14 px body (`text.size.sm`); caption 12; line-heights tight 1.25, snug 1.375, normal 1.5, relaxed 1.625 [verified][16] | Table cell padding condensed / normal / spacious [verified][16] | Controls xsmall 24, small 28, medium 32, large 40, xlarge 48; min touch target 16 fine / 44 coarse [verified][16]. Table cell padding (block x inline): condensed 4 x 8, normal 8 x 12, spacious 12 x 16 px, 20 px line height, so rows about 28 / 36 / 44 px plus border (derived) [verified][16] |
| Shopify Polaris | 4 px tokens (`space-100` = 4 px; 200 = 8; 300 = 12; 400 = 16) [verified][17] | `body-md` 13/20, `body-sm` 12/16 [verified][17] | Button heights step down on md+ viewports | Button: micro 28 mobile / 24 desktop; medium 32 / 28; large 36 / 32; `--pg-control-height` 32; IndexTable cell padding 6 px (`space-150`) [verified][17] |
| Salesforce Lightning (SLDS) | 4 px; rem tokens | 13 px base (unverified) | "Comfy" vs "Compact" density setting (SLDS docs page exists, content not extractable) | Fixed table header height 2rem (32 px); other row sizes (unverified) [partly verified][18] |

Findings confirmed:
- **Carbon**: row sizes xs 24 / sm 32 / md 40 / lg 48 / xl 64; default is lg 48 (`block-size: $spacing-09`, 3 rem); rows use `min-block-size` in the auto-height variants so wrapped content can grow; the old (v10) documented heights 24 / 32 / 48 / 64 correspond to compact / short / default / tall [verified][4]. Toolbar, batch action bar and pagination heights should match row height; xl rows recommended only for two-line cell content (snippet-verified [4]). Carbon type: scale steps 12, 14, 16, 18, 20, 24, 28, 32, 36 px; `heading-compact-01` 14/18 semibold, `heading-compact-02` 16/22 semibold, `label-01` 12/16 with 0.32 px letter spacing [verified][4]. The first draft mislabelled `body-01` as 14/18; the 14/18 style is `body-compact-01`.
- **SAP**: compact for keyboard-and-mouse desktop; one density across the whole app, never mixed; all line items one height (snippet-verified [3]). Horizon focus: 2 px solid (`--sapContent_FocusWidth` .125rem), colour #0032A5 [verified][19]. SAP's own text said the compact touch area is 32; the tokens show that 32 is the compact line height and 26 the compact control height.
- **Primer**: the "spacious" mode has 12 x 16 padding; "condensed" 4 x 8 [verified][16]. Primer radius tokens: small 3, medium 6, large 12 px [verified][16].

### What makes data-dense enterprise UIs work (synthesis)
1. **A density switch, defaulted by input device.** Desktop keyboard users get compact; give older users an easy "Comfortable" option.
2. **Uniform row heights** with truncation plus tooltip, instead of wrapping, so scroll position is predictable.
3. **Aligned columns**: text left, numbers right, header aligned with its data; sticky header.
4. **Inline editing** with an obvious edit state: Enter or F2 to edit, Enter to commit, Esc to revert, Tab to move to the next cell; a changed-cell marker until confirmed. Carbon, SAP and Lightning all follow this pattern (unverified for details).
5. **Status as icon + word + colour**, in a dedicated narrow column, with the same vocabulary everywhere.
6. **Zebra or thin row separators**, not both; 1 px separators with a hover and a clearly different selected row (Fluent 2 web tables use only a 1 px bottom border [verified][13]).
7. **Batch toolbar that replaces the normal toolbar** when rows are selected (Carbon) [4].
8. **Persistent, quiet chrome** so content has the contrast budget.

## Rules we should adopt for Evrakçı

1. Base UI font 14 px / 20 px line height (Body, 14/20 [verified]). Nothing in the working area below 12 px; 12 px (Caption 12/16) only for captions and secondary hints; Microsoft's own floor is 14 px Semibold / 12 px Regular. Offer a text-size setting of 100 / 115 / 130 %. Emphasis by SemiBold (600), never Bold or Italic.
2. Use Segoe UI Variable on Windows (fall back to Segoe UI, then Noto Sans/Inter on Linux, system font on macOS). Test every Turkish diacritic including dotted İ and dotless ı.
3. Layout on a 4 px grid; gaps drawn only from 4, 8, 12, 16, 24 px (all exist in Fluent 2 spacing tokens).
4. Controls: 32 px tall in "Normal" (= WinUI default), 28 px in "Compact" (between WinUI Compact 24 and Normal 32; we choose it because 24 px is too small for older users), 40 px in "Comfortable" (= Fluent 2 large field and WinUI ListViewItem default 40). Table row heights: 32 / 28 / 40 px respectively, uniform within a table. Reference points: WinUI list item 40 default / 32 compact; Carbon sm 32 / md 40; Fluent 2 table 34 / 44.
5. Radii: 4 px on controls (`ControlCornerRadius`), 8 px on dialogs, popups and windows (`OverlayCornerRadius`), tooltips 4 px. No other radii.
6. Focus ring on every focusable element: 2 px outer plus 1 px inner, 1 px margin, outer #E4000000-equivalent (near black) and inner white in light theme, reversed in dark (WinUI values); visible on keyboard focus, never removed.
7. Single accent colour for primary button, selection and focus. At most one primary button per view.
8. Opaque, flat surfaces behind data (tables, thumbnails). Mica is optional on the title bar and sidebar only, and must degrade to a solid fill (#F3F3F3 light, #202020 dark).
9. Status uses icon + text + colour; never colour alone. Same four severities everywhere: info, success, warning, error. Use WinUI light-theme semantic colours as the starting point: critical #C42B1C, success #0F7B0F, caution #9D5D00; dark: #FF99A4, #6CCB5F, #FCE100. Verify 4.5:1 for text.
10. Persistent problems use an inline InfoBar-style banner at the top of the page; toasts only for completed, non-critical events.
11. Every action reachable by keyboard; show accelerators in menus and tooltips; Alt access keys for the six tabs; F6 / Shift+F6 cycle regions; undo/redo Ctrl+Z / Ctrl+Y.
12. Editable tables: Enter/F2 edit, Enter commit, Esc cancel, Tab next cell; edited-but-unconfirmed cells carry a visible marker.
13. Toolbar height equals the row height of the density mode; a selection toolbar replaces the normal one when items are selected.
14. Honour the OS high-contrast palette: when active, drop custom colours and use palette roles only; borders (1 px) must carry state, not fills; no GrayText except disabled.
15. Do not mix density modes on one screen; density is an app-level setting.
16. Icons: Fluent System Icons Regular (Filled for selected) as SVG at 16 px inline, 20 px in toolbars, 24 px for large actions (sizes 16/20/24 exist for essentially all icons).
17. Shadows only for transient layers: use Fluent 2 `shadow8` for menus and `shadow28` or `shadow64` for dialogs; no shadows on cards in the working area (borders instead, 1 px `colorNeutralStroke2` #E0E0E0 light).

## Qt/PySide6 feasibility notes

- **Qt 6 "windows11" style**: added in Qt 6.7 ("Added Windows 11 style"); on systems running Windows 11 and above it is used by default, and supports Windows dark mode [verified][15]. `QStyleFactory` documents the key "windows11" ("follows the Windows 11 Fluent design") alongside "windowsvista", "macos", "android", and always-available "windows" and "fusion" [verified][15]. `QApplication.setStyle("windows11")` therefore works from 6.7; that it falls back to another style off Windows is plausible but not stated (unverified). Fusion is the cross-platform base for our own styling. Qt 6.8 added "FluentWinUI3" but that is a Qt Quick Controls style, not Widgets [verified][15]. `QStyleHints.colorScheme()` exists since Qt 6.5; a setter (`setColorScheme`, `unsetColorScheme`) since 6.8 [verified][15]. Pin PySide6 >= 6.8 if we want a user-selectable dark/light override.
- **Mica from PySide6**: call `DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE = 38, &value, 4)` through `ctypes.windll.dwmapi` on Windows 11 build 22621+ [verified][14]. `DWM_SYSTEMBACKDROP_TYPE` values (enum order): 0 `DWMSBT_AUTO` (DWM decides; may draw none), 1 `DWMSBT_NONE`, 2 `DWMSBT_MAINWINDOW` (Mica), 3 `DWMSBT_TRANSIENTWINDOW` (Desktop Acrylic, brightest variant), 4 `DWMSBT_TABBEDWINDOW` (Mica Alt) [verified][14]. The numeric values 0–4 follow the enum order in the documented declaration; the docs do not print them explicitly. Dark title bar: `DWMWA_USE_IMMERSIVE_DARK_MODE` = 20 (BOOL), supported from build 22000, and windows default to light mode regardless of the system setting [verified][14]. Also available: `DWMWA_WINDOW_CORNER_PREFERENCE` = 33, `DWMWA_BORDER_COLOR` 34, `DWMWA_CAPTION_COLOR` 35, `DWMWA_TEXT_COLOR` 36 (all build 22000+) [verified][14]. Qt side: the window needs `WA_TranslucentBackground` and content widgets must paint transparent where Mica should show through; extending the frame (`DwmExtendFrameIntoClientArea`) may be needed (unverified). Wrap in a version check and try/except; no Mica on Windows 10 or other OSes.
- **Segoe UI Variable**: ships with Windows 11 only (not Windows 10 unless updated), and is not redistributable as a file we can bundle (unverified licence detail). Because the optical size axis is automatic when the variable font is used [verified][1], the "Text" vs "Display" family choice only matters if Qt resolves static named instances; use the family list "Segoe UI Variable Text", "Segoe UI", sans-serif and check the result on a real machine (unverified family names).
- **QSS limits**: QSS cannot do box-shadow, backdrop blur, transitions, or a two-ring focus (outline is unsupported); `border-radius` and `border` work. Build the double focus ring with a custom `QProxyStyle` or a painted overlay, or approximate with a 2 px accent border plus an inner 1 px white via nested widgets. Use QSS only for colours and radii; use `QPalette` for system integration so high contrast keeps working. Prefer a small custom `QStyle` or `QProxyStyle` over deep QSS for a consistent look and for density tokens. (unverified; general Qt knowledge)
- **Fonts and DPI**: Qt 6 enables high-DPI scaling by default; use `QFontMetrics` and logical px, avoid hard-coded pixel icons; render icons as SVG (Fluent System Icons are available as SVG, e.g. `ic_fluent_save_16_regular.svg`) at 16/20/24 px [verified][9].
- **Cross-platform**: on Linux and macOS keep the same layout tokens, with a flat solid background and the platform font.

## Sources (all accessed 2026-11-12)

1. Typography in Windows 11 — https://learn.microsoft.com/windows/apps/design/signature-experiences/typography (fetched)
2. Guidelines for visual feedback / focus visuals — https://learn.microsoft.com/windows/apps/develop/input/guidelines-for-visualfeedback (fetched)
3. SAP Fiori content density (cozy and compact) — https://www.sap.com/design-system/fiori-design-web/v1-120/foundations/visual/cozy-compact ; Grid table usage — https://www.sap.com/design-system/fiori-design-web/v1-96/ui-elements/grid-table/usage (search-snippet evidence only; experience.sap.com did not resolve in this pass)
4. Carbon: data-table SCSS (`packages/styles/scss/components/data-table/_data-table.scss`), type styles (`packages/type/scss/_styles.scss`, `_scale.scss`) — https://github.com/carbon-design-system/carbon (read from a shallow clone); style page — https://carbondesignsystem.com/components/data-table/style (snippet only) ; issue — https://github.com/carbon-design-system/carbon/issues/8875
5. Fluent 2 — https://fluent2.microsoft.design/typography (not reachable in this pass)
6. Why use Segoe UI Variable? — https://tigeroakes.com/posts/segoe-ui-variable (not re-fetched)
7. Mica — https://learn.microsoft.com/windows/apps/design/style/mica ; Acrylic — https://learn.microsoft.com/windows/apps/design/style/acrylic (fetched)
8. Contrast themes — https://learn.microsoft.com/windows/apps/design/accessibility/high-contrast-themes (fetched)
9. Fluent System Icons — https://github.com/microsoft/fluentui-system-icons (asset `metadata.json` files fetched)
10. Geometry in Windows 11 — https://learn.microsoft.com/windows/apps/design/signature-experiences/geometry (fetched)
11. Layering and elevation — https://learn.microsoft.com/windows/apps/design/signature-experiences/layering (fetched)
12. WinUI source, microsoft/microsoft-ui-xaml (shallow clone, HEAD 2a732746): `controls/dev/CommonStyles/CornerRadius_themeresources.xaml`, `TextBlock_themeresources.xaml`, `Common_themeresources_any.xaml`, `ListViewItem_themeresources.xaml`, `CommandBar_themeresources.xaml`, `Button_themeresources.xaml`, `controls/dev/dll/DensityStyles/Compact.xaml`, `NavigationView/`, `TabView/`, `TreeView/`, `dxaml/xcp/dxaml/themes/generic.xaml` — https://github.com/microsoft/microsoft-ui-xaml
13. Fluent UI tokens, microsoft/fluentui `packages/tokens/src` (global/fonts.ts, borderRadius.ts, spacings.ts, strokeWidths.ts, durations.ts, alias/lightColor.ts, alias/darkColor.ts, global/brandColors.ts, utils/shadows.ts) and `packages/react-components` (Button, Input, TableRow styles) — https://github.com/microsoft/fluentui (raw files)
14. DWM_SYSTEMBACKDROP_TYPE — https://learn.microsoft.com/windows/win32/api/dwmapi/ne-dwmapi-dwm_systembackdrop_type ; DWMWINDOWATTRIBUTE — https://learn.microsoft.com/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute (fetched)
15. Qt docs: What's New in Qt 6.7 / 6.8 / 6.6, QStyleFactory, QStyleHints — https://doc.qt.io/qt-6/whatsnew67.html , https://doc.qt.io/qt-6/whatsnew68.html , https://doc.qt.io/qt-6/qstylefactory.html , https://doc.qt.io/qt-6/qstylehints.html (fetched)
16. Primer primitives `src/tokens/functional/size/size.json5`, `radius.json5`, `base/typography`, and Primer React `DataTable/Table.module.css` — https://github.com/primer/primitives , https://github.com/primer/react (shallow clones)
17. Polaris `polaris-tokens/src/themes/base/{size,height,font,text,space,border}.ts`; `polaris-react` Button, TextField, IndexTable CSS, `AppProvider/global.css` — https://github.com/Shopify/polaris (shallow clone)
18. Salesforce SLDS `ui/components/data-tables/base/_index.scss` — https://github.com/salesforce-ux/design-system (sparse clone)
19. SAP theming-base-content, `sap_horizon/css_variables.css` — https://github.com/SAP/theming-base-content ; SAP UI5 Web Components `themes/base/sizes-parameters.css` — https://github.com/SAP/ui5-webcomponents (raw files)
20. Keyboard accelerators — https://learn.microsoft.com/windows/apps/design/input/keyboard-accelerators (fetched)
21. NavigationView — https://learn.microsoft.com/windows/apps/design/controls/navigationview (fetched)
22. Command bar — https://learn.microsoft.com/windows/apps/design/controls/command-bar (fetched)
23. Guidelines for touch targets — https://learn.microsoft.com/windows/apps/design/input/guidelines-for-targeting (fetched)
24. InfoBar — https://learn.microsoft.com/windows/apps/design/controls/infobar (fetched)
25. Segoe Fluent Icons font — https://learn.microsoft.com/windows/apps/design/style/segoe-fluent-icons-font (fetched)
26. Accessible text requirements — https://learn.microsoft.com/windows/apps/design/accessibility/accessible-text-requirements (fetched)
27. Access keys — https://learn.microsoft.com/windows/apps/design/input/access-keys (fetched)

## Verification log (2026-11-12)

**Corrected (first draft was wrong)**
- Type ramp: Body Large 18/24 and Title Large 40/52 and Body Strong 14/20 SemiBold confirmed; added missing Body Large Strong 18/24 SemiBold. Caption is called "Small" in the table but `CaptionTextBlockStyle` in XAML. The draft's claim that Text/Display optical sizes must be chosen by size was replaced: opsz is automatic.
- NavigationView items are 36 px (not 40) and 32 px in Compact; top mode is for 5 or fewer categories (not 5–7).
- CommandBar compact height is 48 px (not 40); expanded 64.
- Touch target: Microsoft says 40 x 40 px (7.5 mm); the "44 recommended" was not from Microsoft.
- Elevation: replaced the invented "2 px / 8 px / 32 px blur" with Microsoft's elevation values (Window 128, Dialog 128, Flyout 32, Tooltip 16, Card 8, Control 2, Layer 1) and the Fluent 2 shadow2–shadow64 token definitions.
- Mica: removed the unsupported "8 px top-left radius" statement; added the actual fallback conditions (including low-end hardware, window deactivated, build below 22000) and Mica Alt.
- Carbon: `body-01` is 14/20; 14/18 is `body-compact-01`; the "productive vs expressive" table row rewritten; row heights now xs 24 / sm 32 / md 40 / lg 48 / xl 64 (confirmed from SCSS; v10 values 24/32/48/64 map to compact/short/default/tall).
- SAP: "compact 32 px" corrected: 32 is the compact element line height (touch area), compact control height is 26 px; cozy 44 / 36.
- Qt: windows11 style added in Qt 6.7 and default on Windows 11 from 6.7 (confirmed); the "falls back to windowsvista elsewhere" claim is not in the docs and is tagged unverified; `colorScheme()` exists since 6.5 and the setter since 6.8 (draft said "6.8+ follows the scheme").
- Light-theme semantic colour hexes (#C42B1C, #0F7B0F, #9D5D00) and layer colour 50 % white confirmed from WinUI source; draft's "#0067C0 light / #60CDFF dark" accent is only partly supported (#0067C0 is WinUI's fallback; accent is system-driven).
- Primer body line height is a 1.5 multiplier at the token level (DataTable uses 20 px); draft's "14/20" is the DataTable value only.

**Confirmed unchanged**: radii 4/8; focus 2 px + 1 px; controls 32 px; DWMWA_SYSTEMBACKDROP_TYPE = 38 and Mica value 2; DWMWA_USE_IMMERSIVE_DARK_MODE = 20; build 22621 for backdrop type; F6 pane cycling; four contrast themes; Carbon toolbar-matches-row-height (snippet); Fluent System Icons sizes (12–48, per-icon) and styles.

**Added**: WinUI Compact density table; Fluent 2 web tokens (colour neutrals light/dark, brand ramp, spacing, radii, font ramp, durations not used); Fluent 2 field heights 24/32/40 and table rows 24/34/44; Primer control sizes 24/28/32/40/48 and table padding modes; Polaris text and button heights; SLDS table header 32 px; SAP Horizon tokens and focus; DWM_SYSTEMBACKDROP_TYPE 0–4 mapping; Segoe Fluent Icons recommended sizes; InfoBar/TabView/TreeView/ScrollBar values; new rules 16 and 17.

**Still (unverified)**: Fluent 2 principles wording; Segoe UI Variable Turkish glyph coverage and bundling licence; Community Toolkit DataGrid 32 px rows; SAP condensed table density and row heights, and SAP prose guidance (page unreachable); all Atlassian values (atlassian.design did not resolve; the Atlassian token source is not on public GitHub); SLDS base font size, density row heights, and comfy/compact mechanics; Carbon grid (16 columns, 2x); `QApplication.setStyle("windows11")` fallback off Windows; `WA_TranslucentBackground` and `DwmExtendFrameIntoClientArea` requirement for Mica; Segoe UI Variable family names in Qt; keyboard-only focus-visual default in WinUI; QSS limitations.
