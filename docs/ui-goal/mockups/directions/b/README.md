# Direction B: "Sessiz masa" (Quiet workspace)

Round-2 mockups for Evrakçı, direction B of `../BRIEF.md` §4. The screens are 1366×768, in light
and dark. All data is invented. `docs/ui-goal/decisions.md` still wins wherever this file
disagrees with it, and every deviation below needs the owner's OK.

| Screen | Light | Dark |
|---|---|---|
| Kontrol: overview of the whole job, document folders with a guide tab for each cut type, 3 selected pages, focus ring, open context menu, inspector, zoom | `png/kontrol-light.png` | `png/kontrol-dark.png` |
| Değerler: dual pane (values table + linked page crop), Emin / Orta / Kontrol / Okunamadı, tinted uncertain characters, one cell being edited, tooltip, toast with "Geri al" | `png/degerler-light.png` | `png/degerler-dark.png` |

## 1. Concept

**One desk, one sheet of paper.** The window has only two surfaces. The **desk** (`--base`) holds
the title row and a slim sidebar. The **sheet** (`--panel`) is one rounded panel inset 8 px from the
window edges, and the work happens on it. No other band, strip or hairline crosses the screen.
Space does the grouping: 8 px inside a group, 20–32 px between groups. The calm comes from what
is left out (Linear, Things 3), not from grey.

- **Navigation is a sidebar, not a tab strip.** The job sits at the top like a project in Linear.
  Below it are the six stations, each with a live count (Kontrol ⚠ 7, Değerler ⚠ 14). Değerler
  opens its three review views (Kontrol gerekenler / İncelenmemiş / Tümü) as sub-rows, the way
  Linear and Things nest views. At the bottom are "İncelendi 58 / 96 belge" with a 4 px progress
  line, plus Ayarlar, Yardım and "Kenar çubuğunu daralt" (Ctrl+B, collapses to a 52 px rail).
- **The title row is a command row.** It holds the "≡" app menu (all six menus, each with its
  Alt access key), the app mark, a centred **command field** ("Komut, belge veya sayfa ara · Ctrl+K",
  the new Outlook / Teams / VS Code pattern that makes the palette discoverable), the save state
  and the caption buttons. There is no resting menu row and no status band.
- **Each screen has one title (24 px)** and a few icon tools. Only the verb you press most has a
  label ("Sonraki kontrol"). Selection commands appear in a **floating contextual bar** at the
  bottom of the canvas (the Photos / Figma / Linear pattern) and nowhere else on screen. They are
  also in the context menu, the "⋯" menu, the "≡" menu and Ctrl+K, so the bar is never the only
  way to reach them.
- **The one memorable element is the filing cabinet.** Each document is a folder: a manila guide
  tab stands on a 2 px manila rule that spans the document's pages. The tab sits at the **left**
  for a QR separator, in the **centre** for a filter cut and at the **right** for a manual cut. The
  rule is **solid / dashed / dotted** to match, and the tab holds the cut pictogram and the number
  (+ ✓ once reviewed). The orange rider ("⚠ Kontrol") is clipped onto the same rule at the
  document's right end. That gives at most two marks per document at rest, and no other colour on
  the canvas.
- **Content is the hero.** Pages are 144 × 204 px white sheets (radius 2, 1 px edge, a 1 px soft
  shadow). In dark mode they stay near white (`#ecedea`) so scans read true, as in Lightroom's
  darkroom. The Değerler crop is the biggest object in its pane (312 × 220 px), and the value being
  checked is set at 20 px.

## 2. Tokens (`tokens.css`)

