# Phase 1 mockups: Evrakçı "Ofis gibi"

HTML mockups of the Qt window at 1366×768, light and dark. They are the approval artefact for
Phase 1 and the spec for Phase 2 (tokens → QPalette + QSS) and Phase 3 (one agent per tab).
All data is invented. `docs/ui-goal/decisions.md` (D1–D13) wins over anything here.

## Visual direction

1. **A Windows 11 Office window, not a web page.** Title bar with the menu bar inline (Dosya … Yardım,
   Alt access keys underlined), a text tab strip with a 3 px accent underline, one command bar per
   tab, a 1 px splitter, an inspector on the right, and a facts-left / zoom-right status bar.
2. **Quiet neutral chrome, one accent.** Chrome and panels are green-tinted greys. Cabinet green
   `#3f5a4c` appears only on the primary button, the selected tab underline, selection frames,
   slider fill and the "İncelendi" band. In dark mode the accent becomes a light green fill with
   dark text, as Windows 11 does.
3. **The memorable part is the filing cabinet, and it is used only in Kontrol, Değerler and Dışa Aktar.**
   Every document is a filed stack: a narrow manila guide tab (pictogram + document number only) on
   a manila page edge, pages below, and a stack foot with the review glyph and the kontrol rider.
   The tab's position, pictogram and line style tell the cut type (QR left/solid, filtre
   centre/dashed, elle right/square badge), and colour only confirms it: QR blue, filtre plum,
   elle slate ink. None of them is orange or red (`kontrol-cuts-gray-*.png` proves the greyscale read).
4. **Orange means kontrol and nothing else.** The orange rider always carries the warning icon
   and the word "Kontrol". Overview flags and the status bar count use the same rule.
   `_contrast.py` fails if any saturated non-kontrol token is within 30° of hue of `--rider`.
5. **Status = icon + word + colour.** One vocabulary on every tab, see "Durum sözlüğü" below.
6. **Flat surfaces, hairline separators.** Only transient layers (menus, tooltips, toasts) and
   paper (page sheets) have shadows. No glass, no gradients, no cards inside panels.
7. **Inter 15/21 with tabular figures** everywhere; weights 400/500/600 only.
8. **Keyboard first, quietly.** Shortcuts live in tooltips, menus and context menus. Keycaps are
   drawn only on (a) the one filled primary, (b) key-hint lines and shortcut tables, (c) search
   fields. Command-bar buttons are icon + label only, on every tab. Every focused item gets the
   2 + 1 px ring.

## Rules applied on every tab

| Rule | Detail |
|---|---|
| One filled primary | It lives in the side panel (inspector footer or panel action) or in the empty state, never in the command bar. Kontrol: Belgeyi onayla · Değerler: Onayla ve sonrakine geç · Yükle: Kontrol'e geç · Şablonlar: Şablonu kaydet · Dışa Aktar: Dışa aktar, after export index.xlsx'i aç · Rehber: Yazdır. A disabled primary keeps a ≥ 4.5:1 label and the reason sits next to it. |
| Headings | No page H1 on work tabs (the tab names the page). Work-area and inspector titles are panel 20/28; pane and section titles section 17/24; empty-state titles panel 20/28. Only the Rehber article keeps its H1 (document content). |
| Save state | Title bar only ("Kaydedildi 14:32"); hidden when no job is open. Şablonlar shows the template's own state in its list ("● kaydedilmedi"). |
| Status-bar zoom | Only on tabs with a zoomable view, and its name says what it zooms: Küçük resim boyutu / Önizleme (Kontrol), Kanvas (Şablonlar), Sayfa kesiti yakınlığı (Değerler), Yazı boyutu (Rehber). Yükle and Dışa Aktar have none. |
| Toasts | One anchor: bottom-right, 16 px above the status bar, inside the side-panel column, never over the table or list being worked. No toast when the page already shows the same done state. A mixed result uses the kontrol icon (`.toast.check`). |
| Kontrol rows | Rider + reason in the Durum cell and a 3 px inset bar (`tr.is-flag`); no row wash. The rider stays on the row in every state, including while files are written. |
| Command-bar overflow | `mockup.js` collapses labelled commands to icon + tooltip from the right, then moves them into "⋯ Diğer komutlar" (Office Simplified Ribbon). The primary never collapses. |
| Text size 130/150 % | Chrome and controls step up one density (rows 48, controls 40, chips 24, icons 20/24), the inspector widens to 368 px and scrolls; tables scroll sideways. `_render.py` renders every tab at 150 % (`png/<tab>-150-light.png`) and runs the clipping check on it. |
| Menus | Access keys are ASCII and never I: &Dosya, Düz&en, &Görünüm, Gi&t, &Araçlar, &Yardım; Yardım ends with "Evrakçı &hakkında". |

