# Evrakçı final UI spec: direction A "Fluent 2 Mica", all six tabs

This folder is **the spec for the Qt build** (GOAL.md Phase 2 and 3). It finishes direction A, which
the owner picked ("A is much better"), for every tab, fixes what the round-2 judges found, and adds the
high-contrast theme and the 150 % text renders. All data is invented.

| File | What it is |
|---|---|
| `tokens.css` | Every colour, size, radius, shadow and duration, for `light`, `dark` and `hc`, plus the 130 % and 150 % text steps and the five HC palettes. The contrast proof is written into its header. |
| `shell.css` | The window shell and the shared components. It holds no hex values. |
| `shell.js` | A mockup helper. It builds the title band and status-bar job item once for all pages and switches `?state=`, `?theme=` and `?text=`. |
| `icons.js`, `_icons.py` | Real Lucide 0.460.0 paths (ISC licence), copied verbatim from `lucide-static` by `_icons.py` (76 icons) |
| `yukle.html`, `kontrol.html`, `sablonlar.html`, `degerler.html`, `disa-aktar.html`, `rehber.html` | The six tabs. Each page lists its states in `<html data-states>`. |
| `_contrast.py` | The D10 proof for the three themes. `--write` refreshes the table in `tokens.css`. |
| `_render.py` | Writes the PNGs and checks the layout, overlays and sheet freshness (see §9) |
| `png/` | 121 renders named `<tab>[-<state>]-<light|dark|hc>.png`, `<tab>[-<state>]-<130|150>-light.png` and `<tab>-hc-desert.png` (a light Windows 11 contrast theme), plus 23 `_sheet-<tab>-<state>.png` contact sheets (light, dark, hc, 150 %) for review |
| `REVIEW.md` | Round-3 review findings and what was done for each |

Commands, run from this folder:

```
python3 _contrast.py --write     # 0 failing pairs in light, dark and five HC palettes
python3 _render.py --sheets      # 23 states x 5 renders + 6 Desert, 0 warnings, gate 7 = 64.0 %
python3 _icons.py /tmp/lucide/package/icons   # only after adding an icon name
```

## 1. Concept

**Windows 11 calm, with one brand shape.** Everything around the work stays as quiet as File
Explorer: no resting menu row, one icon-first command bar and three tonal levels. The brand lives
in one shape, the **Evrakçı tab**: the trapezoid tab from the logo. It appears in exactly three
places, and each one carries meaning:

1. **The selected title-band tab** is drawn in this shape, filed into the work layer below it. It
   replaces Fluent's rounded tab with feet and works as the app's signature. You can recognise
   Evrakçı from across the room.
2. **The guide tabs on the timeline** are the same shape in manila. Their position and pictogram
   show the cut type, and a check means the document is reviewed.
3. **The cut diagram in the Kontrol inspector** ("Neden burada başlıyor"): page | guide tab on the
   cut line | page.

Cabinet green is the one deliberate accent. It fills the single primary of each state, the
selection ring, the reviewed segments of the overview and the "filed" moment of the Dışa Aktar done
state (a folder-check seal). The logo symbol, in one colour, is the empty-state mark for first-use
screens. Orange appears only for Kontrol, always as icon + word. In high contrast, Kontrol keeps
the triangle, the word and the rider's outline, and takes the OS text colour.

### What changed against round-2 direction A (judges' notes)

| Judge note | Fix in this spec |
|---|---|
| Kontrol has no visible rounded work layer | The pages lie in a **tray**: a recessed, rounded `well` with a 1 px stroke (rule: *paper lies in a well, data sits on a card*). Değerler, Dışa Aktar and Rehber put their data on cards. |
| Thumbnails 148 px, page pixels 53 % (gate 7 is 60 %) | Thumbnails are now **166 × 234**, and page pixels are **64.0 %** of the timeline viewport with the inspector open (measured by `_render.py`). |
| Inspector has 4 heading levels | Now 3 levels: title (20/28) with the Kontrol rider inline, group labels (13 semibold), card rows. The separate rider row is gone, the reason sentence became the "QR ayıraç: Bulunamadı" row, and "Son değişiklikler" moved to the undo label and the Düzen menu. |
| No "why here" picture | Added a C-style **cut diagram**: last page of Belge 15 (70), the manila guide tab "16" on a dashed filter line, first page of Belge 16 (72) |
| Dark primary is pastel with dark ink | The accent is split into `accent` (lines, rings, indicators: `#93c4a6` in dark, 3:1 on every surface) and `accent-fill` (the filled primary: **`#33694d` with white ink, 6.42:1**) |
| Deleted page 71 is a heavy grey slab in dark | The deleted page is an **empty outline** (`ghost-edge`) with a bin badge and the word "silinecek". The sheet has no fill in any theme. |
| Title bar crowded at 1366 | **Tab icons dropped. The job name and save state moved to the status bar.** See §2. |
| Not memorable, brand is a 16 px logo | The Evrakçı tab shape now appears in the title band, the timeline and the diagram (§1). There is a green "filed" moment and a brand-mark empty state. |
| No HC or 150 % renders | `[data-theme=hc]` maps every token to a Windows system colour, proven for "Black" and the four Windows 11 contrast themes. Every state is rendered at 130 % and 150 % text with 0 warnings. |
| Title-band tabs need WM_NCHITTEST work | Specified with fallbacks and risk in §7 |

## 2. Decision: the title band

**Text-only tabs. The job name and save state go to the left of the status bar.** The band now
holds: logo · ≡ · six tabs · drag space · "Ara Ctrl+K" · caption buttons.

