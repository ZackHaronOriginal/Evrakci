---
name: Evrakçı
description: Local scan-and-split desktop tool; the job drawn as a transit line in public-wayfinding signage.
colors:
  shell: "#13294b"
  shell-raised: "#1d3a66"
  shell-ink: "#ffffff"
  shell-ink-2: "#c6d3e8"
  ground: "#eef2f7"
  panel: "#ffffff"
  rule: "#cdd6e2"
  rule-strong: "#8d9bb0"
  ink: "#15202e"
  ink-2: "#44526a"
  focus: "#0b5cd5"
  select: "#dce9fb"
  cut-qr: "#1f5fbf"
  cut-filter: "#b45200"
  cut-manual: "#b42318"
  check: "#f5c518"
  check-soft: "#fff4c2"
  check-ink: "#3d2f00"
  check-edge: "#8a6d00"
  ok: "#1b7a3d"
  doc-a: "#e3ecf8"
  doc-b: "#f3f6fa"
  var-1: "#0f7b78"
  var-2: "#6b3fb3"
  var-3: "#9a4a12"
  var-4: "#a3245f"
typography:
  brand:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "20px"
    fontWeight: 700
  value-display:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "26px"
    fontWeight: 700
    letterSpacing: "0.01em"
    fontFeature: "tnum"
  title:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 600
  body:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    fontFeature: "tnum"
  body-strong:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 600
    fontFeature: "tnum"
  label:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "14px"
    fontWeight: 400
    fontFeature: "tnum"
  label-sm:
    fontFamily: "Atkinson Hyperlegible Next, Segoe UI, system-ui, sans-serif"
    fontSize: "13px"
    fontWeight: 700
rounded:
  hairline: "2px"
  tag: "3px"
  key: "4px"
  control: "6px"
  pill: "99px"
spacing:
  xxs: "4px"
  xs: "6px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "18px"
components:
  header:
    backgroundColor: "{colors.shell}"
    textColor: "{colors.shell-ink}"
    height: "54px"
  tab:
    textColor: "{colors.shell-ink-2}"
    typography: "{typography.title}"
    rounded: "{rounded.control}"
    padding: "0 18px"
    height: "44px"
  tab-active:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.shell}"
  button:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 12px"
    height: "36px"
  button-primary:
    backgroundColor: "{colors.shell}"
    textColor: "{colors.shell-ink}"
    rounded: "{rounded.control}"
    padding: "0 12px"
    height: "36px"
  button-compact:
    typography: "{typography.label}"
    height: "30px"
  button-stack:
    height: "40px"
  key-cap:
    textColor: "{colors.ink-2}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.key}"
    padding: "0 5px"
  input:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "0 8px"
    height: "36px"
  chip:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
  chip-check:
    backgroundColor: "{colors.check}"
    textColor: "{colors.check-ink}"
    rounded: "{rounded.pill}"
  tag-check:
    backgroundColor: "{colors.check}"
    textColor: "{colors.check-ink}"
    rounded: "{rounded.tag}"
    padding: "1px 8px"
  cell-check:
    backgroundColor: "{colors.check-soft}"
    textColor: "{colors.check-ink}"
  notice-check:
    backgroundColor: "{colors.check-soft}"
    textColor: "{colors.ink}"
    rounded: "{rounded.control}"
    padding: "10px 12px"
  table-row:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    padding: "0 12px"
    height: "40px"
  table-row-current:
    backgroundColor: "{colors.select}"
  cut-tag:
    backgroundColor: "{colors.panel}"
    typography: "{typography.label-sm}"
    rounded: "{rounded.key}"
    padding: "1px 5px"
  document-band:
    backgroundColor: "{colors.doc-a}"
    typography: "{typography.label}"
    rounded: "{rounded.control}"
    padding: "0 12px"
  variable-chip:
    textColor: "{colors.shell-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.key}"
    padding: "4px 9px"
  status-bar:
    backgroundColor: "{colors.shell}"
    textColor: "{colors.shell-ink-2}"
    typography: "{typography.label}"
    padding: "0 16px"
    height: "30px"
---

# Design System: Evrakçı

## Overview

**Creative North Star: "The Transit Line"**

The job is a transit line. Pages run along one line, documents are the stops, cuts are the station markers. The visual world is public wayfinding signage: deep signage-navy panels with white lettering frame the window (header with tabs, status bar), a light cool ground carries the work, signage yellow marks every stop that needs a check, and cut types are line colours that always come with their own marker shape.

The window is dense but calm for hour-long sessions on 1366×768 office monitors. Text is large and highly legible, every frequent action shows its keyboard shortcut on a key cap, and nothing that needs attention is ever silent: a kontrol shows in the route map, the timeline lane, the side panel, the review table and the status bar at once.

The source of truth is the approved HTML mockup (`docs/superpowers/mockups/plan-5-window.html`). The product ships as a PySide6/Qt window, so every token below is named by role and is meant to become a Qt palette/stylesheet variable. The owner plans configurable looks later; swap values, keep roles.

