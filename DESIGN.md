---
name: Evrakçı
description: Local scan-and-split desktop tool; the job kept like an office card-index cabinet, with manila guide tabs and orange signal riders.
colors:
  shell: "#3f5a4c"
  shell-2: "#344b3f"
  shell-3: "#5a7566"
  on-shell: "#ffffff"
  on-shell-2: "#cddbd2"
  ground: "#e6ebe7"
  card: "#fbfaf6"
  paper: "#ffffff"
  ink: "#1d2a23"
  ink-2: "#4f5d55"
  rule: "#c9d1cb"
  rule-strong: "#74817a"
  control-edge: "#7f8c84"
  manila: "#e9d9a6"
  manila-edge: "#b9a66a"
  manila-ink: "#2b2410"
  index-red: "#c8372d"
  rider: "#e8731a"
  rider-edge: "#9c4a0b"
  rider-ink: "#2a1400"
  check-ink: "#8a3d00"
  check-wash: "#fde7d3"
  row-cur: "#f3efe0"
  qr: "#1f5fbf"
  filter: "#b45200"
  manual: "#b42318"
  ok: "#1e6b3a"
  focus: "#1d2a23"
  v1: "#0f7b78"
  v2: "#6b3fb3"
  v3: "#9a4a12"
  v4: "#a3245f"
typography:
  page-title:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.4
    fontFeature: "tnum"
  panel-title:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 700
    lineHeight: 1.4
    fontFeature: "tnum"
  section-title:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 700
    lineHeight: 1.4
    fontFeature: "tnum"
  body:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: "tnum"
  control:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.4
    fontFeature: "tnum"
  secondary:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.4
    fontFeature: "tnum"
  label:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 700
    lineHeight: 1.4
    fontFeature: "tnum"
  mono-value:
    fontFamily: "ui-monospace, Consolas, monospace"
    fontSize: "15px"
    fontWeight: 700
    lineHeight: 1
rounded:
  sheet: "2px"
  tag: "3px"
  field: "4px"
  control: "5px"
  nav-tab: "6px"
  guide-tab: "7px"
spacing:
  xs: "4px"
  sm: "6px"
  md: "8px"
  lg: "12px"
  xl: "16px"
  gutter: "20px"
  wide: "24px"
components:
  header:
    backgroundColor: "{colors.shell}"
    textColor: "{colors.on-shell}"
    typography: "{typography.body}"
    height: "40px"
    padding: "0 20px"
  nav-tab:
    backgroundColor: "{colors.shell}"
    textColor: "{colors.on-shell-2}"
    typography: "{typography.control}"
    rounded: "{rounded.nav-tab}"
    padding: "8px 16px 9px"
  nav-tab-active:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
  toolbar:
    backgroundColor: "{colors.card}"
    height: "52px"
    padding: "0 16px"
  button:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    height: "34px"
    padding: "0 9px"
  button-primary:
    backgroundColor: "{colors.shell}"
    textColor: "{colors.on-shell}"
    typography: "{typography.control}"
    rounded: "{rounded.control}"
    height: "34px"
    padding: "0 9px"
  button-disabled:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink-2}"
  button-icon:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    size: "34px"
  key-hint:
    textColor: "{colors.ink-2}"
    typography: "{typography.label}"
    rounded: "{rounded.field}"
    padding: "3px 5px"
  key-hint-on-primary:
    backgroundColor: "{colors.shell-3}"
    textColor: "{colors.on-shell}"
  input:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.field}"
    height: "34px"
    padding: "0 8px"
  checkbox-on:
    backgroundColor: "{colors.shell}"
    textColor: "{colors.on-shell}"
    rounded: "{rounded.tag}"
    size: "18px"
  guide-tab:
    backgroundColor: "{colors.manila}"
    textColor: "{colors.manila-ink}"
    typography: "{typography.control}"
    rounded: "{rounded.guide-tab}"
    height: "42px"
    padding: "4px 10px 0"
  rider:
    backgroundColor: "{colors.rider}"
    textColor: "{colors.rider-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.tag}"
    height: "21px"
    padding: "0 7px 0 5px"
  misread-value:
    backgroundColor: "{colors.check-wash}"
    typography: "{typography.mono-value}"
    rounded: "{rounded.tag}"
    padding: "2px 5px"
  table-header:
    textColor: "{colors.ink-2}"
    typography: "{typography.label}"
    padding: "0 10px 6px"
  table-row:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    height: "36px"
    padding: "0 10px"
  table-row-current:
    backgroundColor: "{colors.row-cur}"
  side-panel:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink}"
    padding: "16px 20px"
  progress-bar:
    backgroundColor: "{colors.paper}"
    rounded: "{rounded.tag}"
    height: "14px"
  status-bar:
    backgroundColor: "{colors.shell}"
    textColor: "{colors.on-shell}"
    typography: "{typography.secondary}"
    height: "30px"
    padding: "0 20px"
