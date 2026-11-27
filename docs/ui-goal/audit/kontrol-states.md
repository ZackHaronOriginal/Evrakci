# Kontrol audit: state matrix

Phase 4, Görev A, screen Kontrol. Rows are elements or groups from `kontrol-inventory.md` (E-ids). Columns are the states from
the phase plan. Every cell is one of: a screenshot reference, a measured row, or `n/a: reason`. A cell that could not be filled says
`GAP: reason` instead of a guess; the gaps are counted at the end.

How the cells were made (all offscreen, synthetic demo job from `tools/screenshots.py:build`, window 1366x768, text 100 percent unless
named):
- Screenshots: `/tmp/claude-0/p4/kontrol/states/<theme>-<NN>-<name>.png` for theme `light`, `dark`, `hc` (89 files: 9 from `tools/screenshots.py states`, 80 from my own scripts). Written by a small
  script (session scratchpad `p4_kontrol_states.py`, `states2.py`) that builds a fresh window per theme, puts the element into the state
  (QTest mouse move and press, `setDown`, Tab focus, selection, delete, loupe, context menu event, `set_state` on the strip, zoom),
  and grabs the window or the widget. Plus the 72 matrix files in
  `/tmp/claude-0/p4/kontrol/matrix/` (6 tabs x 3 themes x 2 sizes x 2 text sizes).
- Measured: `/tmp/claude-0/p4/kontrol/measure.tsv` from `python tools/ui_measure.py --tab kontrol` (3 themes x 1366x768, 1920x1080 x
  text 100, 150): 4164 rows, 30 fail. The tool measures the default state only: hover, pressed and loupe colours are not measured
  (GAP in those cells; the screenshots are the evidence).
- Names: `NN` below. 01 default, 02 focus on a page, 03 two pages selected, 04 three pages deleted (with toast), 05 hover on a page,
  06 mouse pressed on a page, 07 inspector with nothing selected, 08 inspector with long text, 09 command-bar hover, 10 command-bar
  pressed, 11 command-bar focus (Tab reason), 12 undo disabled, 13 approve hover, 14 approve focus, 15 approve pressed, 16 focus on a
  selection-card row, 17 loupe, 18 context menu, 19 overview with 240 documents, 20 zoom 50, 21 zoom 200, 22 filter dialog,
  23 go-to dialog, 24 (light only) inspector with a long template name at 150 percent, 25 thumbnails still loading, 26 blank pages
  dropped, 27 empty state with no job, 28 (dark only) text 150 with a selection.

Measured facts used below (all themes, sizes, text sizes): smallest hit area of a clickable widget 24x24 (the two zoom buttons,
AUD-HIT-01 passes at 24, AUD-HIT-02 fails, F-kontrol-09); every other button 32 px or more high; smallest body-text contrast 7.56:1
(DEC-CON-01, inspector primary button, light); smallest secondary-text contrast 6.14:1 (status bar, DEC-CON-02 needs 4.5); smallest
text 13 px at 100 percent, 20 px and up at 150 (DEC-TYP-01 pass, 303 rows); focus ring 3 px on all 273 focusable widgets measured
(DEC-FOC-01) except the title tabs in a single-tab run (F-kontrol-19) and the timeline (item view: ring per item, "skip", seen in 02).