- **Why the tab icons go:** the six tabs are fixed places, not documents. The word is the whole
  label and does not change, so an icon only repeats it, and it costs about 130 px at 1366 and
  about 200 px at 150 %. Explorer, Edge and Terminal show icons because their tabs are documents.
- **Why the job moves to the status bar, not the command bar:** the job is global, not per tab,
  and the command bar changes with every tab. The status bar is always visible, sits where Office
  shows document state, and was the one band with free room on the left. It is a button
  ("Kasım 2026 kapasite raporları ˅", tooltip "İşi değiştir: son işler") that opens the recent-jobs
  list, followed by "✓ Kaydedildi 14:32". **It has no key.** Ctrl+O keeps its one registry meaning,
  "Dosya ekle…" (shortcuts.md: jobs open from the Yükle list); Ctrl+N creates a job and Ctrl+1 goes
  to the job list. On Şablonlar the save item names both objects: "İş kaydedildi 14:32" and
  "Şablon kaydedilmedi", so the job's autosave is never read as the template's. The OS still shows the job in the taskbar and in
  Alt+Tab: the window title is `Kasım 2026 kapasite raporları – Evrakçı`.
- **Result:** at 1366 px the drag area is about **400 px** (it was under 60 px). At 150 % text all
  six tabs, the search and the caption buttons still fit, and nothing is elided.

## 3. Tokens (summary; `tokens.css` is the source)

