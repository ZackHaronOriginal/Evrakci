# Fluent 2 / Windows 11 values with sources

Legend: **verified** = read from the named source; **unverified (memory)** = not obtained from a
source, treat as a hint only. Built 2026-11-26.

Sources
- P1 = `@fluentui/tokens@1.0.0-alpha.25` (MIT), files under `lib/` (global/*.js, alias/*.js,
  utils/shadows.js). `@fluentui/react-theme@9.2.3` (MIT) only re-exports P1.
- X1 = microsoft-ui-xaml `dxaml/xcp/dxaml/themes/generic.xaml` (raw file on main). It is the
  older OS-level generic theme, so its values are legacy WinUI sizes; the newer
  `dev/CommonStyles/*` files were not found at the paths tried.
- L-geo = https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/geometry
- L-typ = https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/typography
- L-mot = https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/motion
- L-col = https://learn.microsoft.com/en-us/windows/apps/design/signature-experiences/color
- L-ico = https://learn.microsoft.com/en-us/windows/apps/design/iconography/
- L-amp = https://learn.microsoft.com/en-us/windows/apps/develop/ui/alignment-margin-padding
- L-dlg = https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/dialogs-and-flyouts/dialogs
- L-ib = https://learn.microsoft.com/en-us/windows/apps/develop/ui/controls/infobar
- F2-lay = https://fluent2.microsoft.design/layout (fetched; spacing ramp only)

Pages that did not open (404): Learn "layout/spacing", the Windows toast UX guidance page.
fluent2 `/motion` opened but gives no numbers. WinUI `dev/CommonStyles/*` paths 404.

## 1. Spacing (P1 `global/spacings.js`, same values horizontal and vertical) - verified

| Token suffix | px |
|---|---|
| None | 0 |
| XXS | 2 |
| XS | 4 |
| SNudge | 6 |
| S | 8 |
| MNudge | 10 |
| M | 12 |
| L | 16 |
| XL | 20 |
| XXL | 24 |
| XXXL | 32 |

Names: `spacingHorizontal<Suffix>` / `spacingVertical<Suffix>`.
F2-lay ramp (verified): 0, 2, 4, 6, 8, 10, 12, 16, 20, 24, 28, 32, 36, 40, 48, 52, 56; base
unit 4.
L-amp (verified): dimensions, margins and padding in multiples of 4 epx; gutters 12 epx under
640 px window width, 24 epx above.

## 2. Corner radius (P1 `global/borderRadius.js`) - verified

| Token | px |
|---|---|
| None | 0 |
| Small | 2 |
| Medium | 4 |
| Large | 6 |
| XLarge | 8 |
| 2XLarge | 12 |
| 3XLarge | 16 |
| 4XLarge | 24 |
| 5XLarge | 32 |
| 6XLarge | 40 |
| Circular | 10000 |

Windows 11 usage (L-geo, verified): 4 px for in-page controls (Button, CheckBox, ComboBox,
TextBox, ListView) and bars (ProgressBar, ScrollBar, Slider); 8 px for top-level and transient
overlays (windows, flyouts, dialogs, MenuFlyout, TeachingTip); ToolTip 4 px; 0 where straight
edges meet or the window is snapped or maximized. XAML globals: ControlCornerRadius 4,
OverlayCornerRadius 8.

## 3. Stroke width (P1 `global/strokeWidths.js`) - verified

Thin 1, Thick 2, Thicker 3, Thickest 4 px. Icon glyph stroke: 1 epx monoline (L-ico, verified).

## 4. Type (P1 `global/fonts.js`, `typographyStyles.js`) - verified

Font sizes: Base100 10, Base200 12, Base300 14, Base400 16, Base500 20, Base600 24, Hero700 28,
Hero800 32, Hero900 40, Hero1000 68. Line heights: 14, 16, 20, 22, 28, 32, 36, 40, 52, 92.
Weights: Regular 400, Medium 500, Semibold 600, Bold 700.
Families: Base `'Segoe UI', 'Segoe UI Web (West European)', -apple-system, BlinkMacSystemFont,
Roboto, 'Helvetica Neue', sans-serif`; Monospace Consolas; Numeric Bahnschrift then Segoe UI.

| Style (P1) | size / line | weight |
|---|---|---|
| caption2 / caption2Strong | 10 / 14 | 400 / 600 |
| caption1 / caption1Strong | 12 / 16 | 400 / 600 |
| body1 / body1Strong | 14 / 20 | 400 / 600 |
| body2 | 16 / 22 | 400 |
| subtitle2 | 16 / 22 | 600 |
| subtitle1 | 20 / 28 | 600 |
| title3 | 24 / 32 | 600 |
| title2 | 28 / 36 | 600 |
| title1 | 32 / 40 | 600 |
| largeTitle | 40 / 52 | 600 |
| display | 68 / 92 | 600 |

Windows 11 type ramp (L-typ, verified), Segoe UI Variable: Caption 12/16; Body 14/20; Body
Strong 14/20 semibold; Body Large 18/24; Subtitle 20/28 semibold; Title 28/36 semibold; Title
Large 40/52; Display 68/92. Learn minimums: 14 px semibold or 12 px regular; sentence case;
left aligned; no bold or italic in the ramp; 50-60 characters per line.

## 5. Motion

| Item | Value | Source | Flag |
|---|---|---|---|
| Durations | UltraFast 50, Faster 100, Fast 150, Normal 200, Gentle 250, Slow 300, Slower 400, UltraSlow 500 ms | P1 `global/durations.js` | verified |
| Curves | AccelerateMax (0.9,0.1,1,0.2); AccelerateMid (1,0,1,1); AccelerateMin (0.8,0,0.78,1); DecelerateMax (0.1,0.9,0.2,1); DecelerateMid (0,0,0,1); DecelerateMin (0.33,0,0.1,1); EasyEaseMax (0.8,0,0.2,1); EasyEase (0.33,0,0.67,1); Linear | P1 `global/curves.js` | verified |
| Windows direct entrance | cubic-bezier(0,0,0,1), 167 / 250 / 333 ms | L-mot | verified |
| Windows point to point | (0.55,0.55,0,1), 167 / 250 / 333 ms | L-mot | verified |
| Windows direct exit | (0,0,0,1), 167 ms, always with a fade out | L-mot | verified |
| Windows gentle exit | (1,0,1,1), 167 ms | L-mot | verified |
| Fade only | linear, 83 ms | L-mot | verified |
| InfoBar | stays until closed by the user or the state resolves; avoid flashing in and out | L-ib | verified |
| Windows app notification (toast) on screen: 5 s default, 25 s long | 5 s / 25 s | none opened | unverified (memory) |
| In-app toast / snackbar auto-dismiss | about 5-7 s | none opened | unverified (memory) |

## 6. Shadow (P1 `utils/shadows.js`, colours from `alias/lightColor.js`) - verified

Form: `0 0 BLUR ambient, 0 Y BLUR key`.
shadow2 `0 0 2px A, 0 1px 2px K`; shadow4 `0 0 2px A, 0 2px 4px K`; shadow8 `0 0 2px A, 0 4px
8px K`; shadow16 `0 0 2px A, 0 8px 16px K`; shadow28 `0 0 8px A, 0 14px 28px K`; shadow64
`0 0 8px A, 0 32px 64px K`.
Light: A = rgba(0,0,0,0.12), K = rgba(0,0,0,0.14). Dark: A = 0.24, K = 0.28
(`alias/darkColor.js`). Lighter / Darker variants (light): 0.06 / 0.07 and 0.20 / 0.24. Brand
shadow A 0.30, K 0.25. Overlay scrim: light black 40 %, dark 50 % (`colorBackgroundOverlay`).

## 7. Colour aliases (P1 `alias/lightColor.js`, `darkColor.js`, `highContrastColor.js`) - verified

Grey ramp (`global/colors.js`), grey[N] is neutral: 4 `#0a0a0a`, 8 `#141414`, 12 `#1f1f1f`,
14 `#242424`, 16 `#292929`, 20 `#333333`, 26 `#424242`, 38 `#616161`, 82 `#d1d1d1`,
88 `#e0e0e0`, 92 `#ebebeb`, 94 `#f0f0f0`, 96 `#f5f5f5`, 98 `#fafafa`. Web brand ramp
(`global/brandColors.js`, brandWeb): 40 `#0c3b5e`, 60 `#0f548c`, 70 `#115ea3`, 80 `#0f6cbd`,
100 `#479ef5`, 110 `#62abf5`, 160 `#ebf3fc`. Fluent has no green brand; our cabinet green is a
custom brand.

| Role | Light | Dark | High contrast |
|---|---|---|---|
| Foreground1 (text) | grey14 `#242424` | white | CanvasText `#ffffff` |
| Foreground2 | grey26 `#424242` | grey84 `#d6d6d6` | `#ffffff` |
| Foreground3 | grey38 `#616161` | grey68 `#adadad` | |
| Foreground disabled | grey74 `#bdbdbd` | grey36 `#5c5c5c` | `#3ff23f` |
| Background1 (surface) | white | grey16 `#292929` | Canvas `#000000` |
| Background2 | grey98 `#fafafa` | grey12 `#1f1f1f` | `#000000` |
| Background3 | grey96 `#f5f5f5` | grey8 `#141414` | |
| Background4 | grey94 `#f0f0f0` | grey4 `#0a0a0a` | |
| Background5 | grey92 `#ebebeb` | black | |
| Background6 | grey90 `#e6e6e6` | grey20 `#333333` | |
| Background1 hover / pressed / selected | grey96 / grey88 / grey92 | grey24 / grey12 / grey22 | Highlight `#1aebff` |
| Subtle background hover / pressed / selected | grey96 / grey88 / grey92 | grey22 / grey18 / grey20 | Highlight |
| Card background | grey98 | grey20 | Canvas |
| Stroke1 | grey82 `#d1d1d1` | grey40 `#666666` | `#ffffff` |
| Stroke2 | grey88 `#e0e0e0` | grey32 `#525252` | `#ffffff` |
| Stroke accessible (3:1 edges) | grey38 `#616161` | grey68 `#adadad` | `#ffffff` |
| Stroke disabled | grey88 | grey26 | `#3ff23f` |
| Brand background (primary button) | brand80 `#0f6cbd` | brand70 `#115ea3` | ButtonFace `#ffffff` |
| Brand bg hover / pressed | brand70 / brand40 | brand80 / brand40 | Highlight |
| Foreground on brand | white | white | ButtonText `#000000` |
| Link | brand70 `#115ea3` | brand100 `#479ef5` | Hyperlink `#ffff00` |
| Compound brand stroke (input bottom, focus accent) | brand80 | brand100 | Highlight |
| Focus stroke 1 / 2 (inner / outer) | white / black | black / white | Canvas / Highlight |

HC constants (`global/colors.js`): Hyperlink `#ffff00`, Highlight `#1aebff`, Disabled
`#3ff23f`, Canvas `#000000`, CanvasText `#ffffff`, HighlightText `#000000`, ButtonText
`#000000`, ButtonFace `#ffffff`. These are theme defaults; on Windows use the live system
colours.
Status colours (`alias/lightColorPalette.js`; cranberry, green, orange ramps in
`global/colors.js`): danger fg `#b10e1c`, bg1 `#fdf3f4`, fill `#c50f1f`; success fg `#0e700e`,
bg1 `#f1faf1`, fill `#107c10`; warning fg `#bc4b09`, bg1 `#fff9f5`, fill `#f7630c`.
Windows guidance (L-col, paraphrase): darker surfaces are less important; use accent
sparingly; never rely on red versus green alone.

## 8. Focus

P1 (verified): inner stroke white and outer black in light, reversed in dark; HC outer is
Highlight. Stroke widths Thick 2 / Thicker 3. Our D11 two-ring layout (2 px outer + 1 px inner)
matches this inner/outer pair.
Exact WinUI ring width and offset: unverified (memory): 2 px dark outer, 1 px light inner,
hugging the control edge.

## 9. Control sizes

| Item | Value | Source | Flag |
|---|---|---|---|
| Button / text box min height | 32 | X1 `TextControlThemeMinHeight` 32, `ContentDialogButtonHeight` 32 | verified |
| Button padding | 8,4,8,5 (legacy); modern WinUI 11,5,11,6 | X1 `ButtonPadding` | legacy verified; modern unverified (memory) |
| ListViewItem min height | 40 | X1 `ListViewItemMinHeight` | verified |
| GridViewItem min size | 44 x 44 | X1 | verified |
| List / grid header item min height | 44 | X1 `ListViewHeaderItemMinHeight` | verified |
| MenuFlyout min height 32; item padding 11,9,11,10 (narrow 11,4,11,7); separator 1 px, padding 12,4 | | X1 | verified (legacy) |
| ComboBox item padding | 11,5,11,7 | X1 | verified (legacy) |
| ContentDialog | min 320 x 184, max height 756, padding 24,18,24,24, buttons 32 high and min 130 wide, title max 56 | X1 | verified (legacy) |
| Flyout padding / min width | 12,11,12,12 / 96 | X1 | verified |
| ToolTip padding | 8,5,8,7 | X1 | verified |
| NavigationView compact pane / top pane | 40 / 40 | X1 | verified |
| ScrollBar size (full) | 16 | X1 `ScrollBarSize` | verified; thin indicator width unverified (memory) |
| Slider track | 2 | X1 `SliderTrackThemeHeight` | verified |
| App bar compact / default min height | 40 / 56 | X1 `AppBarThemeCompactHeight`, `AppBarThemeMinHeight` | verified |
| Compact (small) button 24-28 | | none | unverified (memory) |
| Compact list item 32 | | none | unverified (memory) |
| Title bar height standard 32, tall 48 | | none | unverified (memory) |
| Checkbox / radio box 20 | | none | unverified (memory) |
| Touch target minimum | 44 x 44 (web / iOS), 48 (Android) | F2-lay | verified |
| System icon size | 16 epx base, glyph is a square em, monoline 1 epx | L-ico | verified |
| InfoBar custom icon | 20 px recommended | L-ib | verified |

## 10. Dialog button order and defaults (L-dlg) - verified (paraphrase)

- Always at least one safe, non-destructive button (Close / Cancel); it sits rightmost and
  answers Esc.
- Up to two "do it" buttons: Primary leftmost, Secondary in the middle. Three buttons sparingly.
- A default button, if any, gets the accent style and takes Enter, unless focus is on a control
  that uses Enter.
- Confirmation (OK / Cancel): affirmative left, cancel right.
- Button text names the specific response ("Delete", "Allow"), not generic yes / no.
- Do not use a dialog for errors tied to one field; show them inline. One dialog at a time.

## 11. Notifications

| Item | Value | Source | Flag |
|---|---|---|---|
| InfoBar severities | Informational, Success, Warning, Error; icon plus title and message text, close X (may be non-closable), optional action button | L-ib | verified |
| InfoBar scope | inline, app-wide status, pushes content, does not float, not for time-sensitive alerts | L-ib | verified |
| Toast (transient, floating) lifetime and position | bottom right, about 5 s | none | unverified (memory) |