## Durum sözlüğü (one vocabulary, every tab)

| Meaning | Icon (Lucide) | Word | Colour token | Where |
|---|---|---|---|---|
| Machine read it surely | signal-high | Emin (%) | `--ok` | Şablonlar live reads, Değerler Güven, Örnek kontrol |
| Below "emin", above the kontrol threshold | signal-medium | Orta (%) | `--text-2` | same |
| Value needs a look | triangle-alert | Kontrol (%) | `--check-text` | value cells, Güven column, reads list |
| Document needs a look | rider (triangle-alert + "Kontrol") | Kontrol | `--rider` | Kontrol stacks and overview, job list, batch table, Dışa Aktar rows |
| Nothing read | circle-x | Okunamadı | `--danger` | value cells, Güven column |
| Human looked at it | circle-check | İncelendi | `--ok` | Kontrol stack foot, Değerler İnceleme column |
| Not looked at yet | circle-dashed | İncelenmedi | `--text-2` | same |
| Page will be dropped | trash-2 + struck page | Silinecek | `--danger` | Kontrol |

The current Qt words map as: "Emin okundu" → Emin, "Emin değil" → Kontrol (tooltip "emin değil"),
"Okunamadı" stays. Navigation keeps the Qt names: "Sonraki kontrol" (N), "Önceki kontrol"
(Shift+N), "Yalnızca kontrol gerekenler". "Onayla" replaces "Öneriyi kabul et" on buttons because
the same command also confirms emin values in Tümünü incele / Örnek kontrol; the tooltip keeps
"Öneriyi kabul et". Record this in decisions.md when the owner signs the mockups off.

## Shortcut changes against 07-qol-audit §3 (Turkish Q keyboard)

| Was | Now | Why |
|---|---|---|
| Ctrl+/ shown | **Shift+F1** shown (Ctrl+/ still works) | "/" is Shift+7 on Turkish Q |
| Ctrl+= shown for zoom in | **Ctrl+Num+** / Ctrl+wheel shown; register `QKeySequence.ZoomIn` + numpad | "=" is Shift+0 on Turkish Q |
| Ctrl+Shift+0 = %100 | not used | it is the "=" key on Turkish Q |
| Esc = İptal (OCR) / Durdur (export) | **Ctrl+.** (button only otherwise) | a stray Esc must never cancel 640 pages of work; Esc only dismisses |
| Ctrl+G = Tüm sayfayı göster (Değerler) | **Ctrl+G = Belgeye / sayfaya git on every tab**; the crop's full page is **Boşluk**, like the Kontrol loupe | one meaning per key |
| Esc = "Geri al" (cell) | Esc = **Vazgeç**; "Geri al" is only Ctrl+Z | two meanings of one word |
| — | **F6 = Sonraki bölge**, shown in the Değerler hint line; Tab on the last value leaves the table | no keyboard trap |
| Tooltips | render hints with `QKeySequence.toString(NativeText)` so the layout decides what is shown | |

## Token summary (`tokens.css`)