## 1. Page tile and its parts (E-040 to E-054)

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long text / many items |
|---|---|---|---|---|---|---|---|---|---|---|
| Page tile (E-043) | 01 | 05: no visible change (F-kontrol-11) | 06 | 02 (ring) | 03 (ring + badge), 28 at 150 percent | n/a: tiles are never disabled; a deleted tile is dimmed (04) | n/a: with no pages the screen shows the empty state 27 | 25 (paper + "Yükleniyor") | GAP: a failed render keeps the loading look (B-024, code `thumbnails.py`); not reproduced in a window | 20 (zoom 50: 74x105 px), 21 (zoom 200: 296x418 px, one page per row); a 1000-page job is covered by `perf-profile`, not here |
| Page caption (E-044) | 01 ("1", "2", "3") | n/a: no hover state | n/a: part of the tile | n/a: follows the tile | 03 (bold accent number) | n/a | n/a | n/a | n/a | 21 (caption stays under the tile) |
| Deleted page (E-047) | 04 (dimmed, bin disc, "1 Silinecek"; hc: hatch in the hc disabled colour, bright green) | GAP: hover has no state anywhere | GAP | 04 (ring on the first tile) | 04 (selected and deleted) | n/a | n/a | n/a | n/a | the caption "N Silinecek" with a 3-digit page number: GAP (not rendered) |
| Dropped empty page (E-048) | 26 ("8 Boş") | n/a: see tile | n/a | n/a | GAP | n/a | n/a | n/a | n/a | n/a |
| Separator tile (E-049) | 01 ("Ayraç 4", written upwards) | n/a: no hover state | n/a | n/a: separators take no ring in the demo; with Right the ring moves onto them (P-030) | 03 (selection badge not shown on separators in the shot) | n/a | n/a | n/a | n/a | zoom 50: 32 px wide tile (20) |
| Guide tab, cut icon, number, check (E-040) | 01 | n/a: not interactive | n/a | n/a: not focusable | n/a | n/a | n/a | n/a | n/a | 3-digit numbers: GAP |
| Lip (E-041) | 01 (solid under the tab; dashed and dotted lips need a filter or manual cut: 04 shows none) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Kontrol rider (E-042) | 01 orange "Kontrol" with a warning icon (document 2) | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |
| Rubber band (E-036) | n/a: only while dragging | n/a | P-012: drawn (band is not None), pages selected | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## 2. Overview strip (E-030 to E-033)

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long / many |
|---|---|---|---|---|---|---|---|---|---|---|
| Strip and squares | 01 (3 documents, orange square for the one with a check) | GAP: no hover state and no tooltip (F-kontrol-10) | GAP: click jumps (P-018) | n/a: NoFocus (P-020, F-kontrol-10) | the ring on the documents in view | n/a | n/a: with no job the strip is not built | n/a | n/a | 19 (240 documents, 119 reviewed, 6 with checks; ring over 100 to 112) |

## 3. Command bar (E-010 to E-023)

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long text |
|---|---|---|---|---|---|---|---|---|---|---|
| Icon-only buttons (Geri al, Yinele, Birleştir, Sağa döndür, Sayfayı sil, Şablonu uygula, Filtre, Sonraki incelenmemiş, Git, Önizle, panel) | 01 | 09 (Kes shown; the others share the style) | 10 | 11 (Kes) and the Tab walk (keywalk, 12 combinations OK) | n/a: not toggles; the panel button changes its tooltip instead | 12 (Geri al disabled at the start of history), 27 (every command disabled with no job) | 27 | n/a | n/a | tooltips at 150 percent: GAP |
| Buttons with a label (Kes, Sonraki kontrol) | 01 | 09 | 10 | 11 | n/a | 27 | 27 | n/a | n/a | label "N sayfayı sil" at 150 percent: GAP |
| Diğer komutlar | 01 | GAP | GAP | keywalk step "moreButton" | n/a | n/a | n/a | n/a | n/a | menu of 8: P-090 |
| Measured | AUD-HIT-01 pass (36x36 and 44x44), AUD-HIT-02 pass (32 px), DEC-ICO-01 pass (16, 20, 24 px), HIG-CTL-06 pass (tooltip on every icon button), AUD-A11Y-01 pass | not measured | not measured | DEC-FOC-01 pass, 3 px | | | | | | |

