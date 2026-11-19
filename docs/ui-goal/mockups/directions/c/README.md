# Direction C: "Kartotek"

Round 2, third direction from `../BRIEF.md` §4. HTML mockups of the Qt window at 1366×768, in light
and dark. All data is invented. `docs/ui-goal/decisions.md` (D1–D13) wins wherever this file
disagrees. Every place where it disagrees is listed under "Deviations" below, for the owner to approve.

| File | What it is |
|---|---|
| `kontrol.html` | Kontrol. State `main`: the whole job on the spine, document stacks with guide tabs per cut type, 3 selected pages, focus ring, context menu, inspector, status line with zoom. State `menu`: Alt pressed, app menu open with access keys underlined. |
| `degerler.html` | Değerler: values table and linked page crop. Confidence shown as Emin / Orta / Kontrol / Okunamadı, uncertain characters tinted, one cell being edited, a toast with Geri al. |
| `tokens.css` | All tokens, light and dark. The D10 contrast proof is the comment at the top and is generated. |
| `shell.css` | Window chrome and shared components. Uses only `var(--…)`. |
| `icons.js`, `_icons.py` | Inline sprite of 43 Lucide icons (lucide-static 0.460.0, ISC; paths copied verbatim). Rebuild with `python3 _icons.py <lucide>/icons`. |
| `_contrast.py` | Copied from `../../_contrast.py` and adapted to these token names (53 pairs per theme, plus the hue check against the rider). `--write` refreshes the table in `tokens.css`. It exits 1 on any failure. |
| `_render.py` | Copied from `../../_render.py`. Run `python3 _render.py kontrol.html degerler.html --no-text150`. It writes `png/` and reports clipping, ellipsis, sideways scroll and repeated or non-ASCII access keys. |
| `png/` | `kontrol-{light,dark}`, `kontrol-menu-{light,dark}`, `degerler-{light,dark}`, plus `compare-round1-vs-c.png` (round 1 and C side by side, same data). |

Last run: 0 clipping warnings and 0 failing contrast pairs, in both themes.

---

## 1. Concept

**The window is a filing cabinet, and the documents are the brightest thing in it.**

- **The cabinet.** One 44 px band in cabinet green holds the title bar, the logo, the app menu, the six
  stations as index tabs, the job name with its save state, and the command search. The selected tab is
  cut from the same sheet as the desk below it, with inverted corners. It reads as an index card
  pulled out of the drawer, not as an Office tab with an underline. That is the brand's guide-tab idea
  turned into navigation.
- **The desk.** The work happens on a quiet stone-grey desk. Light mode uses `#e8e7e2`, which has
  almost no chroma; it is deliberately *not* the cream `#F4F1EA` that AI tools tend to produce. Dark
  mode uses untinted graphite `#282a29`, so scans read true. Panels are lighter sheets lying on the desk:
  8 px radius, a 1 px stroke and no shadow. White pages are the brightest surface and are the only
  items that cast the soft paper shadow. In dark mode the desk becomes a Lightroom-style darkroom and
  the paper is dimmed to `#e4e4df` so it does not glare.
- **One memorable thing: the filed stack.** Each document has a manila guide tab standing on a 2 px
  folder edge that spans its pages. The tab's position, pictogram and edge style give the cut type:
  QR is left with a solid edge, filtre is centred with a dashed edge, elle is right with a dotted edge.
  The orange rider sits at the opposite end of the same strip. Nothing else sits around a document
  while it is at rest. The spine above the timeline repeats this in miniature: manila ticks mark
  document starts, and the kontrol flags are the small orange trapezoid of the logo's middle tab.
- **Colour has jobs, not moods.** Green means the cabinet (the band) and the one primary action.
  Manila means a filed document starts here. Orange means kontrol, and it always comes with the
  triangle icon and the word. Everything else is neutral.

The two-second read changes from round 1's "grey Word 2010 strata" to "a green drawer, a calm desk, big
white pages". Compare `png/compare-round1-vs-c.png`.

## 2. What the screens show