**Key Characteristics:**
- Navy signage shell (header, primary button, status bar) around a light cool work ground.
- One line, many stops: route map, document bands and cut rails read as a transit diagram.
- Signage yellow means "kontrol" and nothing else.
- Cut type is carried by shape first, colour second.
- Large legible type (15px base, 17px titles) with tabular figures everywhere.
- Drawn line pictograms at one stroke weight; keyboard shortcut caps on every frequent action.

## Colors

A navy-and-white signage palette on a cool grey-blue ground, with three line colours, one alert yellow and four variable hues.

**Qt mapping (when built):** ground → `Window`, panel → `Base`, ink → `Text`/`WindowText`, ink-2 → `PlaceholderText` and secondary labels, select → `Highlight` for row/list selection, focus → focus frames, shell → header/status bar stylesheet and the default button.

### Primary
- **Signage Navy** (shell): header, status bar, primary button fill, active-document outline, progress fill, checked checkbox. The frame of the whole window.
- **Raised Navy** (shell-raised): dividers and key-cap borders sitting on navy.
- **Signage White** (shell-ink) and **Navy Mist** (shell-ink-2): primary and secondary lettering on navy.

### Secondary
- **Kontrol Yellow** (check): needs-a-check markers, chips, status tags and the status-bar count. Always with dark **Kontrol Ink** (check-ink) text and an alert pictogram.
- **Kontrol Wash** (check-soft): background of unsure cells, notices and unsure reads.
- **Kontrol Edge** (check-edge): border of the yellow chip and the low-confidence meter.

### Tertiary
- **QR Line Blue** (cut-qr), **Filter Line Orange** (cut-filter), **Manual Line Red** (cut-manual): cut rails, cut tags and markers. Each is fixed to one shape (see Components).
- **Variable hues** (var-1 teal, var-2 violet, var-3 rust, var-4 plum): one per template variable, used for its box, label, swatch and naming chip. Always paired with the variable's name in white on the colour.
- **Done Green** (ok): read confidence meter and "Tamam" chips/tags.
- **Focus Blue** (focus): keyboard focus rings, selected pages, the box being drawn.

### Neutral
- **Cool Ground** (ground): the work surface behind lanes and the template canvas; also the active tab, so the tab opens into the work.
- **Panel White** (panel): toolbar, route map, side panels, table, buttons, inputs.
- **Rule** (rule) and **Strong Rule** (rule-strong): hairline dividers; control and page outlines.
- **Ink** (ink) and **Ink Secondary** (ink-2): body text and secondary text, both tinted toward navy.
- **Selection Wash** (select): current table row, selected template in the list.
- **Document Band A / B** (doc-a, doc-b): alternating document bands on the timeline.

