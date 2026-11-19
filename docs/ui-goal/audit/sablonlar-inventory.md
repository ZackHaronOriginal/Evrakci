# Şablonlar audit: element inventory

Phase 4, Görev A, screen Şablonlar. Starts from `docs/ui-goal/research/inventory-sablonlar.md` (feature rows S-01..S-88, observations O-01..O-23). That file answers "what can the user do"; this one answers "what is on the screen". Each element has an ID `E-nnn`, which the other audit files use. "S-" names the research row. Code references are function and class names (the stable part); line numbers are given where a finding needs them (`sablonlar-findings.md`). Working tree: the files under `src/evrakci/ui/` as they stood on 2026-11-19 with no change of mine (another agent edits Kontrol code and tests in parallel; ignored).

Element count: **116 numbered elements** in 9 groups (6 shared chrome, 12 command bar, 21 left column, 7 example bar, 22 page well and canvas, 22 inspector, 6 empty states, 10 status bar, 10 dialogs / toasts / system surfaces). Keys, pointer gestures and drags are not elements: they are in `sablonlar-paths.md`. The OS-drawn surfaces (the taskbar progress, native dialogs) are listed so their states are accounted for, but only the Qt side of them could be driven offscreen.

Screen states of Şablonlar (each has its own set of visible elements): **no template** (empty state "Henüz şablon yok", cards and inspector gone), **template but no job** (empty state "Örnek sayfa yok", inspector still shown), **template without a variable** (page shown, inspector "Değişken yok"), **variable without a box** (inspector "Henüz kutu yok"), **box chosen** (inspector "Kutu i / k"), **Kutu çiz on**, **Okumaları sayfada göster on**, **reading** ("Okunuyor…"), **try-all running** (status text, command disabled), **save failed** (message and status), **example file missing** (read and render failure).