---

# Design System: Evrakçı

## Overview

**Creative North Star: "The Kartotek"**

Evrakçı looks like the card-index cabinet every chamber office already owns. A deep cabinet-green shell (header, window tabs, status bar) holds pale index cards; each document start is a manila guide tab standing above its pages; anything that needs a human check carries a bright orange signal rider clipped to its tab; and a thin red index rule runs under each heading, exactly like a printed index card. The metaphor is borrowed for palette, type, density and these four signatures only. Every control stays a standard Windows widget, because the product ships as a PySide6/Qt window.

The screen is dense but calm: 1366×768 is the design canvas, body text is 15px, nothing is smaller than 13px, and a working screen shows the timeline, a value table and a detail panel at once without scrolling. Groups are separated by thin rules on a single card surface, not by stacked boxes, so long sessions read as one sheet of paper rather than a dashboard. Meaning never rides on colour alone: every state has an icon and a word, and every cut type has a position and a pictogram before it has a colour.

The source of truth is the shipped mockup set in `docs/superpowers/mockups/kartotek/` (`kartotek.css` holds the shared tokens; six screens: yukle, kontrol, sablonlar, degerler, disa-aktar, rehber). It replaces the earlier metro-line ("Hat Haritası") world in full; nothing from that world carries over except the cut-type and variable hues, which were kept on purpose.

**Key Characteristics:**
- Cabinet-green chrome around pale card surfaces; one flat, quiet working sheet.
- Manila guide tabs mark where a document starts; orange riders mark "kontrol" and nothing else.
- Thin red index rule under headings; thin grey rules between groups; no nested boxes.
- One readable sans (Atkinson Hyperlegible Next) with tabular figures everywhere; mono only for misread values and file names.
- Keyboard first: key hints sit inside the buttons they trigger; tab shortcuts live in tooltips and the status bar.
- Every colour and size is a role-named token so the Qt build maps them to a palette and stylesheet, and later themes swap values, not roles.

## Colors

Muted cabinet greens and paper neutrals carry the whole screen; manila and signal orange are the only warm surfaces, and each has exactly one job.

### Primary
- **Cabinet Green** (shell): the header bar, window tab strip, status bar, the primary button, a checked checkbox, progress-bar fill, and the selected-page frame and number plate. It is chrome and commitment, never decoration.
- **Cabinet Green Dark** (shell-2): the hairline between the header and the tab strip.
- **Cabinet Green Light** (shell-3): key-hint plates inside the primary button, and the primary button when disabled.
- **On Shell** (on-shell) and **On Shell Muted** (on-shell-2): primary and secondary text on the shell (inactive tab labels, job line, "Kaydedildi" time, status-bar key names).

### Secondary
- **Manila** (manila), **Manila Edge** (manila-edge), **Manila Ink** (manila-ink): guide tabs above each document's pages, the page-edge strip under them, the active entry in the Rehber table of contents, the "İpucu" tip tab, and text selection. Manila means "this is where something is filed".

### Tertiary
- **Signal Orange** (rider) with **Rider Edge** (rider-edge) and **Rider Ink** (rider-ink): the signal rider, the timeline flags, and the square warning chip in the detail panel. Every use carries the warn pictogram and the word "Kontrol".
- **Check Ink** (check-ink) and **Check Wash** (check-wash): text and wash for things that need a check: the notice heading, "Kontrol" status text, counts of pending checks, the flagged table cell and the misread value chip.

### Functional
- **Index Red** (index-red): the 1px index rule under headings (screen headings, panel meta lines, section headings). Also the chapter number in Rehber headings at 24px bold.
- **Cut types** — **QR Blue** (qr), **Filter Amber** (filter), **Manual Red** (manual): the cut marker, its pictogram, and the pictogram on the guide tab. QR blue doubles as the "information" icon colour in Rehber and Dışa Aktar.
- **Done Green** (ok): "Tamam" status text and icon.
- **Variables** — **Teal** (v1), **Violet** (v2), **Rust** (v3), **Plum** (v4): template variable boxes, their name labels, and the swatch beside each variable name. Each box always prints its name; colour only helps tell neighbours apart.