**Kontrol (`main`).** The page pattern is Split Pane (pattern 8): the timeline is the list and the
inspector is the detail. Under the band there is a 48 px command row on the desk. It has 2 text labels
(Kes, Sonraki kontrol); everything else is a 32 px icon button with a named tooltip and shortcut. Below it
is the 28 px spine: the whole job of 640 pages, a viewport box at pages 66–77, 7 kontrol flags and the
reviewed runs, with the legend "⚠ Kontrol 7" in icon plus word. The timeline shows Belge 14–18 as filed
stacks of 166×234 px pages, QR separator sheets as slim divider cards, and page 71 as "Silinecek".
Pages 72–74 are selected (tray tint and check badge); page 74 has the focus ring, and the context menu is
open on it. The inspector is a floating sheet. Its header "Belge 16" is the screen's one page title. It
shows the rider with the reason in plain ink, and a **boundary preview** for "Neden burada başlıyor?":
the last page of Belge 15 and the first page of Belge 16 with the filtre cut between them, then the
facts. Below that is the single filled primary "Belgeyi onayla" (Enter), two standard buttons, and the
selection tools at the foot. The status line shows the counts and a thumbnail-size slider with %.

**Kontrol (`menu`).** Alt was pressed, so the "≡" app menu is open. It lists Dosya, Düzen, Görünüm, Git,
Araçlar and Yardım with access keys underlined (they are underlined only now), plus "Komut ara Ctrl+K".
The Düzen submenu shows the named undo ("Geri al: Kesim ekle") and the Kontrol verbs with their keys.
This state proves gate 2.

**Değerler.** The page pattern is Split Pane, with a table on the left (see deviation 9). The table
lies on its own sheet. Its header carries a segmented filter (Kontrol gerekenler 14 / İncelenmemiş 105 /
Tümü 152) and the search field; there is no separate heading, so the filter is the title. 13 rows of
40 px are visible, and cells use 15 px body text. The Güven column carries the row's single status,
with icon, word, colour and percentage. Uncertain characters are tinted inside the values (wash plus a
2 px underline, so the cue is a shape and not only a colour). The Sicil no cell of row 16 is being
edited in place, in the same box with no layout shift: it has a 2 px green bottom line, and a hint
popover lists Enter and Esc as quiet text, not keycaps. The right sheet shows the linked crop on a
matte with the field ringed. Below it the **Okunan / Öneri** comparison is set at 24 px; it is the screen's
one page-title-size element, because the value is the hero here. Then come the status and reason, the
toast "8 değer onaylandı · Geri al" above the action footer, the primary "Onayla ve sonrakine geç" (Enter),
and "Elle yaz" (F2) and "Yeni varyant çiz" (V).

## 3. Token summary (`tokens.css`)

| Group | Light | Dark | Notes |
|---|---|---|---|
| Band | `--shell #3f5a4c`, `--on-shell #fff` (7.56), `--on-shell-2 #d9e4dd` (5.84) | `#18211c`, `#fff`, `#b4c3ba` | the cabinet; `--focus-on-shell #fff` for focus on tabs |
| Surfaces | desk `#e8e7e2` · layer `#fafaf8` · well `#f0efeb` · popover `#fff` · selected `#dde8e1` | `#282a29` · `#313432` · `#2a2d2b` · `#3a3e3c` · `#2f4a3c` | desk → layer ΔL ≈ 6.5 (light), ≈ 4.5 (dark) |
| Paper | `--paper #fff`, `--shadow-paper` (alpha ≤ 0.07) | `#e4e4df` (dimmed) | the brightest thing on screen |
| Text | `#1d2a23` (12.05–14.66) · `#4f5953` (5.84–7.11) | `#e7ebe8` (9.33–11.97) · `#b4bcb7` (≥ 4.5 on all, incl. hover) | |
| Lines | `--stroke` (decorative) · `--stroke-strong` · `--edge #7b857f` (inputs, ≥ 3:1) | `#3d413f` · `#4a4f4c` · `#8c9690` | buttons need no 3:1 border (brief §3, C6) |
| Accent | `--accent #3f5a4c` + white (7.56) · `--select-ring #2f5a44` | `#8fbf9f` + `#0f1d16` (8.24) | primary, selection, slider; never decoration |
| Focus (D11) | outer `#1d2a23`, inner `#fff` | outer `#f2f4f2`, inner `#111513` | ≥ 3:1 on desk, layer, tray, popover and band |
| Filing | manila `#e9d9a6` / edge `#857340` / ink `#2b2410`; rider `#e8731a` / ink `#2a1400` / edge `#9c4a0b`; `--check-text #8a3d00`; `--check-wash #fbe2c8` | rider unchanged; check-text `#ffad6e`; wash `#4d3420`; `--check-wash-paper` stays light on scans | orange is kontrol only (hue check: every other saturated token is ≥ 30° away) |
| Status | ok `#1d6a3c` · danger `#ad1f3b` · info `#2a5d99` | `#82cf9b` · `#ff9aa9` · `#8db8ec` | |
| Type | Inter 15/21 body, 13/18 floor; Inter Display 20/28 and 24/32; weights 400/500/600; `--features` tnum + cv05; `--features-value` adds cv08; `--features-decide` adds slashed zero | | |
| Space / radius | {4, 8, 12, 16, 24, 32, 48} / {2 sheet, 4 control, 8 layer} | | |
| Chrome | band 44 · command row 48 · spine 28 · status 28 · inspector 320 | | |
| Motion (D7) | 80 / 120 / 180 / 240 ms; standard (0.2,0,0,1), enter, exit; 0 under reduced motion | | |
| Shadow | `--shadow-pop` is the one floating level (menus, popovers, toasts) | dark: alpha 0.34 + `--edge-light` top highlight | |

