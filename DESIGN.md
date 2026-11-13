---
name: Evrakçı
description: Local scan-and-split desktop tool in Windows 11 / Fluent 2 "Mica" dress; the brand lives in the filed documents (manila guide tabs, one orange rider for kontrol).
source: docs/ui-goal/mockups/final-a/ (direction A as approved; tokens.css is the token source)
colors:  # light theme; dark and high contrast are in src/evrakci/ui/tokens/tokens.json
  base: "#e1e6e3"
  layer: "#f3f5f4"
  card: "#ffffff"
  popover: "#ffffff"
  well: "#e9edea"
  hover: "#e7ebe8"
  hover-pop: "#eaeeeb"
  pressed: "#dce2de"
  selected: "#dde9e2"
  track: "#d3dad6"
  stroke: "#d8dedb"
  stroke-soft: "#e6eae7"
  text: "#16201a"
  text-2: "#4a5550"
  icon: "#36423c"
  edge: "#7a8680"
  accent: "#3f5a4c"
  accent-hover: "#34493e"
  text-on-accent: "#ffffff"
  text-accent: "#3f5a4c"
  manila: "#e9d9a6"
  manila-edge: "#8a7a45"
  manila-ink: "#2b2410"
  rider: "#e8731a"
  rider-edge: "#9c4a0b"
  rider-ink: "#241000"
  check-text: "#8a3d00"
  check-wash: "#fde6d1"
  ok: "#1d6a3a"
  danger: "#b3123a"
  danger-wash: "#fbe4e8"
  cut-qr: "#1f5fbf"
  cut-filter: "#6b3fa0"
  cut-manual: "#37424a"
  paper: "#ffffff"
  focus-outer: "#16201a"
  focus-inner: "#ffffff"
typography:
  family: "Inter (bundled, OFL), then Segoe UI Variable, Segoe UI"
  caption: "13px / 18px"
  body: "15px / 21px"
  section: "17px / 24px"
  panel: "20px / 28px"
  page: "24px / 32px, -0.01em"
  weights: [400, 500, 600]
  value-features: "tnum ss02 zero"
  number-features: "tnum"
rounded:
  paper: "2px"
  control: "4px"
  layer: "8px"  # work layer, cards, menus, popovers, toasts
spacing: [4, 8, 12, 16, 24, 32, 48]
sizes:  # D5 Normal; Sıkı / Geniş in tokens.json
  control: "32px"
  row: "40px"
  icon-button: "36px"
  title-band: "44px"
  command-bar: "44px"
  overview: "32px"
  status-bar: "28px"
  inspector: "312px"
  thumbnail: "148 x 209px"
motion:
  durations: [80, 120, 180, 240]
  standard: "cubic-bezier(.2, 0, 0, 1)"
  enter: "cubic-bezier(0, 0, 0, 1)"
  exit: "cubic-bezier(.3, 0, 1, 1)"
---

# Design System: Evrakçı

## Overview

**Direction A, "Fluent 2 Mica" (approved by the owner, 2026-11-12).** Evrakçı is drawn as if it
shipped with Windows 11 next to File Explorer and the new Outlook: the six tabs sit in a
Mica-toned title band, each tab has one quiet icon-first command bar, and the work lies on a
rounded layer one step lighter than the base. The inspector is a stack of Settings-style cards.
Calm comes from the platform's own restraint; the brand lives in one place: the filed
documents. White pages stand under manila guide tabs drawn in the trapezoid of the logo's tabs,
with one orange rider where a human has to look.

**Source of truth.** The approved renders and code in `docs/ui-goal/mockups/final-a/`
(`png/*-light.png`, `*-dark.png`; the default Kontrol and Değerler renders are direction A
pixel for pixel). The Qt window must look like them. Changes to A are proposed in
`docs/ui-goal/mockups/final-a/PROPOSALS.md` and applied only after the owner says yes.

**Key characteristics**
- Three tonal levels and paper: base (L0, title band, status bar, gutters), layer (L1, the
  rounded work layer and the selected tab), card (L2, inspector cards, table frame), popover.
- One accent: cabinet green for the primary button, the selected tab icon, selection, the
  slider and the selector pill. Orange means kontrol and nothing else (D1).
- No resting menu row: the six menus open from the "≡" button, Alt + access key (the menu row and
  underlines appear while Alt is held) and Ctrl+K.