### Neutral
- **Ground** (ground): window background and the reading column in Rehber.
- **Card** (card): toolbars, side panels and left columns; the "index card" surface.
- **Paper** (paper): buttons, inputs, table body and page sheets.
- **Ink** (ink) and **Ink Muted** (ink-2): primary and secondary text; ink-2 also draws table-header text and the rule under table headers.
- **Rule** (rule): every divider between groups, rows and panels. **Rule Strong** (rule-strong): input borders, progress-bar frames, dashed group rows, drop-zone outline. **Control Edge** (control-edge): button borders.
- **Current Row** (row-cur): the current table row, list item, or job.
- **Focus** (focus): keyboard focus rings; deliberately the same value as ink so focus reads as a firm pencil line, not a colour.

### Named Rules
**The Rider Means Kontrol Rule.** Signal orange (rider) appears only on things that need a human check, always with the warn pictogram and the word "Kontrol" (or "N kontrol"). It is never a brand accent, a hover colour, or a generic warning.

**The One Job Per Warm Rule.** Manila marks where a document or section is filed; orange marks what needs checking. They never swap roles and nothing else on the screen is warm.

**The Variable Names Itself Rule.** A variable colour never appears without the variable's name beside it.

**The Red Under Headings Rule.** Index red draws only the 1px rule under a heading (screen heading, panel meta line, section heading) and a Rehber chapter number. Rows, panels and groups take the grey rule; red never fills, outlines or flags anything.

## Typography

**Body Font:** Atkinson Hyperlegible Next (with Segoe UI, then system-ui)
**Mono Font:** ui-monospace, Consolas (misread values and file names only)

**Character:** one highly legible humanist sans for everything, chosen for staff with weaker eyesight on older monitors; hierarchy comes from size and weight, never from a second display face.

**Licence flag:** Atkinson Hyperlegible Next is licensed under the SIL OFL 1.1, which is **not** on the owner's licence list (MIT, BSD, Apache, MPL, HPND, LGPL). Bundling it needs the owner's explicit approval. Until approved, the Qt build uses Segoe UI (present on every Windows PC); the scale, weights and tabular figures below hold for both.

### Hierarchy
- **Page title** (700, 24px, 1.4): the screen heading on the index rule ("Belge 40 — Belge 43", Rehber chapter titles).
- **Panel title** (700, 20px): the heading of the right-hand detail panel.
- **Section title** (700, 17px): section headings with an index rule (left-column heads, "Değişkenler"), the app name in the header, and big summary figures.
- **Body** (400, 15px, 1.4): all running text, table cells, field values. Rehber prose reads at 16px/1.55 with a 660px measure.
- **Control** (600, 15px): button labels, window tabs, guide-tab first line, emphasised values.
- **Secondary** (400, 14px): meta lines, hints, status bar, state text (600).
- **Label** (700, 13px): table headers, riders, timeline flag numbers, variable labels; key hints use 600 at 13px. 13px is the floor.
- **Mono value** (700, 15px, mono): a misread OCR value such as `48Z13`, and output file names in Dışa Aktar (14px there).

### Named Rules
**The Tabular Figures Rule.** Figures are tabular everywhere (`font-variant-numeric: tabular-nums` on the body); page numbers, counts and ranges must line up in columns and never jitter while a count runs.

**The Mono Means Literal Rule.** Monospace marks text the machine read or will write verbatim (misread values, file names, literal separators in name patterns). It is never used for decoration or headings.

**The 13px Floor Rule.** No text below 13px; body text never below 15px.

## Layout

The canvas is a 1366×768 window with fixed chrome: header (40px), window tab strip (40px), status bar (30px, pinned to the bottom). Working screens use a toolbar band (52px, card) under the tabs, then columns: an optional left column on card (280–420px), a flexible centre on ground, and a right detail panel on card (300–380px) set off by a 1px rule on its left edge. In Qt these are a QSplitter with fixed initial sizes.

Spacing is a small step scale: 4, 6, 8, 12, 16, 20, 24px. Chrome and panels pad 16–20px horizontally; the centre column pads 22–24px; inside a group, items gap 6–10px. Table rows are 36px (40px in Değerler); controls are 34px tall; toolbar buttons gap 6px with a 1px × 28px separator between groups.

**The Rules Not Boxes Rule.** Groups are separated by 1px rules (rule) on one surface. A panel never contains a bordered box; a list item never sits in its own card. The only bordered rectangles are controls, page sheets, and the drop zone.

**The No Scroll Rule.** Each screen's default state fits 1366×768 without scrolling the window; long data scrolls inside its own table or list.