Demo data: `tools/screenshots.py:build` (3 documents of 3, 2 and 2 pages... 15 pages, 2 templates) for the default states, plus the synthetic long-content cases built for this audit (all invented, in the session's scratchpad, never committed): `long` (a template with a 110-character name, 40 variables of which one has a 110-character unbroken name and several have 40-character spaced names, 7 variables with 3 sections each, one with 31 sections, a 3-page example, 30 more templates named "Şablon numara NN" with 0 to 4 repeated words), `reads` (a fake engine returning 150 unbroken characters, 500 characters in 12 lines, 5,000 characters), `docs` (a job of 151 documents, the first 120 pages long), `off` (boxes at 400..460 and 200..260 mm on a 210 x 297 mm sheet), `damaged` (six unreadable template files), `gone` (an example PDF renamed away). Screenshots: `/tmp/claude-0/p4/sablonlar/states/<tag>-<name>.png` with tags `light100`, `dark150`, `hc100`, `hc150` (theme and text size); the names are used as `S:<name>` in the other files.

Tab order measured by `keywalk.py --tab sablonlar` (identical in light, dark, hc, 100, 115, 130 and 150 percent, 1366x768 and 1920x1080, 24 of 24 clean): title tabs, job switch, search box, menu button, command bar (Geri al and Yinele only when enabled; Kutu çiz, Izgaraya oturt, Kutuyu çoğalt, Kutuyu sil, Değişken ekle, Bütün örneklerde dene, Okumaları sayfada göster, Ayrıntı panelini gizle, Diğer komutlar), the two plus buttons, the template list (one stop), the variable list (one stop), Örnek, Sayfa, the canvas (one stop), the inspector's "Diğer", Ad, Zorunlu, the page field, the four millimetre fields, the pattern field, Şablonu kaydet, the status-bar zoom minus, slider and plus, back to the title tabs. Not in the order: the splitter handles (mouse only), the rulers, the message label, the footnote.

## 0Shared chrome visible on Şablonlar (audited once in `kontrol-inventory.md` E-001 to E-006)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-001 | Tab strip Yükle / Kontrol / Şablonlar / Değerler / Dışa Aktar / Rehber | TitleTabs (QTabBar) | `ui/chrome.py:TitleTabs` | S-85 | Şablonlar is the third tab; at 150 % text and 1366 wide the tabs after Şablonlar go into a "»" menu (F-yukle-23 applies) |
| E-002 | Job switch (job name, save state) | JobSwitch | `ui/titlebar.py` | none | shows the job, not the template; "İş açılmadı" when no job |
| E-003 | Search box "Ara  Ctrl+K" | SearchBox | `ui/palette.py` | S-66 | opens the palette; lists every sablonlar.* command except the three key groups |
| E-004 | Menu button (Düzen, Görünüm, Git, Araçlar) | QToolButton | `ui/titlebar.py` | S-66 | Düzen holds Kutuyu sil, çoğalt, Değişken ekle, taşı; Görünüm Okumaları göster; Araçlar Kutu çiz, Izgara, Dene |
| E-005 | Caption buttons | CaptionButton x3 | `ui/titlebar.py` | none | NoFocus by design |
| E-006 | Window title / drag area | TitleBand | `ui/titlebar.py` | none | not exercised |

## Command bar

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-007 | Geri al | ActionButton | `main_window.py:COMMANDS['sablonlar']`, action `app.geri_al` | S-68 | template stack, not the job's (`undo_target`, main_window.py:987) |
| E-008 | Yinele | ActionButton | same, `app.yinele` | S-68 | disabled until something was undone |
| E-009 | Kutu çiz (labelled, toggle, B) | ActionButton, checkable | `sablonlar.kutu_ciz` | S-43 | checked while the tool is on; needs a page |
| E-010 | Izgaraya oturt (toggle, G) | ActionButton, checkable | `sablonlar.izgara` | S-48 | icon only; tooltip "Izgaraya oturt (G)" |
| E-011 | Kutuyu çoğalt (Ctrl+D) | ActionButton | `sablonlar.kutu_cogalt` | S-26 | needs a chosen box and a page |
| E-012 | Kutuyu sil / Değişkeni sil (Del) | ActionButton | `sablonlar.kutu_sil`; text switched in `sablon_sync.py:_sync_actions` | S-19, S-27 | name and tooltip change with what is chosen |
| E-013 | Değişken ekle (Ctrl+Shift+N) | ActionButton | `sablonlar.degisken_ekle` | S-13 | enabled whenever a template is open |
| E-014 | Bütün örneklerde dene (labelled, Ctrl+T) | ActionButton | `sablonlar.dene` | S-57 | disabled while it runs and with no page |
| E-015 | Okumaları sayfada göster (toggle) | ActionButton, checkable | `sablonlar.okumalari_goster` | S-50 | icon only (eye) |
| E-016 | Ayrıntı panelini gizle (F9) | ActionButton | `app.yan_panel` | S-64 | not remembered between sessions (S-87) |
| E-017 | Diğer komutlar (overflow) | QToolButton + menu | `chrome.py` command bar | S-65 | holds what does not fit at 150 % text |
| E-018 | Separators and the grow spacer (3) | QFrame | command bar | none | not focusable |

## Left column: templates and variables (`sablon_nav.py`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-019 | Column scroll area "Şablonlar ve değişkenler" | NavPane (QScrollArea) | `sablon_nav.py:NavPane` | S-01, S-12 | vertical scroll only; horizontal off |
| E-020 | Group label "Şablonlar" | QLabel group-label | `NavPane._group` | S-01 | not focusable |
| E-021 | Plus button "Şablon ekle" | QToolButton | `NavPane._plus` | S-02 | opens the name dialog; no shortcut of its own |
| E-022 | Template card | QFrame card | `NavPane._card` | S-01 | laid out at the height of all its rows |
| E-023 | Template list "Şablonlar" | TemplateList (QListWidget) | `sablon_nav.py:TemplateList` | S-01, S-03 | arrow keys open each template at once |
| E-024 | Template row: open (selected), name left, "N değişken" right | NavDelegate | `NavDelegate.paint` | S-01 | 3 px accent bar; hc fills with accent |
| E-025 | Template row: hover | NavDelegate | same | S-01 | fill `hover`; hc outline |
| E-026 | Template row: focus ring | paint_ring | same | S-01 | drawn inside the row |
| E-027 | Template row: "kaydedilmedi" value | NavDelegate | `SablonScreen._refresh_template_row` | S-06 | replaces "N değişken" while an edit is unsaved |
| E-028 | Template row tooltip and spoken text | ToolTipRole / AccessibleTextRole | `_row` | S-73 | "Şablon {ad}, {n} değişken"; carries the full name when the row elides |
| E-029 | Group label "Değişkenler" | QLabel group-label | `_group` | S-12 | not focusable |
| E-030 | Plus button "Değişken ekle" (Ctrl+Shift+N) | QToolButton | `NavPane._plus` | S-13 | disabled with the tip "Önce bir şablon oluşturun" while no template exists |
| E-031 | Variable card | QFrame card | `_card` | S-12 | full height of all rows; empty and blank when the template has no variable |
| E-032 | Variable list "Değişkenler ve bölümler" | VariableTree (QTreeWidget) | `sablon_nav.py:VariableTree` | S-12 | internal drag and drop reorders; focusable even when empty |
| E-033 | Variable row: number badge, name, " *", "N bölüm" or "kutu yok" | NavDelegate | `NavDelegate._badge`, `VariableTree.fill` | S-12 | a variable with one box is one row |
| E-034 | Section row: grip, "Bölüm k", "Sayfa p" or "son sayfa" | NavDelegate | `VariableTree.fill` | S-12, S-25 | only from two sections on |
| E-035 | Row grip (drag handle look) | icon | `NavDelegate.paint` | S-18, S-25 | the whole row drags, not only the grip |
| E-036 | Drop indicator while dragging | Qt drop indicator | `VariableTree` | S-18 | `dropEvent` never lets Qt move the rows |
| E-037 | Variable and section row tooltip / spoken text | ToolTipRole | `VariableTree.fill` | S-73 | "Değişken 2: Ad, zorunlu, 1 kutu" |
| E-038 | Message label (icon + red text) | MessageLabel | `sablon_nav.py:MessageLabel` | S-14, S-59 | every refusal of this tab lands here; hidden when empty; no live-region announcement |
| E-039 | Footnote under the cards | QLabel caption | `NavPane.foot`, `set_empty` | S-71 | three texts: normal, no template, template without variable |

## Example bar above the page (`sablon.py:_centre`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-040 | Label "Örnek" | QLabel | `sablon.py` | S-35 | buddy of the picker |
| E-041 | Picker "Örnek belge" | QComboBox | `sablon.py` | S-35 | "Örnek N, sayfa P"; after try-all " · N kontrol" and a warning icon |
| E-042 | Picker popup items | QComboBox view | `_mark_example_checks` | S-57 | maxVisibleItems 10 (Qt default) |
| E-043 | Label "Sayfa" | QLabel | `sablon.py` | S-36 | buddy of the picker |
| E-044 | Picker "Örnek sayfa" | QComboBox | `sablon.py` | S-36 | "1 / N" |
| E-045 | Picker popup items (pages) | QComboBox view | `_fill_pages` | S-36 | up to the document's page count |
| E-046 | The bar itself (52 px) | QWidget | `BAR_H` | none | hidden in the empty states |

## Page well, rulers and canvas (`sablon_rulers.py`, `sablon_canvas.py`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-047 | Well frame | CanvasWell | `sablon_rulers.py:CanvasWell` | S-39 | holds both rulers and the canvas |
| E-048 | Horizontal ruler "Cetvel, yatay (mm)" | Ruler | `sablon_rulers.py` | S-41 | ticks follow zoom and scroll |
| E-049 | Vertical ruler "Cetvel, dikey (mm)" | Ruler | same | S-41 | numbers read bottom-up |
| E-050 | Ruler extent bar of the chosen box (x2) | Ruler paint | `CanvasWell.set_extent` | S-41 | also when the box lies off the sheet |
| E-051 | Ruler corner | QWidget | `CanvasWell` | S-41 | blank |
| E-052 | Canvas "Örnek sayfa" (focus stop) | PageCanvas (QGraphicsView) | `sablon_canvas.py:PageCanvas` | S-39, S-51 | StrongFocus; accessible description changes with the chosen box |
| E-053 | Canvas viewport | QWidget | Qt | none | counted by two measure rules (F-sablonlar-22) |
| E-054 | Sheet: scan, hairline, paper shadow | PageItem | `PageItem` | S-39 | painted, not styled |
| E-055 | Vertical and horizontal scroll bars | QScrollBar | Qt | S-39 | vertical shows at fit width (A4 portrait is taller than the well) |
| E-056 | Box: default (first section) | BoxItem | `BoxItem.paint` | S-28 | 2 px outline |
| E-057 | Box: variant (dashed; later section or other example) | BoxItem | same | S-28 | dashes also mean "drawn on another example" (O-07) |
| E-058 | Box: chosen (paper halo, four corner handles) | BoxItem | same; `HANDLE` | S-28 | handles 7 px, hit 8 px |
| E-059 | Box number badge | BoxItem | `BoxItem._badge` | S-28 | the variable's number; all its sections carry it |
| E-060 | Box focus ring (D11, double ring) | focus ring overlay | `PageCanvas._sync_ring` | S-51 | only for keyboard focus |
| E-061 | Reading card under a box (text, warning icon) | BoxItem._reading | `sablon_canvas.py` | S-50 | width grows with the text, no maximum |
| E-062 | Rubber band while drawing | QGraphicsRectItem | `mousePressEvent` | S-43 | dashed, 2 px cosmetic |
| E-063 | Cursor: arrow / cross / size-all / two diagonals / open hand / closed hand | viewport cursor | `_hover_cursor` | S-39, S-43 | by state and position |
| E-064 | Tooltip over a box | QToolTip | `viewportEvent` | S-39 | "N. ad, bölüm k" |
| E-065 | Tooltip over the bare sheet | QToolTip | same | S-39 | how to draw |
| E-066 | Context menu on a box and on a variable row | QMenu "Kutu komutları" | `SablonScreen.box_menu`, `_variable_menu`, `_canvas_menu` | S-52 | Kutuyu çoğalt, Kutuyu sil, Değişkeni yukarı, aşağı taşı, Değişken ekle |
| E-067 | Context menu on the bare sheet | QMenu | `PAGE_MENU` | S-52 | Kutu çiz, Izgaraya oturt, Okumaları sayfada göster |
| E-068 | Hand tool while Space is held | cursor | `keyPressEvent` | S-39 | open hand; Space+drag pans |

## Inspector panel (`sablon_inspector.py`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-069 | Panel "Kutu ayrıntısı" and its scroll area "Ayrıntılar" | InspectorPanel, QScrollArea | `sablon_inspector.py` | S-63 | scroll area has NoFocus; no horizontal scroll |
| E-070 | Top label "Kutu i / k" / "Değişken i / n" | QLabel secondary | `_head` | S-63 | hidden text in state none |
| E-071 | Button "Kutu için diğer komutlar" (…) | QToolButton + menu | `_head` | S-52 | opens the box menu; focus stop |
| E-072 | Title (variable name) | ElidedLabel (min 8 characters) | `_head` | S-63 | tooltip carries the full name |
| E-073 | Sub line ("Bölüm i, sayfa p", "k bölüm", "Henüz kutu yok", hints) | QLabel | `_head` | S-63 | no word wrap (F-sablonlar-03) |
| E-074 | Group label "Kutu" and its card | QLabel + QFrame | `_box_group` | S-63 | hidden in state none |
| E-075 | Label "Ad" and field "Değişken adı" | QLineEdit | `_box_group` | S-15 | commits on Enter or focus out |
| E-076 | Check box "Zorunlu" | QCheckBox | `_box_group` | S-16 | undoable |
| E-077 | Label "Kutunun sayfası" and spin | PageSpin | `PageSpin` | S-29 | 1 to 999 or "son"; hidden in variable mode |
| E-078 | Label "X, Y, genişlik, yükseklik (mm)" | QLabel | `_box_group` | S-49 | buddy of the first spin |
| E-079 | Four mm fields (Kutu X, Y, genişliği, yüksekliği) | MmSpin x4 | `MmSpin` | S-49 | Turkish comma, no buttons; ranges independent (B-016) |
| E-080 | Hint line ("Sayfada Kutu çiz (B)…", "Bir bölüm seçin…") | QLabel (word wrap) | `_box_group` | S-20 | hidden when empty |
| E-081 | Group label "Okunan, örnek N" and its card | QLabel + QFrame | `_read_group` | S-54 | title includes the example number |
| E-082 | Row "Değer": value | QLabel (word wrap, selectable) | `_read_group` | S-54 | font `value`; no maximum height or width (F-sablonlar-01, 02) |
| E-083 | Row "Güven": icon, level word, percent | LevelWidget | `LevelWidget` | S-55 | Emin, Orta, Kontrol, Okunamadı, Okunmadı; never colour alone |
| E-084 | Row "Not": read note | QLabel (word wrap) | `_read_group` | S-56 | hidden when empty |
| E-085 | Busy text "Okunuyor…" | read_value text | `_show_read` | S-54 | after 150 ms |
| E-086 | Group label "Dosya adı" and its card | QLabel + QFrame | `_pattern_group` | S-31 | always visible when a template is open |
| E-087 | Pattern field "Dosya adı kalıbı" (placeholder, tooltip) | QLineEdit | `_pattern_group` | S-31 | placeholder contrast fails (F-sablonlar-20) |
| E-088 | Suffix ".pdf" | QLabel | `_pattern_group` | S-31 | fixed |
| E-089 | Pattern error line | QLabel (word wrap, state bad) | `set_pattern_error` | S-32 | gone at the next key; no icon (word only) |
| E-090 | Button "Şablonu kaydet" (Ctrl+S, primary, pinned) | QPushButton | `InspectorPanel.__init__` | S-07 | disabled with no template |

## Empty states (`sablon_empty.py`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-091 | Empty state "Henüz şablon yok": mark, heading, sentence | EmptyState | `sablon_sync.py:_sync_state` | S-71 | centred in the well |
| E-092 | Button "Yeni şablon oluştur" (primary) | QPushButton | `sablon_empty.py:show_state` | S-02, S-71 | same as the + button |
| E-093 | Button "Rehber'i aç" | QPushButton | same | S-71 | goes to the Rehber tab |
| E-094 | Note naming the job (or telling to open one) | QLabel (word wrap) | `sablon_sync.py` | S-71 | a long unbroken job name widens the column (F-sablonlar-28) |
| E-095 | Empty state "Örnek sayfa yok": mark, heading, sentence | EmptyState | `sablon_sync.py` | S-71, S-37 | also shown when the example's file is missing (F-sablonlar-18) |
| E-096 | Button "Yükle'ye git" (primary) | QPushButton | same | S-37 | goes to the Yükle tab |

## Status bar slot (`sablon.py:attach`, `sablon_sync.py:_sync_status`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-097 | "Örnek n / N" | StatusPart | `sablon_sync.py` | S-69 | hidden without a page |
| E-098 | "Kutu x … y … mm" (box with focus) | StatusPart | `sablon_sync.py` | S-69 | replaces the cursor part while the canvas has focus |
| E-099 | "Kaydır: ok tuşları 0,25 mm, Shift 1 mm" | StatusPart | `sablon_sync.py` | S-69 | with the box part |
| E-100 | "İmleç x … y … mm" | StatusPart | `sablon_sync.py` | S-42 | "x —  y —" when the pointer is off the sheet |
| E-101 | Save state: icon + "Şablon seçilmedi / kaydedilmedi / kaydedilemedi / kaydedildi HH:MM" | StatusPart | `sablon_sync.py` | S-69 | icon and word; not colour alone |
| E-102 | "N okuma kontrol bekliyor" (warning icon) | StatusPart | `sablon_sync.py` | S-58 | hidden when 0 |
| E-103 | Zoom minus button | ZoomSlider part | `ui/widgets.py:ZoomSlider` | S-40 | 24 px (F-sablonlar-21) |
| E-104 | Zoom slider "Sayfa yakınlaştırma düzeyi" | QSlider | same | S-40 | 25 to 400, steps of 10 |
| E-105 | Zoom plus button | ZoomSlider part | same | S-40 | 24 px |
| E-106 | Zoom percent label "%87" | QLabel | same | S-40 | hidden in the empty states |

## Dialogs, toasts and system surfaces

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-107 | Name dialog "Yeni şablon": label "Şablonun adı", field, Oluştur, Vazgeç | QInputDialog | `sablon.py:_ask_text`, `new_template` | S-02 | blank name or Vazgeç do nothing and say nothing (O-17) |
| E-108 | Name dialog "Değişken ekle": label "Değişkenin adı (örn. Firma_Adi)", Ekle, Vazgeç | QInputDialog | `ask_variable` | S-13 | same dialog class |
| E-109 | Toast "Şablon kaydedildi." (success) | Toast | `save` | S-07 | 6 s |
| E-110 | Toast "“X” değişkeni silindi (N kutu)." + Geri al | Toast | `delete_selected` | S-19 | 10 s; Geri al acts only on the newest step |
| E-111 | Toast "“X” değişkeninin N. bölümü silindi." + Geri al | Toast | `delete_selected` | S-27 | 10 s |
| E-112 | Toast "N örnekte denendi. …" (success or Kontrol) | Toast | `sablon_live.py:_all_done` | S-57 | no button |
| E-113 | Toast close (x) button | Toast | `feedback.py` | none | shared with the other tabs |
| E-114 | Taskbar progress during try-all | OS taskbar | `ui/taskbar.py` via `_all_progress` | S-57 | not drivable offscreen |
| E-115 | Palette entries (sablonlar.*) | Palette | `ui/palette.py` | S-66 | Ctrl+K |
| E-116 | Shortcut sheet rows (B, G, Ctrl+T, Del, Ctrl+D, Ctrl+Shift+N, Alt+arrows, arrows, Space) | Shortcut sheet | `ui/shortcut_sheet.py` | S-75 to S-85 | Shift+F1 |