| Role | Light | Dark | HC | Use |
|---|---|---|---|---|
| `base` L0 | `#e1e6e3` | `#191c1a` | `#000000` | title band, status bar, gutters (Mica fallback) |
| `layer` L1 | `#f3f5f4` | `#232725` | `#000000` | rounded work layer, selected tab, command bar |
| `card` L2 | `#ffffff` | `#2b302d` | `#000000` | inspector cards, tables, reading card |
| `well` | `#e6ebe7` | `#1a1d1b` | `#000000` | Kontrol tray, crop wells, cut diagram, canvas |
| `popover` | `#ffffff` | `#313633` | `#000000` | menus, palette, tooltips, toasts |
| `stroke` / `stroke-soft` | `#d3d9d6` / `#e6eae7` | `#383e3a` / `#343a36` | `#ffffff` | 1 px edges of layer, cards and tray / row lines |
| `text` / `text-2` / `icon` | `#16201a` / `#4a5550` / `#36423c` | `#e9ede9` / `#aab4ae` / `#c2cbc5` | `#ffffff` | ink |
| `text-dis` | `#6c7671` | `#7f8a84` | GrayText | disabled labels |
| `dis-ink` × `dis-alpha` | `icon` × 0.4 | `icon` × 0.4 | GrayText × 1 | disabled command-bar buttons (Fluent's disabled alpha; WCAG exempts disabled controls) |
| `edge` | `#76827c` | `#8c9892` | WindowText | input bottom edges, checkboxes, slider rail and thumb (3:1 on card, layer and base) |
| `accent` | `#3f5a4c` | `#93c4a6` | Highlight | selection ring, selected-row bar, selector pill, slider, selected captions |
| `accent-fill` + `text-on-accent` | `#3f5a4c` + white | `#33694d` + white | Highlight + HighlightText | the one filled primary per state, check badges, box numbers; HC selected rows |
| `text-accent` | `#3f5a4c` | `#a3d0b4` | Hotlight | links only ("Geri al", "Sonraki kontrol", "Değerler'e git") |
| `manila` / `manila-edge` / `manila-ink` | `#e9d9a6` / `#8a7a45` / `#2b2410` | `#ddcb93` / `#b9a76f` / same | Window / WindowText / WindowText | guide tabs and lips only (filed documents) |
| `rider` / `rider-edge` / `rider-ink` | `#e8731a` / `#9c4a0b` / `#241000` | same / `#f5a061` / same | Window / WindowText / WindowText (an outlined chip) | Kontrol only |
| `kontrol-mark` | `#e8731a` | `#e8731a` | WindowText | Kontrol as a fill (overview segment) |
| `check-text` / `check-wash` | `#8a3d00` / `#fde6d1` | `#ffb57e` / `#4d311b` | WindowText / Window | the word Kontrol, uncertain characters |
| `ok` / `danger` | `#1d6a3a` / `#b3123a` | `#82d3a0` / `#ff92a6` | WindowText | Emin, Tamam / Okunamadı, Engel, delete |
| cut types | QR `#1f5fbf`, filtre `#6b3fa0`, elle `#37424a` | QR `#2a62b8` | WindowText | on manila; shape + position also differ |
| `paper` | `#ffffff` | `#e4e6e1` (dimmed) | `#ffffff` | page sheets; scans are never inverted |
| `ghost-edge` | `#76817b` | `#6f7a74` | WindowText | outline of a page marked for deletion (3:1 on `well`: 3.17 / 3.81) |
| `focus-outer` / `focus-inner` | `#16201a` / white | white / `#16201a` | WindowText / Window | D11 ring |

**HC tokens are system colours, never literals** (D9). `tokens.css` defines six `--sys-*` roles
(Window, WindowText, Hotlight, GrayText, Highlight, HighlightText) with the "High Contrast Black"
values, and `[data-hc="aquatic|desert|dusk|nightsky"]` swaps in the Windows 11 contrast themes. In
Qt they are read from `QPalette` when HC is on. Kontrol is WindowText + triangle + word + outlined
rider: HC themes have no warning colour, and Hotlight (yellow in Black) belongs to links. Selection
is Highlight with HighlightText. Disabled is GrayText. Paper and scans stay as scanned.

- **Type (D4):** Inter 400/500/600. Sizes used: 13/18 (captions, labels), 15/21 (body, table
  cells), 17/24 (Rehber section headings), 20/28 (inspector title, empty-state title), 24/32 (one
  element per screen at most: the Değerler suggested value, the Rehber page title). Numbers use
  `tnum`; OCR values use `tnum ss02 zero`.
- **Spacing (D6):** 4, 8, 12, 16, 24, 32, 48. **Radii (D6, no others):** 2 paper and marks drawn on
  paper (box numbers, progress bars, inline code), 4 controls, riders, badges and segmented items,
  8 layer/cards/popovers/tray. Circles only for the slider thumb, check badges and step markers. The
  guide tab is a clipped trapezoid with no radius.
- **Sizes, Normal → at 130 % and 150 % text** ("chrome steps up one density", D5 Normal → Geniş;
  one threshold, ≥ 130 %, for the density step, pane collapse and status-bar priority): title band
  44 → 52, tab 36 → 44, command bar 44 → 52, icon button 36 → 44, control 32 → 40, row 40 → 48,
  overview 32 → 40, status bar 28 → 36, inspector 312 → 368 (130 %) / 400 (150 %), icons 16/20 →
  20/24, guide tab 24 → 32. Type scales × 1.3 / × 1.5 (`--ts`). Thumbnails keep 166 × 234: they follow the zoom slider, not the
  text size.
- **Elevation:** strokes first. One float shadow (light alpha < 0.08). Paper has its own two-step
  shadow. Dark mode adds a 1 px top highlight. HC has no shadows and puts a white edge on everything.
- **Motion (D7):** menus and palette 180 ms on the enter curve, toast 240 ms. Nothing moves on
  repeated actions. Reduced motion removes both.
- **Contrast (D10), 0 failing pairs** in light, dark and five HC palettes (Black, Aquatic, Desert,
  Dusk, Night sky; 78 pairs each, plus 8 hue checks in light and dark and a Kontrol-is-not-link check
  in HC). Dark primary: white on `#33694d` is 6.42:1. No non-Kontrol hue sits within 30° of the
  rider. The weakest HC pair is Dusk disabled text, GrayText `#a6a6a6` on `#2d3236`, 5.32:1.
  **The Windows 11 palette values come from Settings > Accessibility > Contrast themes as listed in
  Microsoft's contrast-themes documentation; check them once on a Windows 11 machine before the Qt
  build** (the docs host could not be reached from this session).

## 4. Components

| Component | Spec |
|---|---|
| **Title band** | 44 px on `base`: 20 px app icon, ≡ (32 px, menus on Alt), six text tabs (15 medium, padding 12 + 8 px), drag space, search box ("Ara · Ctrl+K", opens the palette), caption buttons 46 × 32. ≡ pressed = `card` fill + stroke. |
| **Evrakçı tab (selected)** | Trapezoid with 12 px slants, `layer` fill, 1 px `stroke` on three sides, 1 px overlap into the layer so the two read as one sheet. Text 15 semibold `text`. Unselected tabs: `text-2`, hover = `hover` fill. |
| **Menu row on Alt** | A floating strip (popover style) under ≡ with Dosya … Yardım. Access keys are underlined only while it shows. The menu opens below its item. No layout shift. |
| **Command bar** | 44 px on `layer`. 36 px icon buttons (radius 4, hover `hover`, toggled = `selected`), separators 1 × 20 px, **≤ 2 labelled commands** (15 medium). Every button has a tooltip "Label (Key)" with the registry label word for word. Disabled = icon ink at 40 % (`dis-ink` × `dis-alpha`, Fluent's disabled alpha), still listed; in HC GrayText. |
| **Buttons** | `primary` (`accent-fill`, white, 600, 40 px in the inspector foot; **one per state**), standard (`card` + stroke), subtle (transparent). Keys appear as quiet 13 px text inside the primary when useful ("Dışa aktar Ctrl+E"). No keycaps. |
| **Fields** | 32 px, `card`, stroke + 3:1 `edge` bottom, 2 px `accent` bottom on focus, `danger` bottom + message with ban icon on error. The only icon inside a field is a functional one (search, clear). |
| **Cards / inspector** | **One template on every tab:** title 20/28 on the layer (+ inline rider) with a `text-2` subtitle → group label 13 semibold `text-2` → Settings-style cards (radius 8, 1 px stroke) → fixed foot with the one primary and **subtle** secondaries. Değerler: "Sicil no" / "Belge 16, sayfa 72"; its two secondaries (Elle yaz F2, Yeni varyant çiz V) stay a pair because both act on the same value, but in the subtle style. Dışa Aktar: "Dışa aktarma ayarları" / "96 belge, D:\Muhasebe\Çıktı\Kasım". Label/value rows (`kv`) without hairlines. Action rows (`act`): label left, value + chevron right, hover fill. The scroll area shows a thin scrollbar thumb and fades its cut edge. |
| **Status vocabulary** | Emin (signal-high, `ok`), Orta (signal-medium, `text-2`), Kontrol (triangle-alert, `check-text`, semibold), Okunamadı (circle-x, `danger`), İncelendi (circle-check) / İncelenmedi (circle-dashed). Pre-flight grades: Engel (ban, danger), Kontrol, Eksik (circle-dashed), Bilgi (info), Tamam (circle-check). Always icon + word. The İncelendi column shows circle-check or circle-dashed in every row, with the word in the tooltip and accessible name. |
| **Rider** | 22 px orange chip, radius 4, 1 px `rider-edge`, icon + "Kontrol" (or "7 Kontrol") 13 semibold `rider-ink`. **Rule:** the rider marks a Kontrol *object* (a job, a document, a timeline item, a palette result); a *grade* inside a list row or a pre-flight card is icon + word in `check-text`, never the chip (Yükle and Dışa Aktar Ön kontrol, all tables). HC: an outlined chip in WindowText (2 px edge). |
| **Guide tab + lip** | Evrakçı tab in manila, 24 px, cut pictogram + document number + optional reviewed check. Position = cut type (QR left, filter centre, manual right). A 6 px manila lip spans the document with a top line: 2 px solid (QR), 1 px dashed (filter), 2 px dotted (manual). |
| **Page thumbnail** | 166 × 234, radius 2, 1 px edge + paper shadow. Selection: 2 px `accent` ring 3 px outside + 22 px check badge top-left. Focus (D11): 1 px inner + 2 px outer ring outside the selection. Deleted: empty outline + bin badge + "NN silinecek" in `danger`. Separator sheet: 40 px tile "Ayraç NN". Page gap 12, document gap 24. |
| **Overview** | One segment per document, told apart by **height as well as colour**: not reviewed = a 4 px `track` stub, reviewed = 8 px `accent`, Kontrol = 14 px `kontrol-mark` with a `rider-edge` outline (the only segment that rises above the row). Each segment has a tooltip and accessible text ("Belge 21: Kontrol"). The viewport is a 2 px `text` rounded rectangle. "Belge 14–18 / 96" on the right. |
| **Cut diagram** | In a `well` inside the "Neden burada başlıyor" card: 52 × 73 mini pages, a guide tab on top of a 2 px cut line styled like the lip (dashed = filter), page numbers below. |
| **Tables** | In a card: 36 px header 13 semibold `text-2`, rows 40 with `stroke-soft` lines, selected row = `selected` + 3 px `accent` bar (HC: Highlight fill with HighlightText). Inline edit in the same box (inset 4 px, D11 ring). While a cell is edited, its key hint ("Sicil no, Belge 16 düzenleniyor", "Enter onayla, sonraki kontrol", "Esc vazgeç") sits in a 36 px **edit bar at the foot of the table card**, so it never covers a row; the table scrolls the current row away from the bottom edge. Uncertain characters: `check-wash` + 2 px `rider-edge` underline. |
| **Selector bar** | Text items with counts; the selected item is semibold with a 16 × 3 px `accent` pill. The set of items is fixed (Değerler: Kontrol gerekenler, İncelenmemiş, Tümü, Örnek); a mode selects an item, it never swaps one out. |
| **Menus / palette / tooltip / toast** | `popover`, 1 px stroke, radius 8 (tooltip 4), one float shadow. Menu items 34 px, key right-aligned 13 px `text-2`, danger item last. The palette is 600 px wide, groups "Komutlar" / "Belgeler" and a footer "↑ ↓ seç, Enter çalıştır, Esc kapat"; a row shows only its own registered key. **Toast, one anchor on every tab:** bottom-right of the work layer, 12 px in, above the status bar. When the tab has an inspector, the toast is laid out in the inspector column directly above the foot (inserted into its layout, so the scroll area shrinks and nothing is covered: not the primary, the table or the page). The message wraps; "Geri al" (`text-accent`) and × never do. |
| **Status bar** | 28 px on `base`, 13 px. Job button (no key) + save state, then the tab's counts (numbers semibold `text`, one icon per count), zoom slider with "%" at the right. The slider rail is `edge` (3:1), the thumb is 16 px with an `edge` outline and a 24 × 24 hit area. From 130 % text the priority-2 items (save state, page position, counts that the inspector also shows) are hidden, never clipped. |
| **Empty states** | The pane skeleton stays (table header, tray, canvas), then a mark, a 20/28 title, one sentence (≤ 58 characters), one verb-first primary and optionally one standard button. Everything that needs a selection or a job is disabled, secondaries included. The brand mark (logo symbol, `brand-mark`) is used for first-use states; values that were not read and search with no results use a plain Lucide icon. |
| **High contrast** | System colours as in §3. Tonal steps become WindowText 1 px edges; hover and toggles become 1 px Highlight outlines; selected rows and list items get the Highlight fill with HighlightText; Kontrol is WindowText + triangle + word + outlined rider; links are Hotlight; disabled is GrayText (checkboxes too); paper and scans stay as they are. |
| **Key names** | One function renders every key in tooltips, menus, the sheet, the palette and hints: `actions.key_text` = NativeText without `qtbase_tr`, plus an override map **Up → ↑, Down → ↓, Left → ←, Right → →, Space → Boşluk, Return → Enter**. So "Alt+↑", "Önizle (Boşluk)", "Önceki sayfa (←)". Prose may say "ok tuşları", but a key in parentheses always comes from `key_text`. |

## 5. Per-tab layout and states (1366 × 768)

Every tab uses the same frame: title band 44, layer (command bar 44 + body with 12 px padding),
status bar 28. Left panes and inspectors sit on the layer; data sits on cards; paper lies in wells.

| Tab | Layout | States rendered |
|---|---|---|
| **Yükle** | İşler pane 288 (search, recent jobs with Kontrol riders and "Dışa aktarıldı") · Partiler card filling the column (grip, No, Dosya, Sayfa, QR ayıraç, Durum; a Toplam row; the drop hint as the card's last line, no dashed box at rest) · İş özeti inspector (Ön kontrol card: counts + Tamam/Kontrol grade lines; Tarama profili card with an action row to the Rehber; primary **Kontrol'e geç**) · command "Dosya ekle… (Ctrl+O)" | `main`, `running` (progress card: 77 / 124, %62, time left, rate; "İptal et" labelled, tooltip "Okumayı iptal et (Ctrl+.)"; primary disabled + note), `drop` (dashed `accent` frame on the layer edge only during the drag + a card listing the 3 files), `empty` (brand mark, primary **Yeni iş oluştur**, three numbered steps) |
| **Kontrol** | Overview row 32 · paper tray (timeline, 2 rows of 166 × 234 pages) · inspector 312 (Belge 16 + rider; cut diagram card; selection action card; primary **Belgeyi onayla**) | `main`, `menu` (context menu on page 73, shortcuts right-aligned, "3 sayfayı sil" last), `loupe` (page 73 large in the tray, Sığdır/Genişlik/%100, filmstrip stays visible, toast "Kesim eklendi: sayfa 74 · Geri al"), `palette` (Ctrl+K "kontrol": commands + documents), `empty` (brand mark, primary **Yükle'ye git**, Son işler card) |
| **Şablonlar** | Şablonlar + Değişkenler pane 264 (numbered variables = box numbers, sections nested) · canvas column (Örnek and Önizleme sayfası selects; paper in a well with mm rulers that mark the selected box and the cursor; numbered field boxes, handles on the selected one, live read-out) · inspector (Kutu card: Ad, Zorunlu, page, X/Y/Genişlik/Yükseklik mm + nudge hint; "Okunanlar, örnek 1" card; primary **Şablonu kaydet**) | `main`, `empty` (brand mark, primary **Yeni şablon oluştur**) |
| **Değerler** | Table card (selector bar Kontrol gerekenler / İncelenmemiş / Tümü, search, template select; 13 rows with inline edit on row 16 and its key hint) · source inspector 368 on the shared template (title "Sicil no" / "Belge 16, sayfa 72"; Sayfadaki yeri card with the crop in a well; Değer card Okunan / **Öneri 24/32** / Güven / why; primary **Onayla ve sonrakine geç**, subtle Elle yaz and Yeni varyant çiz) · edit bar at the table card's foot · toast "8 değer onaylandı · Geri al" above the inspector foot | `main`, `ornek` (spot check: the fixed selector with Örnek 20 selected, one value per row, Belge 58 Firma in the inspector, status bar "Belge 58 / 96"), `empty` (frame + header kept, primary **38 belgeyi oku**, inspector "Değer seçilmedi", every value command disabled) |
| **Dışa Aktar** | Ön kontrol card (graded rows: grade, message, count (none on Tamam), action link) · Dosya adları card (filter toggle, Kontrol rows first, changed characters marked) · inspector "Dışa aktarma ayarları" (Hedef klasör, Dosya adı kalıbı, Seçenekler incl. "İşi saklama süresi"; primary **Dışa aktar Ctrl+E**) · command "Yenile" (tooltip "Listeyi ve önizlemeyi yenile (F5)") | `main`, `blocked` (2 Engel rows on `danger-wash`, field errors, primary disabled + "Önce iki engeli giderin."), `running` (progress banner 58 / 96, Durdur labelled in the bar; a lock note at the top of the inspector and **every** field, button and checkbox drawn disabled), `done` (**green filed moment**: folder-check seal, no side stripe, "96 belge yazıldı", Kontrol line kept, primary **Klasörü aç**, then "index.xlsx'i aç" and "Dosya Gezgini'nde göster"; foot "Yeniden dışa aktar…" subtle), `empty` (brand mark, primary **Yükle'ye git**) |
| **Rehber** | İçindekiler pane 256 (search with result count and F3 arrows, sections with hit counts) · reading card (68 ch measure, numbered steps because they are a sequence, markers scale with the text, search hits `selected` + accent underline, current hit filled) · Ayıraç sayfası yazdır inspector (front/back preview in a well with its sentence repeated as 13 px text below, Kaç adet / Kâğıt / Dosya; primary **Yazdır Ctrl+P**) | `main` (search "ayıraç", 8 results, 3 / 8), `empty` (no result for "laminasyon": one sentence, Aramayı temizle, frequent topics), `menu` (Alt pressed: floating menu row, Yardım menu with the registry labels: Yardım konuları F1, Klavye kısayolları, Komut ara…), `keys` |

**From 130 % text** (`*-130-light.png`, `*-150-light.png`; one threshold): the bands grow one
density, panes and inspectors scroll (a thin scrollbar thumb plus a fade on the cut edge mark every
scroll viewport), and the card order never changes with the text size. The left navigation panes
(İşler, Şablonlar, İçindekiler) collapse to their toggle in the command bar, like Outlook's folder
pane, and status-bar priority-2 items hide. In Değerler the Sayfa column moves to the source pane
and company names may wrap. In Kontrol the inline Belge line of the loupe header is dropped,
because the inspector already shows it. Gate 7 holds at 100 % (64.0 %) and 130 % (60.4 %); at
150 % the wider inspector leaves 47.2 %; hiding the inspector (its command-bar toggle) gives the pages the room back.

## 6. Qt mapping

| Element | Qt implementation |
|---|---|
| Tokens | `tokens.json` (DTCG) generated from `tokens.css` → `QPalette` per theme (Window = base, Base = card, AlternateBase = layer, Highlight = accent-fill, HighlightedText = text-on-accent, PlaceholderText = text-2, Text/WindowText = text, Link = text-accent) + one templated QSS (`{{token}}` substitution). The text size multiplies `QFont.pointSizeF` and the density token set. |
| Theme switching | `QStyleHints.colorScheme()` + `colorSchemeChanged`. HC: on Windows `SystemParametersInfo(SPI_GETHIGHCONTRAST)`, then take `QPalette` from the OS (`QGuiApplication.palette()`) and map the `--sys-*` roles straight from `QPalette` (Window, WindowText, Link = Hotlight, disabled Text = GrayText, Highlight, HighlightedText); Kontrol = WindowText + icon + word + outlined rider. No QSS colour literals in HC. Unit-test D10 against the five palettes in `_contrast.py`. |
| Focus ring (D11) | A `QProxyStyle.drawPrimitive(PE_FrameFocusRect)` painting a 2 px `focus-outer` + 1 px `focus-inner` rounded rectangle on every focusable widget. Delegates paint their own ring outside the selection ring. |
| Title band | A custom `TitleBar(QWidget)` inside a frameless `QMainWindow` (§7), holding: `QLabel` icon, ≡ `QToolButton` (`InstantPopup`, six `QMenu`s), `EvrakTabBar(QTabBar)`, a stretch, `SearchButton(QPushButton)` that opens the palette, and three caption `QToolButton`s. |
| Evrakçı tab (selected tab, guide tab) | One helper `evrak_tab_path(rect, slant=12) -> QPainterPath`. `EvrakTabBar.paintEvent` fills the selected tab with `layer` and strokes three sides with `stroke`. The timeline delegate draws the same path in `manila` / `manila-edge`. The inspector diagram reuses it. |
| Menu row on Alt | `QMenuBar` kept hidden. An event filter on `Key_Alt` press/release, or ≡, shows a frameless popup strip at ≡'s bottom-left. `SH_UnderlineShortcut` is true only while it shows. Alt+letter opens the menu directly. |
| Work layer | `QFrame#layer { background: layer; border: 1px solid stroke; border-radius: 8px; }` with 8 px side margins in the central widget's layout. |
| Command bar | `QToolBar` of `QToolButton`s with `setDefaultAction(registry.action(id))`. Icon-only `ToolButtonIconOnly` 36 × 36, labelled `ToolButtonTextBesideIcon`. QSS `:hover` / `:checked` / `:disabled`. Separators via `addSeparator()` styled 1 × 20. |
| Icons | Lucide SVG → `QSvgRenderer` → `QIcon` per size (16/20/24) and per colour token. Recolour by replacing `currentColor` before rendering. Stroke 1.75 at 16 px, 1.6 at 20 px. |
| Buttons, fields | `QPushButton#primary` / default / `[flat=true]` in QSS. `QLineEdit { border-bottom: 1px solid edge }`, `:focus { border-bottom: 2px solid accent }`, `[error=true]` property for the danger edge. `QCheckBox::indicator` 20 px radius 4. |
| Inspector | `QScrollArea` (thin `QScrollBar` QSS) of `QFrame.card` holding `QFormLayout` (label column 13 px `text-2`) and action rows (`QPushButton` flat, value + chevron painted). The foot is outside the scroll area. Group labels are `QLabel` 13 semibold. |
| Status vocabulary, rider | Inline in delegates: icon pixmap + text with `QFontMetrics`. The rider is `drawRoundedRect(r=3)` + 1 px edge. As a widget: `StatusLabel(QWidget)`. |
| Kontrol tray + timeline | `QFrame#tray` (`well`, stroke, radius 8) holding a `QListView` (IconMode, custom `QAbstractItemView` layout for document rows) and one `QStyledItemDelegate` that paints guide tab, lip, page pixmap (cached, 9-patch shadow), selection ring, check badge, focus ring, ghost outline for deleted pages and the separator tile. No widget per page; smooth at 1,000 pages. |
| Overview | A custom `QWidget.paintEvent`: 96 `drawRoundedRect(r=2)`, the viewport rectangle; drag moves it. |
| Cut diagram | A small `QWidget` painting two cached mini pixmaps, the tab path and a `Qt.DashLine` / `DotLine` / solid pen for the cut type |
| Loupe | `QGraphicsView` in the tray (fit/width/100 %), a filmstrip `QListView` below, `Space`/`Esc` toggles |
| Edit bar | A `QFrame` under the `QTableView` inside the table card, shown while the delegate's editor is open; text from `key_text`. `scrollTo(index, PositionAtCenter)` after Enter moves on. |
| Tables | `QTableView` in a card frame, `QHeaderView` 36 px, grid off, the delegate draws `stroke-soft` lines, the selected-row bar and the uncertain-character wash with `QTextLayout` format ranges. `QFont.setFeature("tnum"/"ss02"/"zero")` (Qt 6.7+). Inline edit via `createEditor` with the cell rect inset by 4. At 150 %: `setColumnHidden(page)` and word wrap on Firma. |
| Selector bar | Checkable `QToolButton`s in a `QButtonGroup`. The pill is painted in `paintEvent`. |
| Şablonlar canvas | `QGraphicsView` + `QGraphicsScene` at 3 px/mm × zoom. Field boxes are `QGraphicsRectItem` subclasses with number badges and 8 handles. Rulers are two custom `QWidget`s listening to the view's transform. Snap toggle, arrow nudging 0.25 / 1 mm. |
| Menus, palette, tooltip | `QMenu` QSS (`popover`, radius 8 needs `FramelessWindowHint` + `WA_TranslucentBackground` + cached shadow). The palette is a frameless `QDialog` with `QLineEdit` + `QListView` over the actions registry. Tooltips come from `QAction.toolTip()` ("Label (Key)"). |
| Toast | A child widget inserted into the inspector's `QVBoxLayout` just above the foot (tabs without an inspector: bottom-right of the layer, 12 px in), `QPropertyAnimation` on opacity for 240 ms (skipped under reduced motion), "Geri al" calls the undo stack. |
| Status bar | `QStatusBar` 28 px. Permanent widgets: job `QToolButton` (menu of recent jobs, no shortcut), save `QLabel` ("İş kaydedildi" + "Şablon kaydedilmedi" on Şablonlar), count labels, zoom `QSlider` + `%` label. A priority property hides items when the text size is ≥ 130 %. |
| Progress | `QProgressBar` QSS 4–6 px (`track` / `accent`). On Windows also `ITaskbarList3.SetProgressValue`. |
| Empty states | A shared `EmptyState(QWidget)` (mark, title, text, buttons) placed inside the kept skeleton. The brand mark is an SVG with `currentColor` = `brand-mark`. |

## 7. The custom title band in Qt

**Windows 10/11 (primary target).**
1. `setWindowFlags(Qt.FramelessWindowHint | Qt.Window)` would also lose the native resize border,
   shadow and snap. Instead, keep the native frame and extend the client area into it:
   `DwmExtendFrameIntoClientArea(hwnd, {0,0,1,0})` and answer **`WM_NCCALCSIZE`** (wParam TRUE,
   return 0 with the top inset removed) in `QWidget.nativeEvent` / `QAbstractNativeEventFilter`.
   The window keeps its DWM shadow, rounded corners (`DWMWA_WINDOW_CORNER_PREFERENCE = DWMWCP_ROUND`),
   resize borders and Aero Snap.
2. **`WM_NCHITTEST`**: map the cursor to the title band and return `HTCAPTION` over the drag area
   and over empty title-band space. Return `HTCLIENT` over tabs, ≡, search and caption buttons, and
   `HTTOP`/`HTTOPLEFT`/… within 6 px (DPI-scaled) of the edges. Return **`HTMAXBUTTON` over the
   maximise button** so Windows 11 shows **Snap Layouts** on hover. Qt does not receive the clicks
   then, so handle `WM_NCLBUTTONDOWN`/`UP` for that button and repaint its hover state from
   `WM_NCMOUSEMOVE`/`WM_NCMOUSELEAVE`.
3. Double-click on the drag area maximises (`HTCAPTION` gives this for free), and right-click
   opens the system menu (`GetSystemMenu` + `TrackPopupMenu` on `WM_NCRBUTTONUP`).
4. Mica: `DwmSetWindowAttribute(DWMWA_SYSTEMBACKDROP_TYPE = 38, DWMSBT_MAINWINDOW = 2)` on
   Windows 11 22621+, with the title band and status bar painting `base` at about 70 % alpha over it.
   Use solid `base` on Windows 10, in HC, when transparency effects are off, and behind pages and
   tables always. `DWMWA_USE_IMMERSIVE_DARK_MODE` follows the theme.
5. Caption buttons are 46 × 32 `QToolButton`s with Segoe Fluent Icons glyphs (or the Lucide
   fallback), close hover `#c42b1c` with white glyph, the system convention; it is the only
   red outside the tokens, and it is OS chrome.

**Linux and other platforms: fall back to the native title bar.** No custom frame. The tab bar
moves to the top of the client area as the first row of the layer (same Evrakçı tab, same
height), and ≡ and the search box move to its right end. Wayland compositors do not allow
reliable custom hit-testing or snap. KDE/GNOME users expect their own decorations, and
`QWindow.startSystemMove()` alone gives no resize edges or tiling. The status bar and everything
below are the same.

**Risk: medium. It is the single most fragile part of the build, so it is isolated in one module
(`ui/frame_win.py`) behind a flag.**
- Multi-monitor DPI changes (`WM_DPICHANGED`) and maximised windows: the frame inset differs when
  maximised (the window extends past the screen edge by the border width). Pad the title band by
  `GetSystemMetricsForDpi(SM_CYFRAME + SM_CXPADDEDBORDER)` when `IsZoomed`.
- Snap Layouts need `HTMAXBUTTON` exactly. A wrong rectangle silently disables the flyout. Test
  on 22H2+.
- Accessibility: caption buttons drawn by us must expose UIA names ("Simge durumuna küçült",
  "Ekranı kapla", "Kapat"). Keyboard Alt+Space must still open the system menu.
- Qt version drift: native-event signatures changed between Qt 6.5 and 6.8. Pin PySide6 and cover
  the hit-test map with a unit test (`hit_test(point) -> code`).
- **Fallback switch:** `Ayarlar > Görünüm > Windows başlık çubuğunu kullan` (also used
  automatically if any DWM call fails). The tabs then render as the first row of the layer, as on
  Linux, so the app keeps working with the stock frame.

## 8. Deviations (on top of the eight accepted with direction A)

9. Title-band tabs are text-only (no icons).
10. The job name and save state live in the status bar, as a job-switch button.
11. The selected tab is the Evrakçı trapezoid, not the Fluent rounded tab with feet.
12. The accent is split into `accent` (lines) and `accent-fill` (the filled primary). In dark,
    `accent-fill` is a deep green with white ink.
13. From 130 % text (one threshold) the left navigation panes collapse to their toggle, and
    status-bar priority-2 items are hidden (never clipped).
14. In HC, Kontrol takes the OS text colour (WindowText) in an outlined rider, not orange; the
    triangle and the word carry it. HC has no warning colour, and Hotlight is the link colour.
16. The job switcher in the status bar has no shortcut (Ctrl+O stays "Dosya ekle…").
17. The overview segments differ by height as well as colour (4 / 8 / 14 px).
15. Thumbnails default to 166 × 234 (status-bar zoom %112 of the 148 px base). Gate 7 is met at the
    default.

## 9. Gates (measured by `_render.py` and `_contrast.py`)

| Gate | Result |
|---|---|
| Chrome ≤ 120 px (Kontrol ≤ 150) | 44 + 44 + 28 = 116; Kontrol + overview 32 = 148 |
| No resting menu row | met. Alt or ≡ shows the floating row (`rehber-menu-*.png`). |
| ≤ 2 labels per command bar, icon buttons 36 px | Yükle 1, Kontrol 2, Şablonlar 2, Değerler 2, Dışa Aktar 1, Rehber 1 (+ Durdur / Okumayı iptal et while running) |
| One filled primary per state | met in all 23 states. Disabled primaries are grey, not green. |
| Page pixels ≥ 60 % (gate 7) | **64.0 %** at 166 × 234 with the inspector open (60.4 % at 130 % text) |
| Inspector ≤ 3 heading levels | title → group label → rows on every tab |
| Contrast (D10) | 0 failing pairs in light, dark and HC Black, Aquatic, Desert, Dusk, Night sky |
| No clipping, ellipsis, sideways scroll, spill out of cells/buttons, text < 13 px, element outside the window | **0 warnings** over 23 states × (light + 130 % + 150 %); dark, hc and the 6 Desert renders were checked by eye on the regenerated contact sheets |
| No overlay over the work | **0 overlap warnings**: no tooltip, toast, menu, palette or read-out covers the selected or edited row, a status cell or a filled primary |
| Contact sheets current | `_render.py` fails a full run when a `_sheet-*` is older than a render it shows |
| 1366 × 768 with no window scroll | met. Panes scroll inside, the window never does. |
| Real Lucide icons only | 76 icons from `lucide-static@0.460.0` via `_icons.py` |

## 10. How the loaded skills changed this round

| Skill | Change |
|---|---|
| `frontend-design` | "Spend boldness in one place": the trapezoid tab became the one signature, reused with meaning, not decoration. Removed middle-dot meta strings everywhere ("640 sayfa, dün", "İmleç x 84,5 y 41,0 mm"). Numbered markers only where the content is a sequence (Rehber steps, Yükle's 1-2-3, variables = box numbers). |
| `design-system` | New needs became tokens instead of literals: `accent-fill`, `ghost-edge`, `ghost-line`, `text-dis`, `brand-mark`, `on-paper-box`, plus the `--ts` text-size factor and the 150 % density step. The HC theme is a full token set, not overrides. |
| `anti-slop` | No pills on static metadata (counts are plain text). The search icon is the only icon inside fields. The manila step numbers in the empty state were replaced by neutral outlined circles (manila only for filed documents). No glass: the drop overlay is a flat tint with an opaque card. |
| `colour-palette` | 60-30-10 on the screenshots: `base` + `layer` about 60 %, cards and paper about 30 %, green + manila + orange under 10 %. Every list is a card with a frame and row lines. The dark primary was moved off the pastel. |
| `typography` | Weights 400/500/600. At most five sizes per screen. 24/32 is used once per screen at most. Body copy in the Rehber is held to 68 ch. |
| `spacing` | 4/8 grid. The page gap 12 / document gap 24 / row gap 12 rhythm makes stacks read without boxes. The only off-grid value is optical: the 0.4 px tab inset. |
| `ui-polish` (round 3) | Fixed the 32 findings in `REVIEW.md` within the system: new needs became tokens (`dis-ink`, `dis-alpha`, `kontrol-mark`, `--sys-*`), copy follows the registry word for word, and every fix was checked rendered in light, dark, HC, Desert, 130 % and 150 %. |
| `ui-polish` | Fixed only the judges' list and what the renders showed (overlapping tooltips, wrapped list meta at 150 %, duplicate Durdur, baseline of status + reason). Every fix was re-rendered and checked in all four renders. |

## 11. Open points for the owner

- Confirm deviation 10 (the job in the status bar). The alternative is the job as the first item
  of the command bar on every tab, which costs about 260 px of command space.
- The Linux fallback puts the tabs inside the layer. A Linux render can be produced if wanted.
- Confirm deviations 16 (no key on the job switcher) and 17 (overview segment heights).
- For the build, outside this folder: add the key-name override map (§4 "Key names") to
  `actions.key_text`; add an F9-style panel toggle to the registry only if wanted (the mockups no
  longer show F9); and reword the Ctrl+S row in `shortcuts.md` to "Kaydet (Şablonlar: şablonu
  kaydeder)" so the status bar's two save items match it.
- Check the four Windows 11 contrast-theme palettes in `tokens.css` once on Windows 11.
- Dark mode dims scans to `#e4e6e1`. An Ayarlar toggle "Sayfa önizlemelerini karart" can make
  this optional.