| Group | Values |
|---|---|
| Surfaces | `--bg-chrome` (title, tabs, status) · `--bg-layer` (command bar, inspector, lists) · `--bg-canvas` (work area) · `--bg-paper` (page sheets only) · `--bg-popover` · `--bg-hover/pressed/selected` |
| Text | `--text` (≥ 7:1) · `--text-2` (≥ 4.5:1) · `--text-disabled` · `--text-accent` · `--text-on-accent` |
| Lines | `--hairline` (decorative) · `--edge` (control borders, ≥ 3:1) · `--edge-strong` |
| Brand | `--accent` green · `--manila` / `-edge` / `-ink` · `--rider` / `-edge` / `-ink` + `--check-text` / `--check-wash` (kontrol only) |
| Cut types | `--cut-qr` blue · `--cut-filter` plum · `--cut-manual` slate ink (never orange, never the danger red) |
| Status | `--ok` · `--danger` (crimson, ≥ 30° from orange) · `--info` (+ `-wash`) |
| Chips | `--chip-h` 20 (kbd, rider, badge) · `--guide-h` 24 (guide tab); both step up at 130/150 % |
| Type features | `--font-features` (tnum, cv05) · `--font-features-code` (+ ss02, cv08, zero) for values and file names so I/l/1, O/0, B/8 differ |
| Type (D4) | page 24/32 · panel 20/28 · section 17/24 · body 15/21 · secondary 13/18 · caption 13/18; `--text-scale` via `[data-text=115\|130\|150]` |
| Spacing (D6) | `--sp-1 2 3 4 6 8 12` = 4 8 12 16 24 32 48 |
| Radii (D6) | `--r-sheet` 2 · `--r-control` 4 · `--r-overlay` 8 |
| Density (D5) | `[data-density=compact\|normal\|comfortable]` → `--row-h` 32/40/48, `--control-h` 28/32/40, `--commandbar-h` 40/48/56 |
| Motion (D7) | `--dur-0…4` = 0/80/120/180/240 ms; `--ease-standard/enter/exit/linear`; all 0 under `[data-motion=reduced]` or OS reduced motion |
| Focus (D11) | `--focus-ring` = 1 px `--focus-inner` + 2 px `--focus-outer` |

The contrast proof for every text/background pair (light and dark) is the comment table at the
top of `tokens.css`. It is generated: run `python3 _contrast.py --write` after changing any
colour; it exits 1 if a D10 pair fails, if a non-kontrol token is within 30° of hue of the rider,
or if danger equals the kontrol highlight in HC. The focus proof scores the 2 px outer ring against
every surface it can sit on (the 1 px inner ring is a separator; slots keep ≥ 4 px of canvas around
paper so the ring never sits on a page sheet). Current state: 0 failures in light, dark and HC.

## Files

| File | What it is | Who edits |
|---|---|---|
| `tokens.css` | All design tokens, light / dark / hc preview, density, motion, focus | Design lead only |
| `shell.css` | Window chrome and shared components | Design lead only; ask for additions |
| `mockup.js` | Injects the Lucide icon sprite; reads `?theme= &density= &text= &motion=` | Design lead (add icons here) |
| `kontrol.html` | Kontrol tab: `main`, `loupe`, `empty`, `cuts` (1- and 2-page documents of each cut type), `cuts-gray` (the same in greyscale) | Kontrol author |
| `degerler.html` | Değerler: `main` (kontrol gerekenler, F2 edit, undo toast), `empty`, `all` (Tümünü incele), `ornek` (spot-check sample before export) | Değerler author |
| `<tab>.html` | One file per tab: `yukle`, `sablonlar`, `degerler`, `disa-aktar`, `rehber` | Tab author |
| `_render.py` | Renders every `*.html` to `png/<name>-<theme>.png`, plus `-150-light` and (Kontrol, Değerler) `-hc`, and lists clipping, sideways scrolling at 100 % text and menu access keys that are not ASCII A–Z without I or repeat | anyone |
| `REVIEW.md` | Phase 1 review findings and what was done with each | design lead |
| `_contrast.py` | Recomputes the D10 contrast table from `tokens.css` | anyone |
| `png/` | Rendered output (generated, do not edit) | `_render.py` |

## How to write a tab mockup (follow exactly)

1. Copy the skeleton of `kontrol.html`: `<html data-theme="light" data-density="normal">`, link
   `tokens.css` then `shell.css`, load `mockup.js` at the end of `<body>`.
2. Inside `<div class="sheet">`, one `<div class="window" data-state="…">` per state, each a full
   1366×768 window: `titlebar` → `tabstrip` (your tab `aria-selected="true"`) → `commandbar` →
   `workspace` (`work` + `splitter` + `inspector` as needed) → `statusbar`. The first state is the
   main screenshot; add an `empty` state for every tab.
