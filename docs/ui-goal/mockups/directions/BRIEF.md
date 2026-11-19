# Round 2 direction brief: why round 1 reads as "an old office program", and three ways out

Input: the owner's rejection of round 1 ("it still looks like an old, bad office program"; "the
skills are not used well enough"), every PNG in `../png/`, `../tokens.css`, `../shell.css`,
`../README.md`, `../REVIEW.md`, PRODUCT.md, GOAL.md, decisions.md (incl. "Owner answers after
mockup round 1"), research 03, 05, 06 and 07, and the logo kit.

Lenses used (loaded and applied): `ui-design-review:ui-review` (hierarchy, consistency, generic
look, platform), `ui-design-review:ui-compare` (UXKIN does not connect here, so the comparison uses
published platform conventions and the named apps as I know them; numbers marked ≈ are observed or
approximate, not verified against a spec), `vectorlab-ux-skills:anti-slop` (decoration vs.
structure), `vectorlab-ux-skills:ux-audit` (hard gate 10 "visual finish", 60-30-10),
`frontend-design:frontend-design` (one bold thing, no template chrome, middle-dot strings and
labels-above-everything as tells), `design:design-critique` (first impression, reading order).

This is a diagnosis, not a redesign. Nothing about behaviour, vocabulary or the keyboard model is
reopened here (see §3).

---

## 0. The two-second read (design-critique, first impression)

At 1366×768 the first thing the eye lands on in every tab is **the chrome, not the work**: the
menu-bar row, the text tab row and the 8–12-label command row stack up into a grey header that
looks like Word 2010 with the ribbon collapsed. Below it, three equal grey panes divided by
hairlines, filled with outlined rectangles, small bold headings and orange chips. Nothing is
large, nothing is quiet, nothing is lifted. The screens are *correct* (contrast, states, keys all
work) but they have no depth, no rhythm and no hero. "Calm" was implemented as "grey"; "Office" was
implemented as "Office's chrome" instead of "Microsoft 365's 2024–26 restraint".

ux-audit gate 10 (visual finish): **fail** on every tab. Primary content (the pages in Kontrol,
the values in Değerler) carries no more visual weight than the toolbar labels; 60-30-10 is roughly
85 % grey chrome/panels, 10 % white content, 5 % split between green and orange, with the orange
spread over many small marks.

---

## 1. Why it reads as an old Office program (15 measured causes)

Measurements are from the 1366×768 PNGs and the round-1 tokens (`--titlebar-h` 32,
`--tabstrip-h` 40, `--commandbar-h` 48, `--statusbar-h` 32, `--inspector-w` 320).

| # | Cause | Where, and the number |
|---|---|---|
| C1 | **Five stacked full-width bands of chrome.** Title+menu, tab strip, command bar, (Kontrol: overview strip), status bar, each a full-width band ruled off by a hairline. | 32 + 40 + 48 + 32 = **152 px (20 % of 768)** of chrome on every tab; on Kontrol the overview adds ≈ 96 px → **≈ 248 px (32 %)** before a single page. The Office 2010 silhouette is exactly "stacked horizontal strata". |
| C2 | **A permanent text menu bar with underlined access keys** in the title bar. | All tabs: "Dosya Düzen Görünüm Git Araçlar Yardım" with the mnemonics underlined at rest. Windows has hidden mnemonic underlines until Alt is pressed since Windows 2000; showing them always is the single most "old Win32" signal on the screen. |
| C3 | **Text tab strip in its own row, underline indicator.** | 40 px row with 6 text tabs at 15 px + 3 px green underline, separate from the title bar. Reads as Office 2013 ribbon tabs with the ribbon removed. |
| C4 | **Command bar = a row of 8–12 icon+label buttons at body size, equal weight.** | Kontrol: Geri, İleri, Kes, Birleştir, Döndür, Sil, Şablon uygula, Filtre uygula, Sonraki kontrol, Sonraki incelenmemiş, Git…, Önizle = 12 commands, 10 labelled, all 15 px medium, spread across 1366 px. Değerler 9, Dışa Aktar 7, Şablonlar 6. Labels are the same size as content text, so the toolbar competes with the work. This *is* a ribbon. |
| C5 | **No surface hierarchy.** Three greys 2–4 % apart (`--bg-chrome #e9ecea`, `--bg-layer #f9faf9`, `--bg-canvas #eff2f0`), no radius on any pane, no inset content layer; panes are separated only by 1 px splitters running edge to edge. | Every tab. In dark, `#191d1b / #222825 / #1c211e` are within ≈ 3 % L of each other: the dark screens read as one muddy sheet (`kontrol-dark.png`, `disa-aktar-running-dark.png`). |
| C6 | **Dark 3:1 outlines on every secondary control.** `--edge #7a867f` was applied to buttons, selects, inputs and segmented controls alike. | Kontrol inspector: 3 stacked full-width outlined buttons; Değerler: search, 3-segment filter, 2 selects, 2 outline buttons; Dışa Aktar: Klasör seç, input, Değişken ekle, select. Grey-boxed buttons are the Windows 95–Office 2010 button. WCAG 1.4.11 does not require a boundary on a button whose text identifies it; the 3:1 rule was over-applied (it is needed on inputs, focus and state, not on every button). |
| C7 | **Three equal columns on every tab.** List (≈ 336 px) │ work │ inspector (320 px) with hard splitters. | Yükle, Şablonlar, Rehber, Dışa Aktar and (with the inspector) Kontrol and Değerler all share one skeleton. No tab has its own shape, so the app feels like one property sheet with six names. |
| C8 | **The inspector is a property grid.** Section, hairline, 17 px bold heading, key/value list, stacked full-width buttons, hairline, repeat. | Kontrol inspector: 2 headed sections + 3 stacked buttons + a form with 2 inputs and 2 buttons; Yükle "İş özeti": 3 headed sections. Looks like Visual Studio's Properties window. |
| C9 | **Heading inflation and no anchor.** Every pane and section gets a bold 17–20 px heading; the one thing the user is working on is never bigger than its labels. | Yükle has 6 bold headings on screen (İşler, Partiler, İş özeti, Ön kontrol, Tarama profili, + tab name); Dışa Aktar 6 (Ön kontrol, Dosya adları, Hedef klasör, Dosya adı kalıbı, Seçenekler + tab). Values in Değerler are 15 px, the same as the toolbar. |
| C10 | **Badge and marker clutter; orange spread thin.** Orange is correctly reserved for kontrol, but it is repeated in 3 forms per item (filled chip + 3 px inset bar + orange reason text) and joined by triangles in cells, underlined letters, dotted circles and coloured cut icons. | Dışa Aktar (light): 4 rows × 3 orange marks + status = **13 orange marks** in one viewport. Değerler: up to 3 triangles per row + `%58` chips + dashed review circle at every row start (11 dotted circles). Kontrol: around each document 6 marker kinds (guide tab, manila rule, coloured dashed cut line, round cut badge, review circle, Kontrol chip). |
| C11 | **Keycaps everywhere.** Boxed `Ctrl+F`, `Enter`, `Ctrl+2`, `Ctrl+S`, `Ctrl+E`, `Ctrl+P`, `F3`, with a 2 px bottom border. | Search fields, every primary button, Rehber nav rows, the Değerler key-hint line (6 keycaps), tooltips. Keycaps on the primary read as a developer tool or a 2005 kiosk, not as an office app. |
| C12 | **Small, decorated thumbnails; documents are not the hero.** | Kontrol grid thumbnails ≈ 96 × 136 px in a ≈ 1020 px work area, with ≈ 40 % of the area spent on markers, labels and gaps. The loupe filmstrip pages are ≈ 44 × 62 px. In Lightroom/Photos the image is the largest thing on screen; here the toolbar text is. |
| C13 | **Middle-dot meta strings and labels on everything.** | "640 sayfa · 96 belge", "Belge 16 · Ekspertiz Raporu · Sayfa 72", "%60 · yaklaşık 2 dk kaldı", "Sayfa 72–74 · Belge 16 ve 17" on almost every heading. frontend-design names "A · B · C" meta strings as template chrome; in volume they read as dense legacy status text. |
| C14 | **Web-2012 widgets: dashed drop zones and dashed placeholders.** | Yükle: a 656 × 64 px dashed "PDF'leri buraya bırakın" box permanently on screen; Kontrol empty: a dashed "Tüm iş" box; Yükle empty: dashed drop zone + numbered 1/2/3 steps (frontend-design: numbering is only for real sequences; here it is, but the boxed numerals are template chrome). |
| C15 | **An Office-2010 status bar.** Full-width 32 px band with 4–5 facts, each with an icon, plus a zoom slider and "%100". | Every tab. The status bar duplicates information already on screen (kontrol count, belge n/96) at body-adjacent size, adding a sixth band of things to read. |

Secondary observations (not causes on their own, but they compound):
- **Mixed fonts in data**: file names switch to a monospace in Dışa Aktar while the rest is Inter.
- **Dark primary is pastel** (`--accent #9fc5ae` with dark text): correct for contrast, but on a
  muddy base it looks washed out rather than lit.
- **Spacing has no big steps**: no gap larger than 24 px appears anywhere inside a work screen, so
  groups never separate; every block sits 8–16 px from the next (vectorlab `spacing`: density with
  air means tight rows *and* generous group gaps).
- **One radius for everything** (4 px on buttons, chips, rows, inputs, guide tabs, riders): the
  frontend-design "one border-radius on everything regardless of hierarchy" tell.

---

## 2. What modern desktop apps do instead (per cause, with Qt translation)

Numbers marked ≈ are observed/approximate; WinUI values come from research 03 (verified there).

| # | Modern pattern (who does it, numbers) | How in Qt (QSS / QPalette / QPainter, no blur) |
|---|---|---|
| C1 | **Collapse chrome into one or two bands.** Windows 11 File Explorer puts tabs *in* the title bar (≈ 40–48 px), then one command bar (≈ 48 px), and content. New Outlook: one title/search band (≈ 48 px), one simplified-ribbon line (≈ 40 px), then content; no status bar. Linear/Things/Photos: one ≈ 40–52 px unified title/toolbar and nothing else. **Target: ≤ 96 px of horizontal chrome total, ≤ 120 px on Kontrol including the overview.** | Frameless `QMainWindow` with a custom title widget (tabs or search in it) and native snap via `WM_NCHITTEST` handling, or keep the native frame and colour the caption with `DWMWA_CAPTION_COLOR` (35) so title + tab row read as one surface. Overview strip moves into the command-bar band or becomes a 24–32 px scrubber. |
| C2 | **No resting menu bar.** Explorer, Settings, Outlook, Teams, Photos: none. Win11 Notepad/Paint keep a compact menu but mnemonic underlines show only after Alt. Figma and Linear put the whole menu behind one app-menu button and Ctrl+K. | Keep every QMenu and access key (GOAL 3.1), but (a) render no underlines until Alt (Qt does this natively with `QStyle::SH_UnderlineShortcut` = 0 on Windows style; set it in the QProxyStyle), and (b) either hide the `QMenuBar` and show it on Alt (event filter on `QEvent.KeyPress` Key_Alt → `menuBar().setVisible(True)`), or show one "≡" `QToolButton` in the title bar with `InstantPopup` holding the six menus, plus Alt+D/E/G/T/A/Y shortcuts that `popup()` each menu. Ctrl+K palette stays. **Owner decision**: GOAL 3.1 says "a menu bar"; this keeps all menus and keys but not the resting row. |
| C3 | **Tabs in the title bar** (Explorer, Edge, Terminal: TabView ≈ 32 px tabs, 8 px top corners, selected tab = base-colour fill joined to the content below, no underline) **or a left navigation rail/sidebar** (Settings: NavigationView pane ≈ 280–320 px, 36–40 px items, 3 × 16 px accent pill on the selected item; Outlook rail ≈ 48 px icons+labels). | `QTabBar` styled with `QTabBar::tab:selected { background: <layer>; border-top-left-radius: 8px; border-top-right-radius: 8px; }` inside the custom title widget; or a `QListView` sidebar with a delegate painting the 3 × 16 px pill (`QPainter.drawRoundedRect` r = 1.5). Ctrl+1…6 unchanged. |
| C4 | **Icon-first command bars, 1–3 labelled verbs.** Explorer: "New" + "Sort" + "View" labelled, cut/copy/paste/rename/share/delete as 32 × 32 icon buttons with 16 px glyphs and tooltips. Outlook Simplified ribbon: ≈ 5 labelled, rest icons, overflow "…". Photos/Preview: 6–8 icons, no labels. Linear: contextual bar appears only when something is selected. **Target: ≤ 3 labels per bar; icons 20 px in 32–36 px hit areas; labels 13–14 px, never the size of content.** | `QToolButton` with `ToolButtonIconOnly`, `autoRaise`, QSS `border: none; border-radius: 4px; padding: 6px;` hover fill = 6 % ink over layer, pressed 10 %. Tooltip shows "Kes  K" (shortcut as muted text). Selection-only commands live in a contextual bar or in the inspector (Carbon/Paperless pattern, research 03 §2 #7). |
| C5 | **Two or three real layers.** Windows 11: Mica base `#F3F3F3` (dark `#202020`), content layer near-white `#FBFBFB`/`#FFFFFF` (dark `#282828`–`#2C2C2C`) with a 1 px stroke ≈ `#0F000000` and an 8 px top-left radius where it meets the nav (Explorer, Settings ≈). Outlook/Teams 2.0: the reading pane and list are rounded "cards" (≈ 6–8 px) floating on a tinted base with ≈ 4–8 px gutters. Linear: inset main panel with ≈ 6–8 px radius and 1 px border on a darker sidebar base. **Target: base vs. layer ≥ 5–6 % L difference in light, ≥ 4 % in dark (research 06 r11: dark page L 0.18 / panel 0.22 / raised 0.26).** | Base = `QMainWindow` palette `Window`; content layer = `QFrame#layer { background: <layer>; border: 1px solid <stroke>; border-top-left-radius: 8px; }` with 0 margin on the right/bottom edges and 4–8 px on the side facing the nav. Flat fills only; the one shadow level (flyouts) stays a cached 9-patch (research 06 r10). Needs **D6 extended**: 8 px allowed on content layers (currently "dialogs, menus, popovers"). |
| C6 | **Filled-subtle controls, strokes only where they identify.** Fluent standard button: fill `#FBFBFB` on light layer, stroke `#0F000000` plus a slightly darker bottom stroke (elevation border), radius 4, 32 px; subtle/ghost buttons have no stroke at rest. Fluent TextBox: faint stroke on 3 sides, **≥ 3:1 bottom stroke** that becomes a 2 px accent line on focus. Linear/Things: secondary actions are text or ghost buttons. | QSS: `QPushButton { background: <control-fill>; border: 1px solid <stroke-subtle>; border-bottom-color: <stroke-elev>; border-radius: 4px; }` (QSS supports per-side colours). `QLineEdit { border: 1px solid <stroke-subtle>; border-bottom: 1px solid <stroke-strong-3to1>; }` and `:focus { border-bottom: 2px solid <accent>; }`. D10's 3:1 edge rule stays for inputs, checkboxes, focus and selection; buttons rely on fill + label. Note the change in the contrast test. |
| C7 | **Each screen has its own shape.** Outlook: list + reading pane; Settings: nav + single centred column (max ≈ 1000 px); Lightroom Library: grid + filmstrip with collapsible side panels (Tab hides them, Shift+Tab hides all); Photos: content full-bleed, inspector on demand (Cmd+I). | Per tab `QSplitter` presets with collapsible panes (`setCollapsible`, a Görünüm toggle and F9-style key per side panel); inspector default **closed** on Yükle and Rehber, **open** on Değerler. Widths remembered in QSettings (already in GOAL). |
| C8 | **Inspector as grouped cards, one action.** Windows Settings: SettingsCard groups (cards ≈ 4 px radius, ≈ 16 px padding, ≈ 2–4 px between cards in a group, ≈ 24–32 px between groups, group header 14 px semibold). Linear issue sidebar: label/value rows without dividers, 13 px, values clickable inline. Figma UI3: properties in sections with no hairlines between rows, section titles 11–12 px semibold. | Inspector = `QScrollArea` of `QFrame.card` (layer-2 fill, 1 px stroke, radius 4) with `QFormLayout` inside; no full-width hairlines. One filled primary at the bottom; other actions as subtle buttons or a single "⋯" menu. |
| C9 | **One typographic anchor per screen.** Settings: page title 28/36 semibold, everything else 14/20. Things: list title ≈ 26–28 bold, rows ≈ 14–15 regular, no section heading heavier than 13 semibold. Linear: 13 px UI, one 20–24 px title in the issue view. **Rule: one large title (24 or 28), section labels drop to 13–15 semibold in text-2, and the working value (page, OCR value) is the biggest or boldest thing in its area.** | Keep D4 (body 15 floor for older users). Use `page 24/32` once per screen; demote pane titles from 20 to 15 semibold; Değerler value field and "Okunan / Öneri" at 20–24 mono-tabular. Pure QFont work. |
| C10 | **One signal per item.** Outlook: one flag icon per message; Linear: one status glyph per row in a fixed column; Lightroom: one flag badge per thumbnail corner. Colour is concentrated, not repeated. **Rule: one orange mark per item (the rider), reason text in normal ink; per-character tint stays only inside the value being edited.** | Delegate paints the rider once (icon + "Kontrol"), reason in `text-2`. Remove the inset bar or the chip (keep one). Review state as a 16 px glyph only on hover/selected, or in its own sortable column, not as a dotted circle on every row. |
| C11 | **Shortcuts as quiet text, not boxes.** Windows 11 context menus and Figma/Linear menus right-align the shortcut in text-2, no box. Linear shows keycaps only inside tooltips and the Ctrl+K palette. Explorer search shows no keycap. | `QMenu` already right-aligns shortcuts. Tooltips: "Belgeyi onayla" + muted "Enter". Keep keycaps only in the shortcut sheet (Shift+F1) and the Ctrl+K palette; drop them from primaries, search fields and nav rows. Optional first-run TeachingTip (research 03) for the 3 key shortcuts. |
| C12 | **Content is the hero.** Lightroom Library grid: thumbnails user-sized ≈ 120–320 px, cells with minimal chrome (badges only on hover, "Show extras" toggle), filmstrip ≈ 80–100 px tall; loupe surround selectable (black / dark grey / medium grey / white). Photos/Preview: thumbnails ≈ 150–200 px, selection = 2–3 px accent ring + check. **Target on Kontrol at 1366: default thumbnail ≥ 132 × 186 px, ≥ 60 % of the work area is page pixels, markers ≤ 2 per document at rest.** | `QListView` IconMode + delegate (research 05): page sheet radius 2 + 1-step shadow from cached pixmap; document gap 24 px vs. page gap 6 px so grouping is spatial, not drawn; guide tab stays the one signature; other markers on hover/selection (`QStyle.State_MouseOver`). Status-bar slider drives size (owner answer). |
| C13 | **Meta as structure, not strings.** Outlook/Linear put metadata in columns or on its own muted line; titles carry one fact. | Split "A · B · C" into a title + a single `text-2` line, or into aligned columns; cap at two facts per line. |
| C14 | **Drop targets appear only while dragging.** Figma, Photos, Outlook attachments: the whole window shows a tinted overlay on `dragEnter`; at rest, no dashed box. Empty states: one icon, one sentence, one primary (anti-slop, empty-states). | `dragEnterEvent` shows a full-window `QWidget` overlay (accent at 8 % + 2 px accent inset border, radius 8); hide on leave/drop. Remove resting dashed boxes. |
| C15 | **Status bars are thin or gone.** Explorer: ≈ 24–28 px, 12 px text ("640 öğe · 3 seçili"), no icons, view toggles at right. Outlook/Linear/Things: none; progress lives where the work is. | 28 px status, 13 px text-2, no icons except the kontrol count (it is the "never silent" anchor); zoom becomes a compact slider without "%" label, or moves to the command bar's right end. |

---

## 3. Keep (every direction must carry these over unchanged)

Round 1 did the hard, invisible work well. The owner rejected the *look*, not this.

- **Keyboard model**: the full shortcut map (07-qol §3) with the Turkish-Q fixes in `../README.md`
  (Shift+F1 sheet, Ctrl+. to stop, Ctrl+G go-to everywhere, Esc only dismisses, F6 regions, Tab
  leaves the table); the owner-confirmed Kontrol keys (N / Shift+N, U, Enter = Belgeyi onayla,
  Space loupe, Esc back); Ctrl+1…6, Ctrl+K palette, Alt access keys (ASCII, never I).
- **Vocabulary**: Emin / Orta / Kontrol / Okunamadı; İncelendi / İncelenmedi; "Sonraki kontrol",
  "Kontrol gerekenler"; "Onayla" on buttons; verb-first labels; Turkish only; "Şüpheli" retired.
- **Status = icon + word + colour**, orange only for kontrol, and the hue-distance check
  (`_contrast.py`, ≥ 30° from `--rider`).
- **Cut-type encoding by position + pictogram + line style**, with the greyscale proof
  (`kontrol-cuts-gray-*.png`), QR / filtre / elle never orange or red.
- **Contrast proof**: `_contrast.py` per theme incl. HC, D10 thresholds (body ≥ 7:1, secondary ≥ 4.5:1,
  inputs/focus/state ≥ 3:1), and the 150 % text renders with the clipping check. The only change:
  buttons identified by their label are exempt from the 3:1 *border* rule (C6).
- **States designed for every tab**: empty, running, blocked, done, drop, reorder, loupe, örnek,
  all-values, HC; toasts bottom-right with Geri al; one filled primary per view.
- **Features**: overview of the whole job with viewport, loupe with filmstrip, dual-pane Değerler
  with linked crop and per-character uncertainty, Örnek kontrol before export, graded pre-flight
  (Tamam / Uyarı / Bilgi), file-name preview with collision marks, undoable delete (no confirm),
  context menus with shortcuts, save state in the title area, command-bar overflow to "⋯".
- **Tokens as the single source** (DTCG → QPalette + QSS), D3 Inter, D4 type floor (13 px, body 15),
  D5 densities, D7 motion, D8 Lucide, D11 focus ring. Directions change *values and composition*,
  not this architecture.
- **The filing-cabinet signature** (manila guide tab at the document start, orange rider) as the one
  memorable element, used where documents are shown.

---

## 4. Three directions for the designers

All three: Qt-buildable (QSS + QPalette + QPainter; no blur; flat tonal layers; 1 px strokes; one
shadow level for flyouts/dialogs/toasts); keep §3; meet the round-2 gates in §5. They differ in
**chrome model, surface model, colour temperature and where the brand lives.**

### A. "Fluent 2 Mica" — a native Windows 11 / Microsoft 365 app

**Concept.** Evrakçı looks like it shipped with Windows 11 24H2 next to File Explorer and new
Outlook: a soft Mica-toned base, tabs living in the title bar, one compact icon-first command bar,
and the work on a bright, rounded content layer that floats a step above the base. Calm comes from
the platform's own restraint; users already trust it because it looks like Settings and Explorer.
Cabinet green replaces Windows blue as the system accent, nothing more.

- **References:** Windows 11 File Explorer (tabs in title bar, command bar, details pane),
  Windows 11 Settings (cards, nav pills), new Outlook (simplified ribbon, rounded panes), Microsoft
  Loop (quiet canvas, one title), Notepad/Paint 11 (compact menus with Alt reveal).
- **Surface model (light / dark):** base `≈ #F2F3F2 / #202221` (Mica fallback, slight green tint
  ≤ 0.01 chroma); content layer `#FBFBFB / #2A2C2B` with 1 px stroke `rgba(0,0,0,.06) / rgba(255,255,255,.07)`
  and an 8 px top-left radius; cards in inspectors `#FFFFFF / #303231`, radius 4; flyouts 8 px with
  the single shadow. Real Mica via DWM where available (research 03), solid fallback otherwise;
  never behind thumbnails or tables.
- **Density:** Fluent standard: controls 32, rows 40 (Normal), command bar 48, icons 16/20.
- **Chrome:** title bar 44 px holding app icon, **tabs as TabView tabs** (Yükle … Rehber), the job
  name as the title, save state and the "≡" menu button at right before caption buttons; menus
  reachable by Alt (menu row appears on Alt, underlines only then). Command bar 48 px, icon-only
  except the 1–3 core verbs per tab (Kontrol: "Kes", "Sonraki kontrol"; Değerler: "Değerleri oku",
  "Sonraki kontrol"). Status bar 28 px, Explorer style. Inspector a collapsible right pane of
  Settings-style cards.
- **Brand:** green = accent only (selected tab text + 3 × 16 px pill in nav, primary fill, focus,
  selection ring, slider). Manila = guide tabs and the document-start page edge in Kontrol only.
  Orange = rider only. The logo sits 16 px in the title bar.
- **Risk:** "generic Windows app": correct but forgettable, and dated the day Microsoft changes
  Fluent again. Mitigate by letting the Kontrol timeline (manila guide tabs on a clean layer) be
  the one unmistakable Evrakçı screen. Technical risk: a custom title bar must keep Windows snap
  layouts and accessibility (needs `WM_NCHITTEST` handling, or the DWM caption-colour route).

### B. "Quiet workspace" — Linear / Things-level restraint

**Concept.** A focused, almost silent tool: a slim left sidebar replaces the tab strip, the job is
always visible as the "project", and the main area is one large inset panel where the current task
gets generous space and a single big title. Toolbars are small, icon-only, and contextual: commands
appear when something is selected; everything else is a keypress or Ctrl+K away. It feels like a
calm, expensive notebook rather than an application window.

- **References:** Linear desktop (sidebar, inset main panel, contextual actions, Ctrl+K, 13–15 px
  type), Things 3 (whitespace, one title per list, no dividers), Arc (sidebar-as-navigation, content
  framed), Apple Preview/Photos (icon toolbar in the title area, sidebar thumbnails).
- **Surface model:** two layers only. Sidebar/base `≈ #EEF0EE / #1A1C1B`; main panel `#FCFCFB /
  #222423`, inset 8 px from the window edges on the top, right and bottom, 8 px radius, 1 px stroke
  `rgba(0,0,0,.07) / rgba(255,255,255,.06)`. No hairlines inside the panel; grouping by space
  (24–32 px between groups, 4–8 px within). Inspector, when open, is a 300 px column *inside* the
  panel separated by space and a faint 1 px rule, not a third pane.
- **Density:** airy at rest, dense where it counts: rows 40 (Değerler table 36 option), controls
  32, icon buttons 28–32 with 16 px glyphs, page title 24, section labels 13 semibold text-2. Body
  15 (D4) unchanged.
- **Chrome:** native or minimal 36 px title bar carrying only job name, save state and the "≡" menu
  button (full menus inside; Alt+letter opens each). **Left sidebar 216–240 px**: logo + job switcher
  at top, then the six stations as rows (icon 20 + label 15, 36 px, selected = layer fill + green
  3 px pill), each with a live count (Kontrol 7, Değerler 12); collapsible to a 52 px rail (Ctrl+B
  or a Görünüm toggle). **Command bar inside the panel header**: page title left, ≤ 5 icon buttons +
  1 labelled primary verb right; selection swaps in a contextual bar. No status bar: the counts live
  in the sidebar and the panel header; zoom is a small control in the panel's bottom-right.
- **Brand:** quietest of the three. Green on the selected-station pill, primary button and focus;
  the sidebar logo carries manila + orange at 20 px. Manila guide tabs in Kontrol; orange rider only
  for kontrol. The rest is neutral, warm-grey ink.
- **Risk:** furthest from what office staff expect from a Windows tool, and furthest from GOAL D2
  ("command bar per tab", "menu bar"): needs the owner's explicit OK to trade the tab strip for a
  sidebar and the resting menu bar for "≡" + Alt. Hidden commands can hurt discoverability for
  older users (research 05: Microsoft reversed hiding the Quick Access Toolbar), so every hidden
  command must be in the "≡" menu, the context menu and Ctrl+K, and the contextual bar must never
  be the only path. Also: whitespace eats 1366×768 quickly; Değerler must still show ≥ 11 rows.

### C. "Kartotek warm" — brand-forward, documents as the hero

**Concept.** Go back to DESIGN.md's original idea and make it beautiful: the window is a filing
cabinet. Cabinet-green chrome frames a warm paper workspace; the documents themselves, large and
crisp, are the brightest thing on screen, and manila and orange are the only other colours. In
dark mode it becomes a Lightroom-style darkroom: deep green-black chrome, a neutral grey surround,
and white pages that glow. It is the most "Evrakçı" of the three, and the one nobody will mistake
for Office.

- **References:** Lightroom Classic Library/Loupe (dark workspace, filmstrip, panels that hide with
  Tab, user-chosen surround), Figma desktop UI3 (dark chrome, content canvas centre stage, floating
  rounded panels), Apple Photos (content full-bleed, minimal overlays), the Evrakçı logo itself
  (`horizontal-on-green`: manila on cabinet green).
- **Surface model:** **chrome band = cabinet green** `#3f5a4c` in light (title + tabs as one 44 px
  band, white/`on-shell-2 #cddbd2` text, selected tab = warm paper tab joined to the workspace below,
  like a guide tab), `#1d2a23` (logo ink) in dark. **Workspace = warm paper** `≈ #F4F2EC` light /
  neutral `#2B2D2C` dark (Lightroom-style, untinted so scans read true, research 06 r3). Side panels
  float as rounded 8 px layers `#FBFAF7 / #333634` with 8 px gutters to the chrome, collapsible
  (Tab hides side panels, Shift+Tab hides everything but pages, as in Lightroom). Page sheets white
  with radius 2 and the one soft shadow (cached). Loupe surround user-selectable: paper / grey / dark.
- **Density:** content-first: chrome is one 44 px band + a 44 px icon command row on the workspace
  (no separate band colour), thumbnails default ≈ 150 × 212 px at 1366, filmstrip 96 px, rows 40,
  controls 32.
- **Chrome:** green title+tab band (tabs as manila-edged index tabs: selected tab is the paper colour
  and visually "pulls out" of the cabinet, the brand's guide-tab idea used for navigation). Menus via
  the "≡" button in the band and Alt (underlines only after Alt). Command row icon-only on the paper
  with 1–2 labelled verbs; overview strip in Kontrol becomes a thin (≤ 28 px) document "spine" with
  manila ticks and orange riders, directly under the band. Status: 28 px, paper-coloured, text-2.
- **Brand:** loudest of the three, but each colour still has one job: green = the cabinet (chrome)
  and the primary action; manila = paper accents (selected tab, guide tabs, document starts);
  orange = rider/kontrol only; neutral grey = surround for scans. Note: if green is the chrome, the
  primary button cannot also look like chrome; use a manila-ink/green outline on chrome and the
  solid green fill only on the paper workspace, and keep selection/focus in a distinct darker green
  or ink so "selected" never blends into the band.
- **Risk:** strong colour on 20 % of the screen for an hour-long session can tire the eye and
  fight D2's "quiet surfaces"; the warm paper sits close to the "cream + serif" AI tell (keep it
  low-chroma, Inter only, no serif). The green chrome must pass D10 for every label on it (white on
  `#3f5a4c` ≈ 7.5:1, OK; `#cddbd2` on it needs checking) and has to work in High Contrast (falls back
  to the OS palette, losing the brand, which is fine). Most custom painting of the three (tabs,
  spine), so most Phase-2 cost.

### How they differ at a glance

| | A Fluent 2 Mica | B Quiet workspace | C Kartotek warm |
|---|---|---|---|
| Navigation | Tabs in title bar | Left sidebar (rail-collapsible) | Index tabs in a green band |
| Menus | Alt-reveal + "≡" | "≡" + Alt + Ctrl+K | "≡" + Alt |
| Command bar | One 48 px band, icon-first | Inside the panel header, contextual | Icon row on the paper, no band |
| Surfaces | Mica base + rounded content layer + cards | Base + one inset 8 px panel, no inner rules | Green chrome + warm paper + floating panels |
| Status bar | 28 px, Explorer | None (counts in sidebar) | 28 px, paper |
| Brand intensity | Low (accent) | Lowest | High (chrome) |
| Dark mode | Windows 11 dark | Linear-like near-black | Lightroom darkroom |
| Horizontal chrome | ≈ 44 + 48 + 28 = 120 | ≈ 36 (+ panel header 52 inside) | ≈ 44 + 44 + 28 = 116 |
| GOAL/decision changes needed | D6 (8 px on layers), resting menu bar → Alt | D2 (sidebar, contextual bar), menu bar → "≡", status bar removed, D6 | D6, D2 "quiet surfaces" reinterpreted, menu bar → Alt |

---

## 5. Round-2 gates (measurable, so "modern" is not a matter of taste)

Every direction renders at least Kontrol, Değerler and one quiet tab (Yükle or Dışa Aktar) at
1366×768, light and dark, plus Kontrol at 150 % text, and must pass:

1. Horizontal chrome ≤ 120 px (Kontrol incl. overview ≤ 150 px); round 1: 152 / 248.
2. No resting menu row and no mnemonic underlines until Alt; every menu still reachable by Alt+letter.
3. Command bars: ≤ 3 text labels each; icon buttons 28–36 px with tooltips naming the shortcut.
4. Two or more visibly distinct surface levels (ΔL ≥ 5 % light, ≥ 4 % dark) and at least one
   rounded content layer; no full-width hairline inside a content layer except table header and rows.
5. Exactly one element per screen at the page-title size; pane titles ≤ 15 px semibold.
6. One orange mark per kontrol item; no keycaps outside the shortcut sheet, the palette and tooltips.
7. Kontrol: ≥ 60 % of the work area is page pixels at default zoom; thumbnails ≥ 132 px wide.
8. No dashed boxes at rest; drop target appears only during drag.
9. All §3 keeps intact; `_contrast.py` and the 150 % clipping check pass in light, dark and HC.
10. A side-by-side sheet (round 1 vs. round 2, same data, same tab) for the owner.