- Two labelled commands per command bar at most; everything else is a 36 px icon button with a
  tooltip that names the action and its key.
- Status is always icon + word + colour (Emin / Orta / Kontrol / Okunamadı; İncelendi /
  İncelenmedi).

## Token pipeline

```
docs/ui-goal/mockups/final-a/tokens.css      (the approved spec; the only hand-edited values)
        │  python3 tools/build_tokens.py      (--check in CI; a test rebuilds it in memory)
        ▼
src/evrakci/ui/tokens/tokens.json            DTCG ($value / $type); hc values alias the
        │                                     Windows system colours ({color.system.sys-*})
        ▼
src/evrakci/ui/tokens/generated.py           plain dicts for the frozen app; the ONLY module
        │                                     with hex literals (besides logo_data.py)
        ▼
src/evrakci/ui/theme.py   ThemeManager       colours, sizes, fonts, QPalette, stylesheet
src/evrakci/ui/tokens/qss.py                 the stylesheet template ({{role}} placeholders)
src/evrakci/ui/style.py   EvrakciStyle       Fusion + D11 focus ring, title tabs, metrics
```

Rules: no hex colour in any other module of `src/evrakci/ui` (a test scans for them; the four
Kartotek screens rebuilt in Phase 3 hold a few that may only go down). New colours are added
to the spec's `tokens.css` first, with a contrast row, never to code.

## Colors