## 4. Round-2 gates (measured on the rendered DOM)

| Gate | Result |
|---|---|
| 1. Chrome ≤ 120 (Kontrol ≤ 150 incl. overview) | Kontrol: 44 + 48 + 28 + 28 = **148**. Değerler: 44 + 48 + 28 = **120**. Round 1: 248 / 152. |
| 2. No resting menu row, no underlines until Alt | Yes: "≡" plus Alt; `kontrol-menu-*` shows the Alt state. The access keys D E G T A Y are ASCII, without I, and unique (checked by `_render.py`). |
| 3. ≤ 3 text labels per command bar; 28–36 px icon buttons | Kontrol 2 (Kes, Sonraki kontrol). Değerler 2 (Değerleri oku, Sonraki kontrol) plus the Şablon picker. Icon buttons are 32 px. |
| 4. ≥ 2 surface levels, a rounded layer, no inner full-width rules | desk / layer / well / popover; 8 px sheets; only the table has rules (header and rows). |
| 5. Exactly one page-title-size element | Kontrol: "Belge 16". Değerler: the Okunan / Öneri value pair. Pane titles are 15 semibold. |
| 6. One orange mark per kontrol item; keycaps only in palette, sheet and tooltips | One rider per document, one status per row. Shortcuts appear as quiet text; there are no keycaps anywhere. |
| 7. Kontrol ≥ 60 % page pixels, thumbnails ≥ 132 px | **60.8 %**, 166×234 px. |
| 8. No dashed boxes at rest | none (the dashed line is the filtre folder edge, which is information, not a drop zone) |
| 9. Keeps intact; contrast passes | `_contrast.py`: 0 failures in light and dark. HC and 150 % were not rendered in this round (see §8). |
| 10. Side-by-side sheet | `png/compare-round1-vs-c.png` |

## 5. How each skill changed a concrete decision