## Elevation & Depth

The system is flat. Depth comes from tone (shell → card → paper) and from rules, not from shadows. The few shadows that exist imitate paper thickness:

### Shadow Vocabulary
- **Sheet** (`box-shadow: 0 1px 2px rgba(29,42,35,.12)`; 0 1px 3px at .18 for the larger canvas page and Rehber thumbnail): page sheets, the scan crop in Değerler.
- **Rider thickness** (`box-shadow: inset 0 -3px 0 rgba(0,0,0,.14)`): the lower lip of a signal rider, so it reads as a clipped plastic tab.
- **Key cap** (2px bottom border on the key hint): a key-cap lip, not a shadow.
- **Toggle pressed** (`box-shadow: inset 0 1px 2px rgba(29,42,35,.18)`): a toggled tool button (snap, grid).

**The Paper Only Rule.** Only paper objects (page sheets, riders, key caps) have depth. Panels, toolbars and dialogs-as-panels are flat.

## Shapes

Small, stationery-scale corners: sheets 2px, riders/tags/checkboxes 3px, inputs and key hints 4px, buttons 5px, window tabs 6px (top only), guide tabs 7px (top only). Guide tabs and window tabs are open at the bottom: they sit on the surface below them, like a card divider standing in a drawer. Dashed outlines mean "provisional or derived": a filter cut, a filter-made guide tab, an empty page, a variable box being drawn, a fallback (variant) box, the drop zone.

## Components

### Buttons
Plain, firm, labelled. One custom widget carries them all.
- **Shape:** 5px corners, 34px tall (38–40px for a full-width panel action), 9px side padding, 600 weight, 18px stroke icon before the label.
- **Default:** paper fill, control-edge border, ink text.
- **Primary:** cabinet-green fill and border, white text. One per area (the action the screen is waiting for).
- **Icon-only:** 34×34 square; the name lives in the tooltip and the key hint.
- **Focus:** 3px focus outline with 2px offset.
- **Disabled:** card fill, rule border, muted text; primary disabled uses shell-3 with white text.
- **Toggle (on):** row-cur fill, ink-2 border, inset pressed shade.
- **Key hint:** a key-cap plate at the right end of the label (13px/600, 4px corners, 2px bottom lip; shell-3 plate on primary). In Qt every button with a key hint is one custom-painted `KeyHintButton` (a `QPushButton` subclass) that paints icon, label and key cap; not a nested widget.

### Window tabs
- Cabinet-green strip; inactive labels on-shell-2 at 600; the active tab is a card-coloured folder tab (6px top corners) joining the toolbar below.
- Shortcuts (Ctrl+1…5, F1 for Rehber) live in each tab's tooltip and in the status bar's key list, not on the tab face.

### Inputs / Fields
- **Style:** paper fill, 1px rule-strong border, 4px corners, 34px tall, 8px padding. Number fields are centred bold (36×30px inline, 56×34px standalone). Search fields carry a leading 18px search icon.
- **Selects:** same box with a chevron icon at the right.
- **Checkbox:** 18px, 3px corners, 1.5px rule-strong border; checked is shell fill with a white check.
- **Progress:** 12–14px bar, rule-strong frame, 3px corners, shell fill; count and remaining time sit in text beside it.

### Tables / Lists
- No vertical lines. Header in label type (13px/700, ink-2) over a 1px ink-2 rule; rows 36px over 1px rule; first column flush left.
- **Current row:** row-cur fill. **Focused cell or list item:** inset 2px focus frame.
- **Flagged cell:** check-wash fill with check-ink bold text and the warn icon.
- **Sort:** sorted header turns ink with a small chevron.
- **State text:** icon + word, 14px/600: Tamam (ok), Kontrol (check-ink), Okunmadı (ink-2).

### Headings with the index rule
- Screen headings sit on a 1px index-red rule with an ink-2 subtitle on the same line and optional navigation at the right. Panel headings put the rule under their meta line; section headings (17px) take the same rule.

### Side panel (detail)
- Card surface, 16px 20px padding, rule on its left edge. A panel title, a meta line on the index rule, then sections separated by rules: notices, key–value lists (ink-2 terms, 600 values), and a stack of full-width actions with key hints at the right.

### Guide tab (signature)
- A manila tab (7px top corners, manila-edge border, open bottom) stands above the first page of each document, with a 6px manila page-edge strip running under the whole document. First line: cut pictogram in its cut colour + "Belge N · name" (700); second line 13px detail.
- Cut type is shown by **tab position first** (QR left, filter centred, manual right), **pictogram second** (QR, funnel, scissors), colour third; a filter tab and edge are dashed in filter amber.