Three themes (D9): **light** (default), **dark**, **high contrast**. "System" (the default
setting) follows the OS: high contrast when Windows reports it (`SPI_GETHIGHCONTRAST`, else
Qt's contrast hint), otherwise the OS colour scheme, and it changes live.

| Role | Light | Dark | Use |
|---|---|---|---|
| base | `#e1e6e3` | `#191c1a` | L0: title band, status bar, gutters (Mica fallback) |
| layer | `#f3f5f4` | `#232725` | L1: the rounded work layer, the selected tab, command bar |
| card | `#ffffff` | `#2b302d` | L2: inspector cards, table frame, buttons, inputs |
| popover | `#ffffff` | `#313633` | menus, tooltips, toasts |
| well | `#e9edea` | `#1e2220` | recessed crop well inside a card |
| hover / hover-pop / pressed | `#e7ebe8` / `#eaeeeb` / `#dce2de` | `#333835` / `#3e4440` / `#3a403c` | subtle hover, menu hover, pressed |
| selected | `#dde9e2` | `#2f4337` | selected row / list item (+ 3 px accent bar) |
| track | `#d3dad6` | `#3b423e` | overview track, slider groove, progress |
| stroke / stroke-soft | `#d8dedb` / `#e6eae7` | `#383e3a` / `#343a36` | 1 px edge of layer and cards / row and menu dividers |
| text / text-2 / icon | `#16201a` / `#4a5550` / `#36423c` | `#e9ede9` / `#aab4ae` / `#c2cbc5` | body, secondary, icons |
| edge | `#7a8680` | `#8c9892` | 3:1 input bottom edge, checkbox and radio edge |
| accent / accent-hover | `#3f5a4c` / `#34493e` | `#93c4a6` / `#a7d1b6` | D1 cabinet green |
| text-on-accent / text-accent | `#ffffff` / `#3f5a4c` | `#0f1f16` / `#a3d0b4` | label on the primary / green text and links |
| manila / manila-edge / manila-ink | `#e9d9a6` / `#8a7a45` / `#2b2410` | `#ddcb93` / `#b9a76f` / `#2b2410` | guide tabs and the document lip only |
| rider / rider-edge / rider-ink | `#e8731a` / `#9c4a0b` / `#241000` | `#e8731a` / `#f5a061` / `#241000` | kontrol only, always icon + "Kontrol" |
| check-text / check-wash | `#8a3d00` / `#fde6d1` | `#ffb57e` / `#4d311b` | Güven "Kontrol", uncertain characters |
| ok / danger / danger-wash | `#1d6a3a` / `#b3123a` / `#fbe4e8` | `#82d3a0` / `#ff92a6` / `#4a2229` | Emin, errors |
| cut-qr / cut-filter / cut-manual | `#1f5fbf` / `#6b3fa0` / `#37424a` | same (they sit on manila) | cut pictograms; none within 30° of the rider hue |
| paper (+ paper-ink, -line, -head, -box, -mark) | `#ffffff` | `#e4e6e1` (dimmed) | scans stay light in dark mode |
| focus-outer / focus-inner | `#16201a` / `#ffffff` | `#ffffff` / `#16201a` | D11 ring |

**High contrast** maps every role to a Windows system colour (defaults: High Contrast Black;
on Windows the live `GetSysColor` values are used): Window for surfaces, WindowText for text,
strokes and every status (Kontrol is told apart by its triangle, the word and the outlined
rider), Highlight + HighlightText for selection, the primary and focus, Hotlight for links,
GrayText for disabled only. Paper stays as scanned. Hover becomes a Highlight edge and a
selected row a Highlight fill.

**Contrast (D10)** is unit-tested per theme for 65 token pairs (`tests/ui/test_tokens.py`,
ported from the spec's `_contrast.py`): body and table text ≥ 7:1, secondary ≥ 4.5:1, input
edges, icons, ticks and focus ≥ 3:1. Button borders are exempt (their label identifies them);
input bottom edges are not.

**Derived roles** (computed, not stored): `text-disabled`, `icon-disabled`, `accent-disabled`,
`on-accent-disabled` = A's 45 % opacity over the layer (GrayText in high contrast).

### Named rules (kept from the Kartotek system)
- **The Rider Means Kontrol Rule.** Signal orange appears only on things that need a human
  check, always with the warn pictogram and the word "Kontrol". Never a brand accent, hover,
  emphasis or generic warning.
- **The One Job Per Warm Rule.** Manila marks where a document is filed; orange marks what needs
  checking. They never swap roles and nothing else on the screen is warm.
- **The Position Before Colour Rule.** A cut type is identifiable in greyscale: tab position and
  pictogram (plus the dashed lip for filter) carry it; the cut colour only confirms.
- **The Variable Names Itself Rule.** A template variable colour never appears without the
  variable's name beside it.

## Typography

Inter (SIL OFL 1.1, bundled; D3) with Segoe UI Variable and Segoe UI as fallbacks, via
`fonts.font_stack()`. Weights 400 / 500 / 600 only.

| Role | Size / line | Weight | Use |
|---|---|---|---|
| caption | 13 / 18 | 400, 600 for labels | the floor: status bar, table header, group labels, job name, tooltips |
| body | 15 / 21 | 400; 500 for commands and tabs; 600 for the selected tab and primary | everything else |
| section | 17 / 24 | 600 | section headings |
| panel | 20 / 28 | 600 | empty-state titles, panel headings |
| page | 24 / 32, −0.01em | 600 | one per screen ("Belge 16", the suggested value) |

OCR values use Inter's `ss02` (I with serifs, l with tail) + `zero` + `tnum`
(`ThemeManager.font("value")`); counts and numbers use `tnum` (`font("num")`).
**Text size** 100 / 115 / 130 / 150 % scales every type step; at 130 % and 150 % the chrome also
moves one density up (D5). Sizes round to whole pixels (150 %: 20 / 23 / 26 / 30 / 36).

## Layout

The canvas is a 1366×768 window; three bands, 116 px of chrome (Kontrol 148 with the overview):

1. **Title band** (44, base): logo 20 px · six tabs with Lucide icons · (space) · job name +
   "Kaydedildi 14:32" + chevron (the job switch) · "Ara  Ctrl+K" search (148 wide, opens the
   palette) · "≡" button · caption buttons. The selected tab is a filled layer tab with 8 px top
   corners, a 1 px stroke and two 8 px reverse "feet" that flow into the work layer.
2. **Work layer** (layer, 8 px margins, 1 px stroke, radius 8) holding the **command bar** (44)
   and the tab's content: Split Pane, the work area plus an inspector (312 Kontrol / 368
   Değerler) of Settings-style cards.
3. **Status bar** (28, base): counts in caption type, numbers semibold, one icon per count, the
   zoom slider with "%" at the right.

Spacing: 4, 8, 12, 16, 24, 32, 48. Tight inside a group (4–8), wide between groups (12–28).
Each screen's default state fits 1366×768 without scrolling the window; at 150 % panes scroll
in their own area (thin scrollbar) above pinned actions.

**Density (D5):** Sıkı / Normal / Geniş = controls 28 / 32 / 40, rows 32 / 40 / 48. Normal is A;
Geniş is A's 150 % chrome (icon buttons 44, bands 52, status 36, inspector 400, icons 20 / 24);
Sıkı is not drawn in A and changes only controls, rows, icon buttons (32) and the command bar
(40).

**Title band at 150 % (provisional, owner decision pending, PROPOSALS item 3):** unselected tabs
show only their icon (name in the tooltip); the band is 52 high, tabs 44, search 196.
`theme.title_band_rule()` is the one place to switch it.

## Elevation and shape

Strokes first; one float shadow (`0 8 24 / 7 %` + `0 2 6 / 6 %` light) for menus, the palette and
toasts, painted (QSS has no shadows); paper has its own two-step shadow; dark adds a 1 px
top-edge highlight instead of glow; high contrast has no shadows. Radii: 2 paper, 4 controls,
8 work layer, cards, menus, popovers (A's deviation 3); the rider keeps A's 3.

## Components and their Qt names

The stylesheet (`tokens/qss.py`) styles every standard widget and these component classes.
One-off chrome uses the objectName; repeated pieces use the dynamic property `kind`; buttons
use `variant` and `size`.

| Component | Qt | Look |
|---|---|---|
| Title band | `QWidget#titleBand` | base, 44 high |
| Title tabs | standalone `QTabBar#titleTabs` (not inside a QTabWidget), icons with a Normal (text-2) and Selected (accent) mode | painted by EvrakciStyle: A's tab, feet, 500 / 600 labels |
| Job switch | `QWidget#jobSwitch` with `QLabel#jobName` + a label for the save state | caption, name 600, hover fill |
| Search | `QPushButton#searchBox` | layer fill, stroke, "Ara" + "Ctrl+K" in text-2 |
| ≡ button | `QToolButton#menuButton` | 32 px icon button |
| Caption buttons | `QToolButton[kind="caption-button"]` | 46 × 32 |
| Work layer | `QFrame#layer` | layer, stroke, radius 8 |
| Command bar | `QToolBar#commandBar` (or a QWidget) | 36 px icon buttons; labelled ones `kind="command"`; separators 1 × 20 stroke |
| Icon button | `QToolButton[kind="icon"]` (`size="sm"` = 32) | transparent, hover fill, radius 4 |
| Buttons | `QPushButton`; `variant="primary"` (also the old `primary=true`), `"subtle"`, `"link"`; `size="lg"` (40) | standard = card + stroke; primary = accent + text-on-accent, 600 |
| Inputs | `QLineEdit`, spin boxes, `QComboBox`, text edits | card, stroke, 3:1 `edge` bottom; focus = 2 px accent bottom + the D11 ring |
| Checkbox / radio | standard | 20 px, `edge`, accent when on |
| Tables and lists | standard item views in a `QFrame[kind="table-card"]` | rows 40, header 36 caption 600 text-2, `stroke-soft` row lines, selected fill (the 3 px accent bar is the delegate's) |
| Cards | `QFrame[kind="card"]` | card, stroke, radius 8; `QLabel[kind="group-label"]` above |
| Inspector rows | `QLabel[kind="inspector-key"]` / `"inspector-value"`, `QPushButton[kind="inspector-row"]` | label column caption text-2; flat action rows |
| Status bar | `QStatusBar#statusBar`, numbers `QLabel[kind="count"]` | base, caption text-2 |
| Rider | `QLabel[kind="rider"]` (icon + word in a custom widget) | rider fill, rider-edge, 22 high, radius 3 |
| Status words | `QLabel[state="kontrol" / "ok" / "orta" / "bad"]` | check-text 600 / ok / text-2 / danger 600 |
| Badge | `QLabel[kind="badge"]` | accent, 20 high |
| Menus | `QMenu` (made frameless + translucent by the style for the 8 px corners) | popover, stroke, padding 4, items 34 high, radius 4, hover-pop |
| Tooltips | `QToolTip` | popover, stroke, radius 4, caption |
| Toast / InfoBar | `QFrame[kind="toast"]`, `QFrame[kind="infobar"][severity=…]` | popover + stroke, radius 8 (+ painted shadow) |
| Scrollbars | standard | 9 px, 3 px text-2 thumb, wider on hover, no track |
| Slider / progress | standard | 4 px track, accent fill, 16 px handle with accent dot / 4 px bar |
| Splitter | standard | invisible 4 px gutter, stroke on hover |

**Focus (D11):** a 2 px outer (`focus-outer`) + 1 px inner (`focus-inner`) ring, 1 px outside the
control, following its radius (`focusRadius` property overrides). `EvrakciStyle` draws it with
an overlay on whichever widget gets keyboard focus (Tab, Shift+Tab, shortcuts, focus moved by
code), so widgets Fusion never frames get it too; item views draw it on the current item. A
mouse click on a field shows only the accent bottom edge (Fluent). Never hidden otherwise.

**Access keys:** `SH_UnderlineShortcut` is off; underlines appear while Alt is held.

**Motion (D7):** 80 / 120 / 180 / 240 ms with the standard, enter and exit curves (`motion.py`);
menus 180 ms enter, toasts 240 ms; nothing on repeated actions. Reduced motion (setting or OS)
sets every duration and Qt's widget animations to 0.

## Signatures (painted)

- **Guide tab:** one `QPainterPath` in the logo's trapezoid (8 px slants, 3 px top corners),
  manila fill, manila-edge stroke, cut pictogram + number; the document lip is a 6 px manila
  strip with a solid (QR) / dashed (filter) / dotted (manual) top line.
- **Rider:** rounded rect (radius 3) in rider + 1 px rider-edge, warn icon + "Kontrol" in
  rider-ink 13/600. In high contrast: Window with a 2 px WindowText edge.
- **Selection:** a 2 px accent ring 3 px outside the sheet + a 22 px check badge.

## Palette history

| Kartotek name (2026-11) | Was | Now (A role) |
|---|---|---|
| shell, shell-2, shell-3 | `#3f5a4c`, `#344b3f`, `#5a7566` | accent, accent-hover, accent-hover |
| on-shell, on-shell-2 | `#ffffff`, `#cddbd2` | text-on-accent |
| ground, card, paper | `#e6ebe7`, `#fbfaf6`, `#ffffff` | base, layer, card |
| ink, ink-2 | `#1d2a23`, `#4f5d55` | text, text-2 |
| rule, rule-strong, control-edge | `#c9d1cb`, `#74817a`, `#7f8c84` | stroke, edge, edge |
| manila, manila-edge, manila-ink | `#e9d9a6`, `#b9a66a`, `#2b2410` | manila, manila-edge (`#8a7a45` for 3:1), manila-ink |
| index-red | `#c8372d` | retired (A has no index rule; maps to stroke) |
| rider, rider-edge, rider-ink | `#e8731a`, `#9c4a0b`, `#2a1400` | unchanged (ink `#241000`) |
| check-ink, check-wash, row-cur | `#8a3d00`, `#fde7d3`, `#f3efe0` | check-text, check-wash, selected |
| qr, filter, manual | `#1f5fbf`, `#b45200`, `#b42318` | cut-qr, cut-filter (violet, away from orange), cut-manual (slate) |
| v1–v4 (template variables) | teal, violet, rust, plum | cut-qr, cut-filter, on-manila-ok, cut-manual (paper-safe, no orange) |
| key-cap, key-edge, disabled-ink, hover | | hover, stroke, text-2, hover (keycaps are retired in A) |

The old names still resolve through `theme.TOKENS` / `theme.LEGACY` (and the old selectors in
the stylesheet's legacy block) until the Phase 3 screens stop using them.

## Do's and Don'ts

- **Do** take every colour and size from the tokens (`theme.manager()`); a new screen adds
  layout only.
- **Do** keep A's chrome exactly: logo, tabs with icons, job switch, search, ≡, caption buttons,
  command bar, inspector cards, spacing and labels. Propose changes in PROPOSALS.md.
- **Do** show kontrol with the orange rider, the warn pictogram and the word, and nothing else in
  orange; pair every status colour with an icon and a word.
- **Do** keep figures tabular; OCR values use the value font.
- **Don't** use a resting menu row, keycaps on buttons, gradients, glass or glow.
- **Don't** set text below 13 px or use weights above 600.
- **Don't** call `setStyleSheet` per widget in hot paths; set `kind` / `variant` properties.