| Skill | What it changed |
|---|---|
| `frontend-design:frontend-design` | **Spend boldness in one place.** The green band and the filed stack are the only loud things; everything else on the desk is neutral. The skill's calibration list also changed two values. The warm "paper" desk the brief suggested (`#F4F2EC`) sits right next to the AI-cream tell `#F4F1EA`, so the desk became low-chroma stone `#e8e7e2`, with Inter only and no serif. Middle-dot meta strings were removed everywhere ("Ekspertiz Raporu, sayfa 72–73"; the status line uses 24 px gaps instead of dots). |
| `vectorlab-ux-skills:anti-slop` | Deleted decoration and kept structure. There are no pills around metadata: page numbers, reasons and counts are plain text. The cut colours from round 1 (blue, plum, slate) are gone because the position, pictogram and edge already carry the type. There is no glass or blur. The table keeps its frame and hairlines, because an empty-looking table would fail the skill. Search is the only input with an icon. |
| `vectorlab-ux-skills:typography` | Three weights (400/500/600), size hierarchy rather than weight hierarchy, and four sizes per screen (13, 15, 24, plus 20 reserved). Table cells were measured at 15 px, not meta size. The skill's "variable font + tracking" warning is why the titles use the static **Inter Display** cut with only −0.01em tracking. Its body = 16 px is overridden by D4 (15). |
| `vectorlab-ux-skills:colour-palette` | 60-30-10 measured on the PNGs: desk and paper ≈ 60 %, sheets and band ≈ 30 %, green, manila and orange ≈ 10 %. Elevation is a border first: panels have a 1 px stroke and **no** shadow, and only floating layers get the one soft shadow (alpha 0.07, below 0.08). In dark mode a `--edge-light` top inset replaces the shadow. The table is an L1 sheet with hairlines, not text lying on the desk. |
| `vectorlab-ux-skills:spacing` | Large gaps between groups, small ones inside them. Document gap 24 against page gap 8, so grouping is spatial and nothing needs to be drawn. The inspector groups use 16–24 between groups and 4–8 inside. Every value is on the 4/8 grid; the one optical nudge is the 12 px divider-to-document gap. |
| `vectorlab-ux-skills:surfaces` | Single-field editing is inline in the same box (the Sicil no cell keeps its 40 px row; Enter saves, Esc cancels). The inspector and crop are non-modal side sheets, never dialogs. Deleting is undoable instead of confirmed (research 04 r11 and the owner's answer override the skill's confirm-first rule), and the menu item names the count: "3 sayfayı sil". |
| `vectorlab-ux-skills:icon-buttons` | It collapsed 10 of round 1's labelled commands into square 32 px icon buttons. Each one has an `aria-label` that holds the tooltip text and shortcut ("Önceki belgeyle birleştir (M)"). Labels stay on the primary, the destructive menu item and the two core verbs. The 44 px web hit-target rule is translated to D5's 32 px desktop controls. |
| `vectorlab-ux-skills:page-patterns` | I named the pattern before building: both screens are **Split Pane (8)**. That choice is why the inspector shows only the selected item, why selection updates only the right side, and why there is no KPI strip. Değerler breaks one catalog rule, "no DataTable in the left pane", on purpose; see deviation 9. |
| `vectorlab-ux-skills:empty-states` | No empty state is rendered here, but the empty-state rules shaped the toast and the unread cell. The Okunamadı cell says "değer yok" and the row status names the problem. For the empty Kontrol state (Phase 3) the spec is: the timeline frame stays in place, with "Henüz sayfa yok", one sentence, "PDF ekle" (Ctrl+O) and no illustration. |
| `design:design-system` | Every value is a token: no hex in `shell.css` or the page styles (the logo SVG keeps its brand fills). Tokens are named by role, not by value (`--bg-well`, `--select-ring`, `--check-wash-paper`), and the contrast pairs are tested. `--check-wash-paper` and `--features-decide` were added when the audit found two real gaps: the dark-mode wash hid letters on light scans, and slashed zero made whole tables look monospaced. |
| `ui-design-review:ui-compare` | UXKIN does not connect here, so the comparison uses the named apps' known conventions. **Lightroom**: the darkroom surround, dimmed paper and image-as-hero sizing (60 % page pixels). **Windows 11 Explorer and Edge**: tabs in the title band, with the selected tab joined to the content by inverted corners. **Figma UI3**: floating rounded side sheets on the canvas. **Outlook and Linear**: one status glyph per row in a fixed column. **Windows 11 Notepad**: menus behind Alt. What differs is the brand band. Most of these apps keep the title neutral; C makes it the cabinet, and that is the risk the owner should weigh (§7). |

## 6. Iterations (what the critique passes changed)

1. **First render.** The band overflowed by 8 px, so the command search was narrowed. The inspector's
   button pair clipped. The spine's 96 ticks read as a ruler, so they became 6 px high at 45 %. The
   paper looked flat, so a second, wider shadow at alpha 0.05 was added. The inspector had 100 px of
   dead space, which the selection group now anchors at the foot.
2. **Second pass.** The selection rings on adjacent trays looked heavy, so selection is now the tray
   tint plus the check badge, and the ring is kept for focus only. The empty middle of the inspector got
   the boundary preview, which answers "Neden burada başlıyor?" with pictures instead of words. In
   Değerler the toast covered the secondary buttons and now sits above the action footer. The dark
   uncertain-character wash hid letters on the light scan, so a paper-specific token was added. Inter's
   tnum and slashed zero made the table look monospaced, so the slashed zero is now kept only where O and 0
   are decided (edit cell, comparison, crop). The Okunamadı cell no longer repeats the status word.
