# Direction A: "Fluent 2 Mica"

Round 2, direction A from `../BRIEF.md` §4. Evrakçı drawn as if it shipped with Windows 11
next to File Explorer and new Outlook: the tabs sit in a Mica-toned title band, one quiet
icon-first command bar, and the work lies on a rounded layer one step lighter than the base. All
data is invented. Rendered at 1366×768, light and dark:

| | Light | Dark |
|---|---|---|
| Kontrol | `png/kontrol-light.png` | `png/kontrol-dark.png` |
| Değerler | `png/degerler-light.png` | `png/degerler-dark.png` |

Files: `tokens.css` (all values, contrast proof at the top), `shell.css` (window + shared
components), `kontrol.html`, `degerler.html`, `icons.js` (real Lucide 0.460.0 paths, ISC),
`_contrast.py` (D10 proof, writes the table into `tokens.css`), `_render.py` (PNG + clipping
check). Commands: `python3 _contrast.py --write` then `python3 _render.py --no-text150`.

## 1. Concept

**Calm comes from the platform's own restraint, and the brand lives in one place: the filed
documents.** Everything around the work is Windows 11 at its quietest: no resting menu row, no
labelled ribbon, no grey boxes on buttons, no status icons except the one count that must never be
silent. That quiet is what lets the Kontrol timeline stand out: white pages filed under manila
guide tabs drawn in the exact trapezoid shape of the logo's tabs, with one orange rider where a
human has to look. Someone who knows the logo recognises the screen; someone who knows Explorer
already knows how to use it.