## 4. Inspector (E-060 to E-089)

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long text / many items |
|---|---|---|---|---|---|---|---|---|---|---|
| Title, sub line, reason (E-072 to E-074) | 01 | n/a: static text | n/a | n/a | n/a | n/a | 07 ("Belge seçilmedi" and the hint) | n/a | n/a | 08, 24: sub line wider than the panel, everything cut at the right edge (F-kontrol-03); measured: content 304 px in 296 px (25-character template name, 100 percent), 461 in 375 (150 percent), 700 in 375 (45 characters) |
| Rows Kesim, Önceki, Durum | 01 | n/a: static | n/a | n/a | Durum "İncelendi" after approval (P-052) | n/a | 07 (rows hidden) | n/a | n/a | 08 ("Önceki" value cut) |
| Row Şablon uygula / Filtre uygula (ActionRow) | 03 (the card appears with a selection) | GAP | GAP | 16 | n/a | 07 (card hidden) | 07 | n/a | n/a | template name in the value: GAP |
| Pinned button Belgeyi onayla | 01 | 13 | 15 | 14 (Enter does nothing, F-kontrol-04) | n/a | 07, 27 | n/a | n/a | n/a | n/a |
| Pinned button Değerlerde aç | 01 | GAP (same style as 13) | GAP | keywalk step | n/a | 07 | n/a | n/a | n/a | n/a |
| Diğer belge komutları (...) | 01 | GAP | GAP | keywalk step | n/a | n/a | n/a | n/a | n/a | menu of 4: P-084 |
| History rows | after any edit (04 shows "3 sayfa silinecek 14:18") | n/a | n/a | n/a: rows are not focusable | n/a | n/a | card hidden when empty (01) | n/a | n/a | 3 rows shown, 10 kept |
| Whole panel | 01 | n/a | n/a | n/a | n/a | n/a | 07 | n/a | n/a | the card scroller with its hairline: GAP (the demo fits at 1366x768 100 percent; AUD-WIN-02 pass) |
| Measured | DEC-CON-01 pass, min 7.56:1 | | | DEC-FOC-01 pass 3 px | | | | | | HIG-TYP-07 pass for the demo text, not for long names (F-kontrol-03) |

## 5. Status bar (E-090 to E-097)

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long / many |
|---|---|---|---|---|---|---|---|---|---|---|
| Counts "Belge", "Sayfa", "N sayfa seçili", "⚠ ... kontrol bekliyor", "✓ ... incelendi" | 01, 03 (selected count appears), 28 at 150 percent | n/a: static | n/a | n/a: not focusable | n/a | n/a | 27 (single line "İşler Yükle sekmesinde açılır (Ctrl+1)") | n/a | n/a | 3-digit counts: GAP |
| Message line | message after a refused command (P-040 "İlk belgenin öncesi yok.") | n/a | n/a | n/a | n/a | n/a | empty text | n/a | long message: the text is a plain label, never cleared (O-05) | GAP |
| Zoom group: minus, slider, plus, "%100" | 01 | GAP | GAP | keywalk steps (3) | n/a | n/a: in 27 the group stays | n/a | n/a | n/a | slider at min and max: 20, 21 |
| Measured | DEC-CON-02 pass (min 6.14:1) | | | DEC-FOC-01 pass | | | | | | **AUD-HIT-02 fail: buttons 24 px** |

## 6. Timeline view, scroll bar, empty space (E-030 area)

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long / many |
|---|---|---|---|---|---|---|---|---|---|---|
| Timeline | 01 | n/a: see tile | 06 | 02 | 03 | n/a | 27 (replaced by the empty page) | 25 | B-024 | 20, 21; scroll range 307 px at 15 pages (P-015) |
| Scroll bar | 01 (right edge) | GAP | GAP | n/a: not focusable (`AUD-HIT-01 skip: thin scroll bar`) | n/a | n/a | n/a | n/a | n/a | at 21 (zoom 200) |
| Measured | DEC-FOC-01 skip (item view: ring per item) | | | ring visible in 02 (white ring in dark, 3 px) | | | | | | AUD-WIN-02 pass: no window-sized scroll bar |