3. **Third pass.** Page share measured 53.7 %, below gate 7, so the pages grew to 166×234 and the row
   gap tightened, giving 60.8 %. The dark menu hover was invisible because hover equalled the popover
   colour, so it was fixed and secondary text was lifted to keep 4.5:1 on hover. The Alt/app-menu state
   was added. Off-scale radii were removed, and the % was restored next to the zoom slider.

## 7. Deviations from `decisions.md` and GOAL (owner approval needed)

| # | Decision | What C does | Why |
|---|---|---|---|
| 1 | **D2** "quiet surfaces, one accent" | The title and tab band is a cabinet-green surface, about 6 % of the screen. The work surfaces stay quiet. | It is the direction's identity: nobody mistakes it for Office, and the brand stops being a 16 px icon. Risk: strong colour for an hour-long session. Mitigations: the band is only 44 px, the desk and panels are neutral, and the dark band is near-black. If you want it quieter, the same layout works with `--shell` set to the desk colour (that becomes direction A). |
| 2 | **GOAL 3.1** "a menu bar" | There is no resting menu row. The "≡" app button in the band holds all six menus; **Alt** opens it with the access keys underlined; Alt+D/E/G/T/A/Y open each menu directly; Ctrl+K searches every command. | A resting text menu row was round 1's strongest "old Win32" signal (brief C2). Every menu, item and key is still there. |
| 3 | **D6** radii "8 for dialogs, menus, popovers" | 8 px is also used on the floating sheets (inspector, table, crop) and the tops of the index tabs. Circles are used for the slider thumb and the selection check badge. | It gives a rounded content layer (gate 4). The circles are the standard shape for those two controls. No other new radius: the segmented items and viewport box use 2. |
| 4 | **D3** font | Titles at 20 and 24 px use **Inter Display** SemiBold, the display-optics cut of the same OFL family and the cut used in the wordmark. | Tighter, crisper titles, and the title type matches the logo. Bundling it adds one static TTF. |
| 5 | **D5** controls 32 | Icon buttons are 32×32 with a 20 px glyph. The status-line zoom buttons are 24×24, which is the GOAL floor. | They are a secondary control in a 28 px line. |
| 6 | Round-1 cut colours (QR blue, filtre plum, elle slate) | Dropped. The cut type is told by tab position, pictogram and edge style (solid, dashed, dotted), all in manila ink. | One signal per item (brief C10). The greyscale read gets better, because colour was never the carrier. D1 is untouched. |
| 7 | Brief: spine "directly under the band" | The spine sits under the command row, directly above the timeline. | Proximity: the spine describes the timeline, so it touches it. |
| 8 | Brief: thumbnails ≈ 150×212 | Default is **166×234** at 1366×768 (slider-adjustable). | Needed for gate 7 (≥ 60 % page pixels); 150×212 measured 54 %. |
| 9 | Skill `page-patterns`: no table in a split pane's left side | Değerler keeps a sortable table beside the crop. | Research 05 r6 (dual-pane validation, as in Rossum and ABBYY) wins over the skill. |
| 10 | Round 1: review circle on every row, key-hint line under the table | Değerler drops both. Review state is the filter (İncelenmemiş); "Tümü" adds an İnceleme column. Shortcuts live in the edit hint, tooltips, menus and the Shift+F1 sheet. | Brief C10 and C11, gate 6. |
| 11 | New key proposal | **F4** shows or hides the inspector (Görünüm menu). | Lightroom's Tab key conflicts with the keyboard model (Tab moves to the next value). F4 is unused in 07-qol §3. |
| 12 | Toast anchor | Toasts sit bottom-right *inside the right sheet, above its action footer*. | They never cover the table or the primary button. |
| 13 | Crop text size | The crop shows the scan at %200. Its 18 px is image scale, not UI type. | In Qt it is a rendered pixmap, not text. |

## 8. How each element is built in Qt (PySide6, Fusion base)