3. Use shell classes as they are: `.btn.subtle|secondary|primary|icon`, `.kbd`, `.input`, `.select`,
   `.search`, `.slider`, `.table`, `.list`, `.menu` + `.mi`, `.tooltip`, `.toast`, `.infobar(.check|.danger)`,
   `.rider`, `.status(.ok|.check|.todo)`, `.badge`, `.empty`, type roles `.t-page/.t-panel/.t-section/.t-2/.t-caption`.
   States are classes you can force: `.is-hover`, `.is-focus`, `aria-selected`, `aria-pressed`, `disabled`.
4. Tab-only styles go in the page's own `<style>` and may use **only** `var(--…)` tokens. No hex,
   no new radii, no spacing outside the scale. 1 px hairlines and marked optical nudges are fine.
5. Icons: `<svg class="i"><use href="#name"/></svg>`, names from `mockup.js` (Lucide). Need a new
   one? Add it to the sprite with its Lucide name.
6. Buttons: verb first, sentence case, Turkish ("Filtreyi uygula", "Belgeyi onayla"). One primary
   per view. Icon-only buttons need `aria-label` with the shortcut, and the tooltip shows it.
7. Keep every existing feature and its wording from `src/evrakci/ui/<tab>.py`; new commands follow
   `docs/research/07-qol-audit.md` §3 for keys.
8. Run `python3 _render.py yourtab.html`, open both PNGs, and fix every clipping warning (a scrolling
   list uses `overflow:auto`, not `hidden`; mark a deliberate crop with `data-clip-ok`).

## Kontrol decisions worth reviewing

- **Layout pattern: split pane** (overview + timeline | inspector). The timeline wraps
  documents into rows so two rows of 160 px thumbnails fit at 1366×768; a cut marker always wraps
  with the document it starts.
- **Overview strip**: one tick per document start, a bottom "İncelendi" band, orange flags with
  document numbers (numbers merge when closer than 28 px), a viewport box and a cursor line.
- **Thumbnail size** is the status-bar slider (Office zoom position, Ctrl+wheel, Ctrl+= / Ctrl+-).
- **New keys**: U = "Sonraki incelenmemiş" (proposal; N stays "Sonraki kontrol", Shift+N
  "Önceki kontrol"), Enter = "Belgeyi onayla" (marks the document reviewed and moves on), Ctrl+G
  "Git…" (belge or sayfa). All need sign-off.
- **Loupe filmstrip** keeps each document's start tick (cut pictogram at the cut position) and its
  rider under the pages, so paging with the arrows never loses where documents start.
- **Context menu** opens to the right of the clicked page so the selection stays visible.
- **Delete** from the context menu names the count ("3 sayfayı sil") and is undoable; deleting
  every page of a document is refused with an InfoBar (not shown).

## Skill notes (conflicts resolved in favour of decisions.md)

- `typography` asks for 16 px body and ≤ 3 weights, none above 600: body stays 15 px (D4); weights
  400/500/600 adopted, so DESIGN.md's 700 is retired.
- `icon-buttons` asks for 44 px hit targets (web touch): desktop D5 controls are 32 px (28 Sıkı);
  slider thumbs get a 24 px hit area. It also asks for a kbd in every icon tooltip: kept in tooltips,
  but command-bar buttons carry no keycaps (Office convention, review finding).
- `verbs` asks for verb-first labels; Turkish puts the imperative last ("Yeni iş oluştur",
  "Değişken ekle"), which is the Windows Turkish convention.
- `colour-palette` 60-30-10 holds: canvas, layer surfaces, accent < 10 %.
- `spacing` 8 pt majors: chrome heights 32/40/48 follow it; 4 px micro gaps only inside components.
- `defaults`: the template select is pre-filled with the last used template; drafts are a Qt concern
  (QSettings) rather than localStorage.
- `page-patterns`: Kontrol = Split Pane (8); `surfaces`: no dialog for single actions; destructive
  actions are undoable instead of confirmed (research 04 r11 wins over the skill's confirm-first rule).

## Fonts

Inter is installed in this container (`fonts-inter`, `fc-list | grep -i inter`), so the PNGs render
in Inter. On Windows the fallback chain is Segoe UI Variable Text → Segoe UI.