## 7. Context menu, template menu, overflow menus (E-060 to E-069, E-075, E-022)

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long / many |
|---|---|---|---|---|---|---|---|---|---|---|
| Page context menu | 18 | GAP: native hover of QMenu items, not captured | GAP | keyboard walk inside the menu: GAP (offscreen cannot grab the keyboard; Esc was sent to the menu, P-008) | n/a | "Şablon uygula" submenu shows a disabled hint when there are no templates (code `kontrol_actions.py:context_menu`); not captured | n/a | n/a | n/a | header "3 sayfa seçili", entries follow the count |
| Template menu (inspector row) | P-086 lists 2 templates, current checked | GAP | GAP | GAP | checked item = the template last used | disabled hint: GAP | n/a | n/a | n/a | 30 templates: GAP |
| Diğer menus (command bar, inspector) | P-084, P-090 | GAP | GAP | GAP | n/a | n/a | n/a | n/a | n/a | n/a |

## 8. Toast (E-100 to E-103)

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long text |
|---|---|---|---|---|---|---|---|---|---|---|
| Toast with Geri al | 04 and 17 (visible in the corner, over the inspector buttons: F-kontrol-07) | GAP | P-103 (double click on Geri al undoes one step) | n/a: not in the Tab order, mouse and Esc only | n/a | n/a: "Geri al" is left off when the step is stale (code `available`) | n/a | n/a | n/a | "Belge 1: bütün sayfaları silinecek, belge dışa aktarılmayacak." fits in 17; a 3-document message: GAP |

## 9. Dialogs

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long / many |
|---|---|---|---|---|---|---|---|---|---|---|
| Filtre uygula dialog | 22 | GAP | GAP | opens on the spin box (P-064) | n/a | n/a | n/a | n/a | N below 1 cannot be typed (spin box minimum 1) | n/a |
| Belgeye veya sayfaya git dialog | 23 | GAP | GAP | P-065 | radio Belge / Sayfa | n/a | n/a | n/a | out-of-range values are clamped by the spin box | 3-digit counts: GAP |

## 10. Loupe (E-110 to E-120)

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long / many |
|---|---|---|---|---|---|---|---|---|---|---|
| Loupe as a whole | 17 (hc: page, head, mode buttons, strip, chevrons) | GAP | GAP | P-006 (focus returns to the timeline) | n/a | n/a | n/a: with 0 pages it does not open (K-98) | GAP: no capture while the page renders | GAP | zoom 10 to 200: P-094 (mode becomes "custom") |
| Mode buttons | 17 (Sığdır selected) | GAP | P-093 | GAP | 17 | n/a | n/a | n/a | n/a | n/a |
| Strip thumbnails | 17 | GAP | P-095 | n/a | 17 (ring on page 5) | n/a | n/a | strip renders on demand | n/a | 15 pages fit; a 640-page strip: GAP |
| Chevrons, Kapat | 17 | GAP | P-092b | keywalk: the loupe is not part of the Tab walk (focus stays on the loupe widget) | n/a | n/a | n/a | n/a | n/a | n/a |
| Measured | not measured (the tool measures the base window only) | | | | | | | | | |

## 11. Empty state (no job) (E-130 to E-135)

| Element | Default | Hover | Pressed | Focused | Selected | Disabled | Empty | Loading | Error | Long / many |
|---|---|---|---|---|---|---|---|---|---|---|
| Title, text, two buttons, "Son işler" card | 27 (all three themes) | GAP | GAP | Tab order: GAP (keywalk walks the demo job, not this page) | n/a | n/a | this is the empty state | n/a | n/a | one recent job shown; 3 rows: GAP |

## Gaps

Counted from the cells above: about 55 cells say `GAP` (the word appears 60 times). Almost all are hover and pressed colours of buttons and menus (the screenshots show
one example per kind, not each button), controls only reachable with a longer script, and three-digit counts. None of the gaps hides
a failing rule; the findings do not depend on them. The two states that are real gaps in coverage are the failed-render tile
(B-024, known) and the loupe while a page renders.