| Element | Construction |
|---|---|
| Window and band | Frameless `QMainWindow` with a custom 44 px title widget. Snap layouts and dragging come from `nativeEvent` handling `WM_NCHITTEST` (HTCAPTION on empty band, HTMAXBUTTON on the maximise button for Win11 snap flyout). Fallback: keep the native frame and set `DwmSetWindowAttribute(DWMWA_CAPTION_COLOR=35)` to `--shell`, with the tabs in a band directly under it. Band background comes from QSS `#Band { background: <shell>; }`. |
| Index tabs | `QTabBar` (document mode, not expanding) in the band. QSS: `QTabBar::tab { color: <on-shell-2>; padding: 0 16px; height: 36px; border-top-left-radius: 8px; border-top-right-radius: 8px; } :selected { background: <bg-base>; color: <text>; font-weight: 600; } :hover:!selected { background: <shell-hover>; }`. The inverted 8 px outer corners are painted in a `QTabBar` subclass `paintEvent` using `QPainterPath` (rect minus circle) filled with `<bg-base>`, or with two small cached pixmaps. Ctrl+1…6 and Ctrl+Tab are unchanged. |
| App menu and Alt | A `QToolButton` (icon `menu`, `InstantPopup`) whose `QMenu` holds the six `QMenu`s from the `actions.py` registry. An app-wide event filter on `Key_Alt` release pops it up. Alt+D/E/G/T/A/Y call `menu.popup()` for each menu. Underlines are hidden until Alt via the QProxyStyle `SH_UnderlineShortcut` = 0, and `QMenu` shows `&` mnemonics once opened from the keyboard. |
| Command search | A `QPushButton` styled as a field (`<shell-hover>` fill) that opens the Ctrl+K palette (`QDialog` + `QLineEdit` + `QListView`). |
| Command row | `QToolBar` on `<bg-base>`, `setIconSize(20)`. Actions use `ToolButtonIconOnly`, except the 2 labelled ones with `ToolButtonTextBesideIcon`. QSS: `QToolButton { border: none; border-radius: 4px; padding: 6px; } :hover { background: <bg-hover>; } :checked { background: <bg-pressed>; }`. The tooltip is `"{text}  {QKeySequence.toString(NativeText)}"`. Overflow goes to "⋯" through the existing command-bar overflow. |
| Spine | Custom `QWidget.paintEvent`: a rail (`drawRoundedRect` r=2), document ticks from `document_starts` (`drawLine`, manila-edge at 45 %), reviewed runs (3 px accent rects), kontrol flags (a 10×7 trapezoid `QPolygonF`, the logo tab, `--rider`), and the viewport (2 px `<text>` rounded rect). Click or drag scrolls the timeline. The legend is a `QLabel` with icon and word. Accessible name: "Tüm iş: 640 sayfa, 96 belge, 7 kontrol". |
| Timeline, stacks and pages | `QListView` (IconMode, custom layout per document row) with a `QStyledItemDelegate`. There are no widgets per page, which keeps 1,000 pages smooth. The delegate paints: tray (`<bg-selected>` rounded 4 when selected), the paper pixmap with a cached 9-patch shadow (research 06 r10), the page number, the folder edge (`QPen` 2 px manila-edge, `Qt.SolidLine`/`DashLine`/`DotLine`), the guide tab (path with 4 px top corners, manila fill and edge, Lucide pictogram pixmap and number), the rider (rounded 4, `--rider` fill, icon and "Kontrol"), and the check badge (circle and check). Focus is drawn by the shared focus painter around the tray. Thumbnail size is bound to the status-line slider and Ctrl+wheel. |
| Divider card (QR separator) | The same delegate, a 36 px slot: `<bg-well>` fill, 1 px stroke, QR icon, and `QPainter.rotate(-90)` text "Ayıraç". |
| Floating sheets (inspector, table, crop) | `QFrame#Sheet { background: <bg-layer>; border: 1px solid <stroke>; border-radius: 8px; }` inside a layout with 8 px margins on the desk. No shadow. In dark mode a 1 px top highlight is painted in `paintEvent` (`--edge-light`). The panels collapse with F4 (`QSplitter.setSizes` / hide). |
| Wells and facts | `QFrame.well { background: <bg-well>; border-radius: 4px; }` with a `QFormLayout` (13 px `text-2` labels, 15 px values), and no hairlines. |
| Boundary preview | Two cached thumbnail pixmaps plus a painted dashed line and mini guide tab in a small `QWidget`. |
| Buttons | Primary: `QPushButton[primary="true"] { background: <accent>; color: <on-accent>; border: none; border-radius: 4px; min-height: 40px; font-weight: 600; }`, with the shortcut as a second right-aligned `QLabel` at 13 px (opacity through palette, not QSS). Standard: `background: <bg-popover>; border: 1px solid <stroke>; border-bottom-color: <stroke-strong>`. Subtle: no border; hover fill. |
| Inputs | `QLineEdit, QComboBox { background: <bg-popover>; border: 1px solid <stroke-strong>; border-bottom: 1px solid <edge>; border-radius: 4px; } :focus { border-bottom: 2px solid <accent>; }` (per-side QSS colours are supported). |
| Segmented filter | `QButtonGroup` of checkable `QToolButton`s in a `QFrame.seg`. `:checked` gets the popover fill and a stroke. The counts are a second run of text in `text-2`, painted by a small delegate or rich-text label. |
| Values table | `QTableView` + `QStyledItemDelegate`. 40 px rows (D5), a `QHeaderView` 36 px tall with 13 px semibold. Hairlines are painted per row (`<stroke>`), not grid lines. The current row is `<bg-selected>` with a 3 px `<select-ring>` inset at the left. Uncertain characters are painted per glyph: `QFontMetricsF.horizontalAdvance` gives the run offsets, and the delegate draws a `<check-wash>` rect plus a 2 px `<rider-edge>` underline under each uncertain index. Tabular figures come from `QFont.setFeature("tnum", 1)` (Qt 6.7+; with no QSS font-features, set it in code), plus "cv05"/"cv08", and "zero" on the editor and comparison only. |
| Inline edit | `QStyledItemDelegate.createEditor` returns a `QLineEdit` with the same geometry as the cell (`updateEditorGeometry` = option.rect inset 4), so nothing moves. The hint is a non-activating `QFrame` popup (Qt.ToolTip flags) under the cell, shown while the editor has focus. |
| Crop and comparison | The crop is a `QGraphicsView` (zoom: Ctrl+wheel, buttons, %), with a matte in `<bg-base>`, the page pixmap and a `QGraphicsRectItem` ring (2 px select-ring, radius 4). The comparison is two `QLabel`s with rich text spans (`<span style="background:…">` resolved from tokens) at 24 px, or a painted widget. |
| Status words | A delegate or `QLabel` with a 16 px Lucide pixmap, the word and a `text-2` %. Colours come from tokens. |
| Context menu and menus | `QMenu` with QSS `QMenu { background: <bg-popover>; border: 1px solid <stroke>; border-radius: 8px; padding: 4px; } QMenu::item { height: 32px; padding: 0 24px 0 10px; border-radius: 4px; } QMenu::item:selected { background: <bg-hover>; } QMenu::separator { height: 1px; background: <stroke>; margin: 4px 0; }`. The rounded shape needs `setAttribute(WA_TranslucentBackground)` + `FramelessWindowHint`, and the soft shadow is a cached 9-patch painted in a `QMenu` subclass (one level, `--shadow-pop`). Shortcuts are right-aligned by Qt. |
| Toast | A child `QFrame` (rounded 8, popover fill, 9-patch shadow) anchored above the sheet footer. It fades in or out over 180 ms with `QPropertyAnimation` on a `QGraphicsOpacityEffect`, and the duration is 0 with reduced motion. "Geri al" triggers `undoStack.undo()`. |
| Focus ring (D11) | A QProxyStyle `drawPrimitive(PE_FrameFocusRect)` plus a focus overlay widget. It paints a 1 px `<focus-inner>` and a 2 px `<focus-outer>` rounded rect outside the widget or tray; it uses `<focus-on-shell>` when the parent is the band. |
| Icons | Lucide SVGs rendered by `QSvgRenderer` into pixmaps per size × DPR × colour token, cached and flushed on `themeChanged`. |
| Themes | `ThemeManager` generates the `QPalette` and the QSS from the DTCG token JSON. Light and dark come from this file; HC uses the OS palette (D9) and drops the band colour to `Highlight`/`Window`. |

## 9. Not done in this round (honest list)

- High-contrast and 150 % text renders were not produced for C. The tokens and layout are ready for
  them: the band falls back to the OS palette, and at 150 % the inspector scrolls and the thumbnails
  shrink through the slider. Both should be rendered before Phase 2 if C is chosen.
- Only Kontrol and Değerler were mocked, as the brief asked. The quiet tabs (Yükle, Dışa Aktar) would
  use the same band, desk and sheets, with one sheet centred at max 960 px wide.
- The loupe (Space), the empty states and the drag overlay are specified in the text above and in
  round 1. They were not re-rendered in C.