| Group | Light | Dark | Notes |
|---|---|---|---|
| Desk `--base` | `#e9ecea` | `#161917` | title row + sidebar |
| Sheet `--panel` | `#fbfbfa` | `#212422` | ΔL\* ≈ 6 (light) / ≈ 5.5 (dark): passes gate 4 |
| `--well` / `--hover` / `--selected` / `--popover` | `#f0f2f0` / `#eceeec` / `#dfe8e2` / `#fff` | `#2a2e2b` / `#2a2e2b` / `#2b3b32` / `#2c302d` | quiet fills; popover = the only shadowed layer |
| Ink `--text` / `--text-2` | `#16201a` / `#4a5650` | `#e6ebe8` / `#a9b3ad` | ≥ 13:1 / ≥ 5.5:1 on every surface |
| `--edge` (inputs, hollow marks) | `#77837d` | `#7f8a84` | ≥ 3.3:1; only where an edge identifies a control |
| `--stroke` / `--stroke-panel` / `--stroke-pop` | decorative hairlines | | exempt from 3:1 (they separate, they don't identify) |
| Accent | `#3f5a4c` (white text 7.56:1) | `#8dbd9f` (ink `#0d1a12`) | primary, selected station pill, selection ring, focus-adjacent, progress |
| Manila / rider / kontrol text | `#e9d9a6` · `#e8731a` · `#8a3d00` | `#d9c68e` · `#e8731a` · `#ffb27a` | D1 unchanged |
| Cut types | QR `#1f5fbf` · filtre `#7a3d9e` · elle `#46525c` | `#8fb7ff` · `#d2a6ee` · `#b7c2cb` | ≥ 108° of hue from the rider |
| Type | 24/32 page (×1 per screen) · 20/28 working value · 15/21 body, labels 500, pane titles 600 · 13/18 secondary | | Inter; weights 400/500/600; `tnum` everywhere; `zero cv08 ss02` on read values so I/1, O/0, B/8 differ |
| Space | 4 8 12 16 24 32 48 | | one 20 px row gap (8 + 12) in the timeline, marked |
| Radii | 2 sheet · 4 control · 8 panel, popover, menu, tray, segmented track | | 5 px inner segment = 8 − 3 inset (concentric, marked) |
| Shadow | `--shadow-pop` α .07/.06 (light) | α .36/.28 + 1 px top sheen (dark) | popovers, floating bar, toast only |
| Chrome | title 40 · sidebar 232 · panel header 56 · rows 40 · controls 32 · icon buttons 32 | | D5 Normal |
| Motion | 80/120/180/240 ms, standard/enter/exit | | D7 unchanged; 0 under reduced motion |

**Contrast proof.** The comment table at the top of `tokens.css` is generated by `_contrast.py`
(copied from `../../_contrast.py`, with the pairs adapted to these tokens). It checks 48 pairs per
theme, plus the hue distance from the rider. Result: **0 failures, light and dark**. Body text is
≥ 13:1 everywhere, secondary text ≥ 5.49:1, and edges/icons/focus ≥ 3.31:1. Run
`python3 _contrast.py --write` after any colour change.

## 3. How each skill changed a concrete decision

| Skill | What it changed here |
|---|---|
| `frontend-design:frontend-design` | **Spend boldness in one place**: the manila folder (tab + rule + rider) is the only expressive element; everything else is neutral. It removed the round-1 "A · B · C" meta strings (subtitles are sentences: "96 belge, 640 sayfa", "Belge 16, sayfa 72"), the eyebrow labels over sections, and the keycaps on buttons. Also its "tinted near-black" warning: dark base is a green-tinted `#161917`, not #111. |
| `vectorlab-ux-skills:anti-slop` | No glass or blur: the floating bar and the menus are opaque popover fills with a 1 px border. No pills on static metadata: counts in the sidebar are plain text. The only icon inside an input is the search magnifier. The slop pass deleted decoration but kept structure: the table keeps its header rule and row hairlines. |
| `vectorlab-ux-skills:typography` | Three weights only (400/500/600, no 700: DESIGN.md's 700 is retired). Hierarchy by size: one 24 px title, the working value at 20 px, everything else 15/13. The −1.2 % tracking is only on the 24 px title. Conflict: the skill wants 16 px body with 1.5 line height; **D4 (15/21) wins**. |
| `vectorlab-ux-skills:colour-palette` | **60-30-10 estimated from the PNGs**: about 60 % sheet, 30 % desk and structure, accent + manila + orange under 8 %. Elevation is "1 px border first, shadow second": the panel has only a border, and only popovers get the shadow (α < .08 in light). In dark, a 1 px top sheen (`inset 0 1px 0 rgba(255,255,255,.05)`) replaces glow. The table is an L1 surface (it sits on the raised panel with hairlines). |
| `vectorlab-ux-skills:spacing` | 8-pt majors (40/56/32 chrome, 24 panel padding, 32 between documents, 24 between inspector groups) and 4-pt micro gaps (4 between icon and text in chips, 2 between nav rows). Group gaps (24–32) are larger than item gaps (8): the round-1 "no gap larger than 24" problem is gone. Optical offsets are marked in the CSS. |
| `vectorlab-ux-skills:surfaces` | The Sicil no edit is **in place with zero layout shift**: the input fills the same 40 px cell, inset 4 px, with no Save/Cancel row. Selection actions are a non-modal floating bar, not a dialog. Conflict: the skill wants a confirm dialog for destructive actions; **research 04 r11 and the owner's answer win**: "3 sayfayı sil" names the count and is undone with Ctrl+Z. |
| `vectorlab-ux-skills:icon-buttons` | Header and floating-bar commands are square 32 × 32 icon buttons. Each has an `aria-label` and a real tooltip that names the shortcut (shown: "Önceki kontrol  Shift+N"). The primary and the destructive "Sil" keep their labels, as the skill asks. Conflict: the skill wants 44 px hit targets (touch); desktop **D5 32 px** wins. |
| `vectorlab-ux-skills:page-patterns` | Named before building: **Kontrol = Split Pane** (timeline + document inspector), **Değerler = Split Pane** (table + linked crop). The sidebar is chrome, not a page. The three Değerler filters are *view modes of one page*, so they became sidebar sub-rows, not separate screens, and the template switch is the title itself ("Ekspertiz Raporu ▾"). |
| `vectorlab-ux-skills:empty-states` | Not rendered in this round (two main states only). The rule set for the build: an empty Kontrol keeps the overview track and the canvas frame, with one sentence and one primary ("Belge yok: önce Yükle'de bir iş açın", **İş aç**). A filtered-empty Değerler view gets a "Süzgeci temizle" action as well as its primary. |
| `design:design-system` | Every value is a role token (no hex in `shell.css` or the pages except the logo's own colours in `chrome.js` and the always-light scan crop in dark mode in `degerler.html`). Each component has its states in `shell.css`: button (subtle / secondary / primary / danger, hover, focus), field (rest, focus = 2 px accent bottom), segmented, menu item (hover, danger), nav row (current, sub-current), rider, status. The token table above is the documentation. |
| `ui-design-review:ui-compare` | UXKIN does not connect here, so this compares against published conventions and the named apps as I know them. **Linear** (inset panel, sidebar counts, contextual bottom bar, Ctrl+K), **new Outlook / Teams** (command field in the title row), **Photos / Lightroom** (selection = accent ring + check badge, thumbnail slider top-right, near-white scans in dark), **Windows 11 Settings** (3 × 16 px accent pill on the current nav row). What most do, and Evrakçı now does too: no resting menu bar, no status band, one labelled verb. Where Evrakçı deliberately differs: the counts and the "İncelendi" progress stay visible at all times (never silent), and the orange rider is a word, not just a dot. |

## 4. Deviations from decisions.md / GOAL.md (each needs the owner's OK)

| # | Decision | What B does | Why |
|---|---|---|---|
| B1 | **D2** "a command bar per tab" | No command-bar band. Each screen's header holds ≤ 6 icon tools + 1 labelled verb, and selection commands float in a contextual bar. | Round-1 cause C4: a row of 12 labelled commands *is* a ribbon. Every command stays in the "≡" menus, the context menu, "⋯" and Ctrl+K (research 05: hidden-only commands hurt older users, so nothing is *only* in the bar). |
| B2 | **GOAL 3.1** "a menu bar (Dosya … Yardım)" | The six menus live behind the "≡" button in the title row. Alt shows them (Alt+D/E/G/T/A/Y opens each), and underlines appear only after Alt. | Cause C2: a resting mnemonic row is the strongest "old Win32" signal. All access keys and shortcuts are unchanged. |
| B3 | **GOAL 3.1 / D2** tabs ("Window tabs") | The six stations are a left **sidebar** (Ctrl+1…6 unchanged, Ctrl+B collapses it to a rail). | Direction B by definition. It leaves room for live counts and the Değerler sub-views, and makes the job a visible "project". |
| B4 | **GOAL 3.1** "status-bar zoom slider with %" and the status bar | No status bar. Kontrol shows the thumbnail-size slider + "%100" at the right of the overview legend. "Sayfa 74 / 640" sits at its left, and the kontrol / İncelendi counts are in the legend and the sidebar. | Cause C15: the status bar repeated facts already on screen. The never-silent counts are still always visible. |
| B5 | **D6** radii "8 for dialogs, menus, popovers" | 8 px also on the content panel, the selection tray and the segmented track. The inner segment is 5 px (8 − 3 inset, concentric). | A rounded inset layer is the main modern cue (Linear, Explorer, Outlook). It is still the same three radii plus one marked optical value. |
| B6 | **D6** spacing set | One 20 px gap (8 + 12) between the two timeline rows. | It lets two rows of 144 px pages fit at 1366×768 without the floating bar covering page numbers. |
| B7 | **D10 application** (round-1 practice) | Buttons that carry a label have no 3:1 border. Secondary buttons have a faint frame + a 3:1 bottom edge. Inputs keep the 3:1 bottom edge and a 2 px accent bottom edge on focus. | BRIEF C6 and §3: WCAG 1.4.11 does not need a boundary on a button its text identifies. Focus, inputs, selection and state marks all stay ≥ 3:1. |
| B8 | **Round-2 gate 7** (≥ 60 % page pixels) | **57 %** at default zoom (10 pages × 144 × 204 in an 844 × 610 canvas); it rises when the sidebar is collapsed (Ctrl+B) because more pages fit per row. Thumbnails are 144 px wide, above the 132 px floor. | The inspector and the sidebar share 1366 px. A larger default would push the second row under the floating bar. The slider goes up from there. |
| B9 | Round-1 Değerler "Sayfalar" column | Dropped from the table. The page range is in the inspector ("Belge 16, sayfa 72") and the row's tooltip. | Gives Firma 200 px without sideways scrolling at 100 % text. |
| B10 | Round-1 review circle on every row | No per-row İncelendi glyph. The view itself (İncelenmemiş) says it, the Kontrol tab shows ✓ inside the guide tab, and the inspector says "Durum: İncelenmedi". | BRIEF C10: 11 dotted circles per screen were clutter. |

Not changed: D1, D3, D4, D5 (32 / 40 Normal), D7, D8, D9, D10 thresholds, D11, all vocabulary, and
the full keyboard map (N / Shift+N, U, Enter = Belgeyi onayla, Space, Esc, Ctrl+G, F2, F6, Ctrl+Z).

## 5. Round-2 gates (BRIEF §5), measured

| Gate | Result |
|---|---|
| 1 Horizontal chrome | Değerler 40 + 56 = **96 px**. Kontrol 40 + 56 + 52 (overview) = **148 px** (≤ 150). |
| 2 No resting menu row | Yes. The menus are behind "≡", opened with Alt+letter. |
| 3 ≤ 3 labels, icon buttons 28–36 with tooltips | Kontrol header 1 label, floating bar 1 ("Sil"), Değerler header 1. All icon buttons are 32 px. |
| 4 Distinct surfaces | Desk/sheet ΔL\* ≈ 6 / 5.5. One rounded layer. The only full-width rules inside it are the table header and rows. |
| 5 One page-title size | One 24 px title per screen. Pane titles are 15/600. |
| 6 One orange mark per item, no keycaps | One rider per document on the canvas, one in the inspector, one bar in the overview. Shortcuts appear as muted text and tooltips only. |
| 7 Page pixels | 57 % (see B8). Thumbnails 144 px. |
| 8 No dashed boxes at rest | None. Dashed / dotted lines appear only as the cut-type rule (meaningful). |
| 9 Keeps | All §3 keeps intact. `_contrast.py` 0 failures. `_render.py` reports 0 clipping warnings. |

## 6. How each element is built in Qt

| Element | Qt build |
|---|---|
| Two surfaces | `QPalette.Window` = `--base`. The panel is a `QFrame#panel { background: panel; border: 1px solid stroke-panel; border-radius: 8px; }` placed with `setContentsMargins(0, 0, 8, 8)` in the central layout. In dark, the 1 px top sheen is one `drawLine` in the frame's `paintEvent`. |
| Title row | Frameless `QMainWindow` with a custom 40 px title widget: `WM_NCHITTEST` returns `HTCAPTION` on empty areas and `HTMAXBUTTON` on the maximise button, which keeps snap layouts. Alternatively keep the native frame and set `DWMWA_CAPTION_COLOR` to `--base`. |
| "≡" app menu | `QToolButton` (`InstantPopup`) holding the six `QMenu`s. A `QMenuBar` stays in the widget tree but hidden, so the Alt access keys keep working. An event filter on `Key_Alt` shows it (or `popup()`s the menu for Alt+letter). `SH_UnderlineShortcut` = 0 in the `QProxyStyle` until Alt is pressed. |
| Command field | A `QPushButton` styled as a field that opens the existing Ctrl+K palette; the "Ctrl+K" text is `QKeySequence.toString(NativeText)`. |
| Sidebar | `QListView` + delegate. Current row = `panel` fill + 1 px `stroke-panel` + a 3 × 16 accent pill (`drawRoundedRect`, r 1.5). Counts right-aligned, kontrol counts with the Lucide triangle in `--check-text`. Sub-rows = a second indentation level (a `QTreeView` without branch decorations). It collapses to a 52 px rail with a `QPropertyAnimation` on `maximumWidth` (180 ms, standard; 0 under reduced motion). |
| Panel header | An `QHBoxLayout`: `QLabel` (24/32, 600), `QToolButton`s with `autoRaise`, QSS `border: none; border-radius: 4px;` and hover = `--hover`. "Sonraki kontrol" is a `QPushButton#secondary` with per-side borders (`border-bottom-color: edge`). |
| Overview | One custom `QWidget`: `paintEvent` draws 96 rounded rects (width ∝ page count; 14 px accent = İncelendi, 6 px edge grey = İncelenmedi, 14 px rider + 6 px triangle = Kontrol) and the viewport rectangle (2 px `--text`, r 4). Clicking or dragging scrolls the timeline. The legend and the zoom are normal widgets in the row above it. |
| Timeline | A `QListView` (IconMode) + `QStyledItemDelegate`, with **no widget per page** (1,000 pages stay smooth). The delegate paints the per-document tab row: the rule with `Qt.SolidLine` / `DashLine` / `DotLine`, the guide-tab path (r 4 top corners), the rider, the page pixmap from a cache, the 1 px shadow (cached 9-patch), the selection tray (r 8, `--selected`), the 2 px accent ring, the 22 px check badge, and the D11 focus ring (2 px outer + 1 px inner, 4 px outside the sheet). |
| Floating selection bar | A child `QFrame#popover` of the canvas viewport. It is shown when the selection is non-empty, centred on `resizeEvent`, with an opacity animation (120 ms enter / 80 ms exit). Its shadow is the cached 9-patch, not `QGraphicsDropShadowEffect` on scrolling content (research 06 r10). |
| Context menu | A standard `QMenu` with QSS `border-radius: 8px; padding: 4px;`, items 32 px, shortcuts drawn by Qt, right-aligned in `--text-2`. The header line is a disabled `QWidgetAction`. `popup()` flips upward on its own when there is no room below. |
| Inspector | A `QScrollArea` with a `QVBoxLayout`. The "why" card is a `QFrame` (`--well`, r 8) with the rider (custom-painted chip) and a word-wrapped `QLabel`. Properties are a `QFormLayout` with no lines. The footer is pinned: the primary `QPushButton` (40 px), a hint `QLabel` and two flat `QPushButton`s. |
| Değerler table | `QTableView` + model. `horizontalHeader` QSS has a 1 px bottom `stroke-panel`, and rows have a 1 px `stroke`. A delegate paints the current row (`--selected` + 3 × 20 accent pill), tints uncertain characters (`QTextLayout` format ranges: `check-wash` background + 2 px `rider-edge` underline), and draws the status icon + word. The editor is a `QLineEdit` given the same rect inset 4 px (no row resize), with QSS `border-bottom: 2px solid accent`. |
| Crop | A `QGraphicsView` on the page pixmap, zoomed to the value's box. The box ring (2 px accent) and the per-character outlines are drawn in `drawForeground`. The ± buttons float in a popover frame. |
| Tooltip / toast | `QToolTip` styled with QSS (popover fill, 1 px border, r 8). The shortcut is appended as rich text in `--text-2`. The toast is a reusable `QFrame#popover` anchored bottom-right of the table region, with "Geri al" calling the undo stack. |

## 7. Files

| File | What it is |
|---|---|
| `tokens.css` | All tokens, light + dark, with the generated contrast proof |
| `shell.css` | Window, sidebar, panel, buttons, fields, segmented control, status words, rider, popovers |
| `chrome.js` | Fills the identical title row + sidebar on both pages |
| `icons.js` | Inline Lucide sprite (lucide-static 0.460.0, ISC), generated by `_icons.py` |
| `kontrol.html`, `degerler.html` | The two screens |
| `_contrast.py`, `_render.py`, `_icons.py` | Contrast proof, Playwright renderer + clipping check, icon sprite builder |
| `png/` | `kontrol-{light,dark}.png`, `degerler-{light,dark}.png` |

Re-render: `python3 _render.py kontrol.html degerler.html` (add `--text150` for the 150 % pass).
Rebuild the icons:
`npm pack lucide-static@0.460.0` into `/tmp/lucide-b`, then `python3 -I _icons.py /tmp/lucide-b/package/icons`.

## 8. Iteration log (self-review against anti-slop and ui-review)

1. **First render.** One CSS class was shared by two elements (`.check` named both the selection
   badge and the kontrol counts), which put stray circles in the sidebar. The inspector button pair
   overflowed the panel by 48 px. The context menu hid the Belge 16 rider (the one orange mark).
   The floating bar covered the zoom control.
2. **Second render.** Moved the kontrol document to the first row so the menu opens downward and
   leaves the rider, the tab and all three selected pages visible. The Değerler filter row became
   sidebar sub-views, which cut chrome from 140 to 96 px. Two outlined buttons in the header read
   as a toolbar, so "Değerleri oku" became an icon. Dates lost the disambiguation glyph set (only
   read codes need it). The crop grew to be the hero of its pane. The "Kontrol gerekenler" sub-row
   wrapped, so the sidebar went from 216 to 232 px.
3. **Third render.** Thumbnails went from 136 to 144 px (closer to gate 7), the position and zoom
   moved into the overview legend, and the tab row got 16 px of air under the overview. The dark
   accent was calmed from `#93c4a6` to `#8dbd9f`. Menu separators were invisible in dark, which
   added `--stroke-pop`. The menu was nudged off the focused page so the whole focus ring shows.