### Named Rules
**The One Meaning Rule.** Kontrol Yellow means "needs a check" and is never used for decoration, branding or emphasis. (The brand mark's middle stop is the one sanctioned exception: it shows the yellow stop on the line.)

**The Shape First Rule.** Colour never carries meaning alone. Cuts differ by marker shape and rail pattern, kontrol by an alert pictogram, variables by their name label.

## Typography

**Display / Body / Label Font:** Atkinson Hyperlegible Next (fallback Segoe UI, then system-ui), weights 400, 600, 700, bundled as latin and latin-ext WOFF2 for Turkish characters.

**Licence flag:** Atkinson Hyperlegible Next is under SIL OFL 1.1, which is not on the owner's permissive list (MIT/BSD/Apache/MPL/HPND/LGPL). It needs explicit owner approval before it ships with the app; if refused, the look falls back to Segoe UI with the same sizes and weights.

**Character:** one family throughout, chosen for low-vision legibility (distinct letterforms such as I/l/1 and 0/O), set large and plain like signage.

### Hierarchy
- **Value display** (700, 26px, 0.01em): the suggested value in the review side panel.
- **Brand** (700, 20px): the Evrakçı wordmark in the header.
- **Title** (600, 17px): tabs, panel headings, read values.
- **Body** (400 / 600, 15px): base text, buttons, inputs, table cells, panel subheadings.
- **Label** (400, 14px): secondary lines, chips, lane names, page numbers, status bar, table headers (700).
- **Label small** (700 or 600, 13px): key caps, cut tags, box labels on the page. The floor; nothing smaller in app chrome.

### Named Rules
**The Tabular Figures Rule.** Tabular figures are on everywhere (`font-variant-numeric: tabular-nums`), so page numbers, counts and ranges line up across the timeline and table.

## Layout

A fixed desktop window designed at 1366×768 and stacked top to bottom: header (54px), toolbar (36px controls, 10px/16px padding), route map (76px, full width), work area, status bar (30px). The work area is a flexible main region with a fixed right panel (324px on Kontrol, 384px on Değerler); Şablonlar uses three columns (312px list, flexible canvas, 356px reads panel).

The Kontrol timeline is a lane grid: a 96px lane-name column, then lanes for documents (54px), pages (flexible), template (42px) and values (42px). Page thumbnails are 100×141px (A4 ratio) with 108px slots; cuts are 40px gaps carrying the rail and marker.

Spacing steps are 4, 6, 8, 12, 16 and 18px: 8px between toolbar controls, 16px outer padding on bars, 18px inside side panels, 12px table cell padding. Table rows are 40px.

## Elevation & Depth

Flat by default; depth comes from tonal layers (navy shell, white panels, cool ground) and 1px rules. Shadows only lift paper so it reads as paper.

### Shadow Vocabulary
- **Thumbnail paper** (`box-shadow: 0 1px 3px rgba(19, 41, 75, .18)`): page thumbnails on the timeline.
- **Page on canvas** (`box-shadow: 0 3px 12px rgba(19, 41, 75, .18)`): the enlarged A4 page in the template creator.

### Named Rules
**The Paper Only Rule.** Only representations of paper cast shadows. Panels, buttons, chips and bars stay flat.

## Shapes

Gently rounded controls (6px) for buttons, inputs, tabs (top corners only), notices, document bands and list rows; 4px for key caps and cut tags; 3px for status tags and swatches; 2px for paper and drawn boxes, which stay nearly square; fully round pills (99px) for lane chips. Outlines are 1px; drawn template boxes and cut rails are 2–3px. Dashed strokes mean "variant" or "filter", never decoration.

## Components

### Buttons
- **Shape:** gently rounded (6px), 36px tall, 1px strong-rule border, pictogram + label + key cap.
- **Default:** panel white with ink text.
- **Primary:** signage navy fill, white text, key cap in navy tones. One per toolbar.
- **Focus:** 3px focus-blue outline, 2px offset.
- **Disabled:** grey text, light rule border.
- **Compact (30px, 14px text)** inside panels and progress rows; **stacked (40px, left aligned, key cap pushed right)** for the review action list. Icon-only buttons are 36px square with a tooltip.

### Key caps
Every frequent action shows its shortcut in a small outlined key cap (13px, 4px radius) inside the button or tab.

### Tabs
Signage tabs in the navy header: 17px semibold, Navy Mist text; the active tab takes the cool ground colour with navy text so it opens into the work area.

### Chips and tags
- **Lane chips:** pills, 14px, white with strong-rule border; done chips green text, empty chips dashed.
- **Kontrol chip / tag:** yellow fill, Kontrol Ink, bold, with alert pictogram.
- **Variable chip:** variable hue fill with white semibold name; builds the file-name pattern.

### Inputs / Fields
36px, 1px strong-rule border, 6px radius, 8px side padding, panel white. Search fields carry a pictogram inset at the left.

### Review table
Sticky header (14px bold, secondary ink), 40px rows with rule dividers. Current row in Selection Wash; unsure cells in Kontrol Wash with alert pictogram; the focused cell gets a 3px inset focus ring; hand-edited values carry a small "elle" tag.

### Notices
Kontrol Wash fill, 6px radius, alert pictogram, a sentence of explanation and one action button.

### The Route Map (signature)
The whole job as one horizontal line across the full width: documents as stops, kontrol stops as yellow diamonds, cut types as line segments, the visible window boxed in focus blue. Click to jump. A legend at the right repeats each marker shape.

### Cut markers (signature)
A cut is a gap with a vertical rail and a 29px station marker, plus a small outlined tag above it:
- **QR separator:** solid blue rail, filled blue disc with QR pattern.
- **Filter:** dashed orange rail, white disc with dashed orange ring and funnel.
- **Manual:** solid red rail, red rounded square with scissors.

### Document bands and page thumbnails
Documents are rounded bands alternating doc-a / doc-b; the current document has a 2px inset navy outline. Selected pages get a 3px focus-blue outline; skipped blank pages are faded, dashed and italic-numbered.

### Pictograms
Drawn line icons on a 24px grid, shown at 18px (15–16px inline), 1.8px stroke, round caps and joins, `currentColor`.

## Do's and Don'ts

### Do:
- **Do** take every colour, size and radius from the role tokens so the look can be swapped later.
- **Do** pair each cut colour with its fixed marker shape and rail pattern (QR disc, filter dashed ring, manual square).
- **Do** show the keyboard shortcut on a key cap for every frequent action, and a visible 3px focus ring.
- **Do** keep body text at 15px or larger and nothing in app chrome under 13px.
- **Do** repeat a kontrol everywhere the user might look: route map, lane, side panel, table, status bar.

### Don't:
- **Don't** use Kontrol Yellow for anything but "needs a check".
- **Don't** carry meaning by colour alone.
- **Don't** add shadows to panels, buttons or chips; only paper casts shadows.
- **Don't** add chamber branding; Evrakçı is a neutral tool.
- **Don't** use text glyphs (▲, ✓, ⚠) as icons; use the drawn pictogram set.