**The Position Before Colour Rule.** A cut type must be identifiable in greyscale: tab position and pictogram (plus dashed line for filter) carry it; the cut colour only confirms.
- Between documents a cut marker repeats it: a 24px badge with the pictogram (round for QR and filter, square for manual) over a vertical line (solid for QR and manual, dashed for filter).

### Signal rider (signature)
- Orange rider tab (21px, 3px corners, rider-edge border, inner lower lip) clipped to the top-left of a guide tab or a panel item, or inline in tables and summaries. Always the warn pictogram + "Kontrol" (optionally "Kontrol · reason"). On the overview track it becomes a flag: number, 9px rider head and a 2px orange stem.

### Misread value
- Mono 15px bold on check-wash with 3px corners, followed by an arrow and the suggestion ("48Z13 → 48213?").

### Status bar
- 30px shell bar, 14px text: counts separated by middle dots, pending checks with the warn icon, and at the right the key list (key names bold white, actions on-shell-2).

### Qt mapping
Tokens are role-named so the build maps them once and later themes swap values.
- **QPalette:** `Window` = ground; `Base` = paper; `AlternateBase` = card; `WindowText`/`Text`/`ButtonText` = ink; `PlaceholderText` = ink-2; `Button` = paper; `Highlight` = row-cur with `HighlightedText` = ink; `Mid` = rule; `Dark` = rule-strong; `BrightText` = on-shell; disabled `Text` = ink-2.
- **Stylesheet:** header widget, `QTabBar` and `QStatusBar` on shell (`QTabBar::tab:selected` = card + ink, 6px top radius); `QToolBar`/toolbar frame and side panels on card with `border-bottom`/`border-left: 1px solid` rule; `QPushButton` paper + control-edge + 5px + `min-height: 34px` + 600, `[primary="true"]` shell; `QLineEdit`, `QComboBox`, `QSpinBox` paper + rule-strong + 4px + 34px; `QCheckBox::indicator` 18px, 3px, checked shell; `QHeaderView::section` 13px/700 ink-2 with a bottom ink-2 border, no vertical grid; `QTableView` gridline rule, row height 36px, `selection-background-color` row-cur; `QProgressBar` rule-strong frame, 3px, chunk shell; `QSplitter::handle` rule, 1px. Tooltips are not drawn in the mockups; leave them native until designed.
- **Custom-painted:** `KeyHintButton` (icon + label + key cap), guide tabs, riders and track flags, cut markers, page thumbnails, the index rule under headings (a 1px index-red bottom border on the heading frame). Qt stylesheets cannot offset an outline, so the 3px focus ring is painted in `KeyHintButton` and the page thumbnail delegate; standard fields use a 2px focus-colour border.
- **Font:** `QApplication.setFont` with Atkinson Hyperlegible Next if approved, else Segoe UI, 15px (11.25pt at 96 dpi); enable tabular figures via `QFont.setFeature("tnum", 1)` (Qt 6.7+) and fall back silently where unsupported.

## Do's and Don'ts

### Do:
- **Do** take every colour and size from the role tokens; a new screen adds layout only, never a new colour.
- **Do** show "needs a check" with the orange rider, the warn pictogram and the word "Kontrol", and nothing else in orange.
- **Do** mark cut type by tab position and pictogram first, colour second; dash the filter cut.
- **Do** put the 1px index-red rule under headings only (screen, panel meta, section).
- **Do** separate groups with 1px rules on one surface.
- **Do** keep figures tabular; right-align count columns (pages, QR counts, summary totals).
- **Do** put the key hint inside the button it triggers (one `KeyHintButton`), and tab shortcuts in tooltips and the status bar.
- **Do** pair every state colour with an icon and a word (Tamam, Kontrol, Okunmadı).
- **Do** use mono only for misread values, file names and literal name-pattern text.

### Don't:
- **Don't** use orange for brand, hover, emphasis or generic errors.
- **Don't** draw the index rule as a divider between rows or panels; rows and panels take the grey rule.
- **Don't** nest boxes: no bordered card inside a panel, no card per list item.
- **Don't** put eyebrow labels above headings, gradient text, or thick coloured side borders.
- **Don't** use emoji or Unicode glyphs as icons; icons come from the 18px, 1.75-stroke round-cap sprite.
- **Don't** set text below 13px or body text below 15px.
- **Don't** show a variable colour without the variable's name.