What changed against round 1 (the owner's "old office program"):

| Round 1 | Direction A |
|---|---|
| 5 stacked bands, 152 px chrome (Kontrol 248 px) | 3 bands, **116 px** chrome; Kontrol with the overview **148 px** |
| Resting menu bar with underlined mnemonics | "≡" button in the title band; menu row appears on Alt, underlines only then |
| Text tab row + 3 px underline | Fluent TabView tabs in the title band, selected tab flows into the work layer |
| 10–12 labelled commands at body size | 2 labelled verbs per bar, the rest 36 px icon buttons with tooltips |
| 3 greys 2–4 % apart, no radius | base L\* 90.8 / layer 96.4 / card 100 (dark 9.9 / 15.2 / 19.3), 8 px rounded layer and cards |
| Every button outlined at 3:1 | filled primary, standard (fill + faint stroke), subtle (no stroke) |
| 96 × 136 thumbnails, 6 marker kinds per document | **148 × 209** pages, 2 marks at rest: guide tab (+ check when reviewed) and, only for kontrol, the rider |
| Property-grid inspector, stacked outlined buttons | Settings-style cards, label/value rows without hairlines, one filled primary |
| Keycaps on primaries, search and hint lines | Shortcuts as quiet text in menus, tooltips and one edit hint; no keycaps |

## 2. Tokens (summary; `tokens.css` is the source)

| Group | Light | Dark | Notes |
|---|---|---|---|
| `base` (L0, Mica fallback) | `#e1e6e3` | `#191c1a` | title band, status bar, gutters; real Mica via DWM where available |
| `layer` (L1) | `#f3f5f4` | `#232725` | rounded work layer, selected tab, command bar |
| `card` (L2) | `#ffffff` | `#2b302d` | inspector cards, table frame |
| `popover` | `#ffffff` | `#313633` | menus, hint, toast (+ the one shadow level) |
| `well` | `#e9edea` | `#1e2220` | recessed crop well, separator tile |
| `text` / `text-2` / `icon` | `#16201a` / `#4a5550` / `#36423c` | `#e9ede9` / `#aab4ae` / `#c2cbc5` | |
| `accent` (D1) | `#3f5a4c` | `#93c4a6` (+ dark ink `#0f1f16`) | primary fill, selected tab icon, selection ring, selector pill, slider |
| `manila` / `manila-edge` | `#e9d9a6` / `#8a7a45` | `#ddcb93` / `#b9a76f` | guide tabs and the document lip only |
| `rider` (D1) | `#e8731a` | `#e8731a` | kontrol only, always icon + "Kontrol" |
| `check-text` / `check-wash` | `#8a3d00` / `#fde6d1` | `#ffb57e` / `#4d311b` | Güven "Kontrol", uncertain characters |
| cut types | QR `#1f5fbf`, filtre `#6b3fa0`, elle `#37424a` | same (they sit on manila) | none within 30° of the rider hue |
| `paper` | `#ffffff` | `#e4e6e1` (dimmed) | scans stay light in dark mode |

- **Type (D4):** Inter; 13/18, 15/21, 20/28, 24/32 used; weights 400/500/600. OCR values use
  Inter's own `ss02` (I with serifs, l with tail) + `zero` (slashed 0) + `tnum`.
- **Spacing (D6):** 4, 8, 12, 16, 24, 32, 48. **Radii:** 2 paper, 4 controls, 8 layer/cards/popovers.
- **Sizes (D5 Normal):** controls 32, rows 40, icon buttons 36, title band 44, command bar 44,
  overview 32, status 28, inspector 312 (Kontrol) / 368 (Değerler).
- **Elevation:** strokes first; one float shadow (`0 8 24 / 7 %` + `0 2 6 / 6 %` light, alpha < 0.08);
  paper has its own two-step shadow; dark adds a 1 px top-edge highlight instead of glow.
- **Motion (D7):** menus 180 ms enter curve, toast 240 ms; nothing on repeated actions; `prefers-reduced-motion` removes both.
- **Contrast (D10):** 65 pairs per theme in `tokens.css`, **0 failing**. Highlights: body text
  ≥ 13.6:1 light / ≥ 8.4:1 dark on every surface; secondary ≥ 6.0:1 light / ≥ 4.98:1 dark (lowest:
  dark selected row); primary label 7.56:1 (dark 8.70:1);
  inputs, ticks, focus, rider edge, cut pictograms ≥ 3:1. Button *borders* are no longer held to
  3:1 (labels identify them, WCAG 1.4.11; brief C6); input bottom edges still are.

## 3. How each skill changed a concrete decision

| Skill | What it changed here |
|---|---|
| `frontend-design` | "Spend boldness in one place": the bold thing is the guide tab, redrawn as the logo's trapezoid tab; everything else stays platform-quiet. Removed middle-dot meta strings ("Belge 15, 1 sayfa", "Ekspertiz Raporu, sayfa 72–73"), no eyebrow caps, no "→". Rejected cream + serif and the dark/acid-green defaults by name. |
| `anti-slop` | Deleted the fake "stamp" circles on thumbnails after the first render (they read as spinners); no gradients, no glass (no backdrop blur anywhere); search field keeps its one functional icon, other fields none; percentages in Güven are plain text, not pills. Table frame and row hairlines kept (deleting structure is a fail). |
| `typography` | Weights capped at 400/500/600 (measured: a stray 700 from `<b>` shapes was removed). Four sizes per screen: 13 / 15 / 20 / 24. Headings tight (24/32 with −0.01em), body 15/21. Pane titles demoted to 15 semibold; one 24 px element per screen (Kontrol "Belge 16", Değerler the suggested value). D4's 15/21 kept over the skill's 16/1.55 (owner decision). |
| `colour-palette` | 60-30-10 from the screenshot: base + layer ≈ 60 %, cards/paper ≈ 30 %, green + manila + orange < 10 %. Table is an L2 card with a 1 px border and hairline rows. Shadow alpha held below 0.08 in light; dark uses a top-edge highlight. Dark accent raised to `#93c4a6` with dark ink instead of reusing the light hex. |
| `spacing` | Tight inside groups (4–8), wide between groups (12–28): page gap 12 vs document gap 28 makes documents read as stacks without drawing boxes; card padding 16; command-bar separators 8 px each side. All gaps on the 4/8 grid; the only optical value is the 7.6 px inner trapezoid inset (1 px stroke on an 8 px slant). |
| `surfaces` | Cell correction is an inline edit in the same box (input inset 4 px inside the 40 px cell, zero layout shift) with Enter/Esc; no dialog. Delete stays undoable instead of confirmed (owner decision, research 04 r11): this overrides the skill's "always confirm destructive" rule, noted as a conflict. |
| `icon-buttons` | Command bars collapsed to square 36 px icon buttons; every one has an accessible name that includes the shortcut ("Önceki belgeyle birleştir (M)"), shown as a tooltip in Qt. Labels kept only for the primary verbs (Kes, Sonraki kontrol, Değerleri oku) and the destructive menu item. 36 px instead of the skill's 44 (desktop pointer; Fluent 32–40; D5). |
| `page-patterns` | Both screens named before markup: **Split Pane** (work area + inspector of the selection). That drove one inspector per tab and no dashboard tiles in either. |
| `empty-states` | Not shown in these two states (the brief asked for the main states). Rule carried into the system: empty states keep the pane skeleton (table frame, timeline lip), one sentence, one verb-first primary; the drop target appears only during drag (gate 8). |
| `design-system` | Three-tier tokens (primitive hex → semantic role → component use), every hex in `tokens.css` only (grep shows none in the pages), contrast proof regenerated from the file, new tokens added when a need appeared (`hover-pop`, `on-manila-ok`, `paper-box`, `paper-mark`, `cut-filter-text`) instead of hard-coding. |
| `ui-compare` | UXKIN does not connect here; compared with published conventions (table below). It moved the menu into an Alt-reveal + "≡", put tabs in the title band, made selection a ring + check badge (Photos/Explorer gallery) and the context-menu shortcuts plain right-aligned text. |

`ui-compare` (no real journeys opened; platform conventions as known):

| Point | Explorer 11 | New Outlook | Photos / Lightroom | Round 1 | Direction A |
|---|---|---|---|---|---|
| Menus at rest | none | none | none / menu bar (mac) | text menu row | none; "≡" + Alt reveal |
| Tabs | in title bar | rail | none | separate row | in title band |
| Command labels | 2–3 | ≈ 5 | 0 | 10 | 2 |
| Selection | fill + check | fill + bar | ring + check | ring + fill | ring + check |
| Status bar | 24–28 px text | none | thin | 32 px with icons | 28 px, one icon per count |

## 4. Gates from BRIEF §5 (measured with Playwright on the pages)

| Gate | Result |
|---|---|
| 1 chrome ≤ 120 (Kontrol ≤ 150) | 44 + 44 + 28 = **116**; Kontrol + overview 32 = **148** |
| 2 no resting menu row / underlines | met; Alt reveals the row (not drawn in these states) |
| 3 ≤ 3 labels per bar, icon buttons 28–36 | Kontrol 2, Değerler 2; 36 px |
| 4 surface levels ΔL ≥ 5 / ≥ 4 | light base→layer 5.6, layer→card 3.6, base→card 9.2; dark 5.3 / 4.1 / 9.4 L\*. Rounded layer: yes. No full-width hairline inside the layer except table rows. |
| 5 one title-size element | Kontrol "Belge 16"; Değerler the suggested value |
| 6 one orange mark per kontrol item | timeline: rider only; table: the Güven cell is the item mark, the character tint lives inside the value (required by the task) |
| 7 ≥ 60 % page pixels, thumbs ≥ 132 | thumbs **148 × 209**; page pixels **53 %** of the timeline with the inspector open (round 1 ≈ 20 %). Miss: 60 % is reached one zoom step up (164 px) or with the inspector hidden (F9). |
| 8 no dashed boxes at rest | met (the filter lip is a dashed *line*, the cut-type encoding) |
| 9 keeps | keyboard model, vocabulary, status = icon + word + colour, cut encoding, contrast proof all carried over. 150 % text renders were not produced in this round (two states asked). |

Clipping check (`_render.py`): 0 warnings in both pages. Font sizes outside the scale appear
only inside the scan crop (14 / 17 px), which stands for image pixels, not UI text.

## 5. Deviations from `decisions.md` (owner approval needed)

1. **GOAL 3.1 "a menu bar": no resting menu row.** All six menus remain, reached by Alt + D/E/G/T/A/Y
   (the row appears on Alt, underlines only then, `SH_UnderlineShortcut`), by the "≡" button in the
   title band, and by Ctrl+K. Reason: the permanent mnemonic row is the strongest "old Win32" signal (brief C2).
2. **D2 "1 px hairlines" reinterpreted.** Separation is by tonal layers + 1 px strokes on layers and
   cards; hairlines remain only between table rows and menu groups. Reason: brief C5/C8.
3. **D6 radii: 8 px also on the work layer and cards** (D6 lists 8 only for dialogs, menus, popovers).
   Windows 11 Explorer/Settings and Outlook round content layers; 4 px cards read as Office 2010.
   Guide tabs use 3 px top corners inside the trapezoid (paper scale).
4. **D10 test scope: button borders exempt.** Buttons identified by their label no longer need a 3:1
   border; inputs keep a 3:1 bottom edge (Fluent TextBox). Brief C6.
5. **D5 icon buttons 36 px** in a 44 px command bar (D5 lists control heights, not icon buttons).
6. **Status bar zoom shows "%" but no label text**; the slider's tooltip names what it zooms
   ("Küçük resim boyutu" / "Kaynak kesiti yakınlığı").
7. **Search shows "Ara  Ctrl+K"** (command palette) instead of a labelled menu; it opens the palette.
8. **Command-bar labels at 15 px** (body), not 13–14 as the brief suggested: D4 keeps 15 for
   readability and only two labels remain, so they no longer compete with content.

## 6. How each element is built in Qt (QSS + QPalette + QPainter, no blur)

| Element | Qt |
|---|---|
| Title band + tabs | Frameless `QMainWindow`, custom title widget handling `WM_NCHITTEST` (caption drag, snap layouts on the maximise button), or keep the native frame and set `DWMWA_CAPTION_COLOR` to `base`. Tabs: `QTabBar` in the title widget; QSS `QTabBar::tab:selected { background: layer; border: 1px solid stroke; border-bottom: none; border-top-left-radius: 8px; border-top-right-radius: 8px; }`; the two 8 px reverse "feet" are painted in `paintEvent` with a `QPainterPath` arc. Mica: `DwmSetWindowAttribute(DWMWA_SYSTEMBACKDROP_TYPE=38, 2)` on Windows 11 22621+, solid `base` otherwise, never behind pages or tables. |
| Menus on Alt | `QMenuBar` hidden; event filter on `Key_Alt` release shows it; `QStyle.SH_UnderlineShortcut` 0 until Alt; "≡" `QToolButton` with `InstantPopup` holding the six `QMenu`s. Ctrl+K palette unchanged. |
| Work layer | `QFrame#layer { background: layer; border: 1px solid stroke; border-radius: 8px; }` with 8 px margins in the central layout. |
| Command bar | `QToolBar` of `QToolButton` (`ToolButtonIconOnly`, `autoRaise`) 36 × 36, `border-radius: 4px`, `:hover { background: hover }`; labelled ones `ToolButtonTextBesideIcon`. Icons: Lucide SVG via `QSvgRenderer` recoloured to `icon`, stroke 1.6 at 20 px / 1.75 at 16 px (set the attribute before rendering). Tooltips from the action registry: "Birleştir" + muted shortcut. |
| Overview | One custom `QWidget`: 96 rounded rects (`drawRoundedRect` r 2) in `track` / `accent` / `rider` + 1 px `rider-edge`, viewport as a 2 px `text` rounded rect; drag moves the viewport. |
| Timeline | `QListView` in IconMode with a `QStyledItemDelegate` (no widget per page, smooth at 1,000 pages). Pages: cached thumbnail pixmap, 1 px edge + two-step shadow from a cached 9-patch, radius 2. Guide tab: one `QPainterPath` (trapezoid, 8 px slants), fill `manila`, stroke `manila-edge`, pictogram + number; lip = 6 px rect with a 2 px solid / 1 px dashed (`Qt.DashLine`) / 2 px dotted (`Qt.DotLine`) top pen. Rider: rounded rect `rider` + 1 px `rider-edge`, icon + "Kontrol". Selection: 2 px `accent` ring 3 px outside the sheet + 22 px check badge. Focus: D11 ring painted by the delegate at 7–9 px. Document gap 28 vs page gap 12 via the delegate's `sizeHint` / custom layout. |
| Inspector cards | `QScrollArea` of `QFrame.card` (`card` fill, 1 px `stroke`, radius 8) with `QFormLayout`; label column 13 px `text-2`; no `QFrame::HLine`. Action rows are flat `QPushButton`s with a right-aligned value + chevron. Primary `QPushButton#primary { background: accent; color: text-on-accent; border-radius: 4px; min-height: 40px; }`. |
| Context menu | `QMenu` with QSS: `background: popover; border: 1px solid stroke; border-radius: 8px; padding: 4px; ::item { height: 34px; border-radius: 4px; } ::item:selected { background: hover-pop; }`; rounded corners need `FramelessWindowHint` + `WA_TranslucentBackground` and the cached shadow; shortcuts right-aligned by Qt (`QKeySequence.NativeText`). |
| Değerler table | `QTableView` in a card frame; `QHeaderView` 36 px, 13 px semibold `text-2`; rows 40; grid off, delegate draws the `stroke-soft` row line; selected row = `selected` fill + 3 px `accent` bar at the left. Values: `QFont.setFeature("ss02"/"zero"/"tnum")` (Qt 6.7+); uncertain characters painted by the delegate with `QTextLayout` format ranges (wash + 2 px underline). Güven: icon + word + % in a delegate. |
| Inline edit | `QStyledItemDelegate.createEditor` → `QLineEdit` given the cell rect inset by 4 px (no layout shift), QSS `border-bottom: 2px solid accent`, D11 ring from the focus proxy style. Key hint = custom tooltip widget on edit start. |
| View selector | Three checkable `QToolButton`s in a `QButtonGroup`; the 3 × 16 px pill painted in `paintEvent` (Fluent SelectorBar). |
| Crop | `QGraphicsView` of the page image in a `well` frame; field box and uncertain-character boxes as `QGraphicsRectItem`s in `paper-box` / `paper-mark`; Ctrl+wheel zoom, slider in the status bar. |
| Toast | Frameless child widget, `popover` + 1 px stroke + cached shadow, bottom-right 12 px; "Geri al" is a flat `QPushButton` in `text-accent`; `QPropertyAnimation` on opacity/pos 240 ms, skipped under reduced motion. |
| Status bar | `QStatusBar` 28 px on `base`, 13 px `text-2`, numbers semibold `text`; one icon per count; `QSlider` styled (groove 4 px `track`, sub-page `accent`, 16 px handle). |

## 7. Open points for the owner

- Approve deviations 1–8 above, especially 1 (no resting menu row) and 3 (8 px layers/cards).
- Gate 7 is at 53 % with the inspector open; accept, or default thumbnails one step larger (164 px) and wrap documents across rows.
- Dark mode dims scans to `#e4e6e1`; a "dim page previews" toggle in Ayarlar could make it optional.
