# Değerler audit: element inventory

Phase 4, Görev A, screen Değerler. Starts from `docs/ui-goal/research/inventory-degerler.md` (feature rows V-01..V-99, observations O-01..O-24). That file answers "what can the
user do"; this one answers "what is on the screen". Each element has an ID `E-nnn`, which the other audit files use. "V-" names the research row. Code references are checked
against the working tree on 2026-11-19 (function and class names are the stable part; HEAD a5c1d97, no uncommitted change in `src/` when this was written).

Element count: **134 numbered elements** in 12 groups (6 shared chrome, 12 command bar, 7 progress and message band, 14 card header, 33 table, 6 sample mode, 7 empty states, 20 side panel, 4 page view, 8 menus, 8 status bar, 9 toasts / dialogs / system surfaces). Keys, pointer gestures and drags are inputs,
not elements: they are in `degerler-paths.md`. The OS-drawn surfaces (taskbar progress, the window-flash alert, native tooltips) are listed so their states are
accounted for, but only the Qt side of them could be driven offscreen.

Screen states of Değerler (each has its own set of visible elements): **no job** (empty state), **job without a templated document** (empty state), **templated documents,
nothing read** (empty state, header row still drawn), **table** (the normal state: Kontrol gerekenler / İncelenmemiş / Tümü), **empty view** (Kontrol gerekenler or
İncelenmemiş with nothing in it), **search without a match**, **Tümünü incele** (mode), **Örnek kontrol** (mode, its own five columns), **reading** (progress band),
**read finished** (toast), **read refused or failed** (message band), **cell editor open**, **page view open** (loupe overlay).

Demo data: `tools/screenshots.py:build` (3 documents, 2 variables, one flagged value) for the default states; the synthetic long-content jobs built for this audit:
`real300` (300 documents x 8 variables, homogeneous columns, long company names, a 260-character note, an 78-character unbroken code, empty and flagged values), `mixed60`
(60 documents, mixed column content), `longtpl` (a 120-character template name), `cols48` (52 columns), `notread` (60 documents, nothing read). All in
`/tmp/claude-0/p4/degerler/longroots/` (synthetic, never committed).

Tab order measured by `keywalk.py --tab degerler` (identical in light, dark, hc, 100, 115, 130 and 150 percent, 1366x768 and 1920x1080, 24 of 24 clean): title tabs, job
switch, search box, menu button, command bar (Geri al, Değerleri oku, Yalnızca eksikleri oku, Tümünü incele, Örnek kontrol, Önceki kontrol, Sonraki kontrol, Seçilenleri onayla,
Kaynak panelini gizle, Diğer komutlar; Yinele is disabled and so out of the order), the selected view item (one stop for the whole switch), the search field, the template
picker, the table (every value cell is a stop: 240 presses to cross a 30 x 8 table, P-036 in the paths file), the three crop buttons, Onayla ve sonrakine geç, Elle yaz,
Yeni kutu çiz, the status-bar zoom minus, slider and plus, back to the title tabs. Not in the order: the splitter handle (mouse only, F-degerler-25), the clear (x) button
in the search field (by design, Esc clears), the status items, the page view's own controls while it is closed, the toast and its buttons.

## 1. Shared chrome visible on Değerler (audited once in `kontrol-inventory.md` E-001 to E-006; Değerler-specific facts here)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-001 | Tab strip Yükle / Kontrol / Şablonlar / Değerler / Dışa Aktar / Rehber | TitleTabs (QTabBar) | `ui/chrome.py:TitleTabs` | V-86 | Değerler is the fourth tab; at 150 % text and 1366 wide the tabs after it go into a "»" menu (F-yukle-23 applies) |
| E-002 | Job switch (name, save state "Kaydedildi 15:02") | JobSwitch, ElidedLabel | `ui/titlebar.py` | none | no job: "İş açılmadı"; a long job name is elided by the widget itself (39 clipping lines at 150 %, same as F-yukle-23) |
| E-003 | Search box "Ara  Ctrl+K" | SearchBox | `ui/palette.py` | V-86 | opens the command palette; lists every degerler.* command |
| E-004 | Menu button | QToolButton | `ui/titlebar.py` | V-84 | Düzen, Görünüm, Git, Araçlar (E-100 to E-103) |
| E-005 | Caption buttons | CaptionButton x3 | `ui/titlebar.py` | none | NoFocus by design |
| E-006 | Window title / drag area | TitleBand | `ui/titlebar.py` | none | not exercised |

## 2. Command bar (Değerler)

`ui/main_window.py` (COMMAND_BARS "degerler", L115 to L121), actions in `ui/actions.py` (L300 to L331). Buttons mirror QActions; the two read commands also have hidden
screen buttons (E-011, E-012) that carry their slots and enabled state.

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-010 | Geri al (icon, "Geri al: <step> (Ctrl+Z)") | ActionButton | `actions.py app.geri_al` | V-64 | in the tab order; after a read the step is "Değerleri oku" |
| E-011 | Yinele (icon) | ActionButton | `actions.py app.yinele` | V-64 | disabled until something is undone, so out of the tab order |
| E-012 | Değerleri oku (icon + label) | ActionButton | `actions.py degerler.oku`; slot `degerler.py:read_values` | V-01 | tooltip and accessible name "Şablonu olan bütün belgeleri yeniden oku" (not the label); disabled while reading |
| E-013 | Yalnızca eksikleri oku (icon) | ActionButton | `degerler.eksikleri_oku` | V-02 | disabled until something is read and while reading; name = tooltip |
| E-014 | Tümünü incele (icon, checkable) | ActionButton | `degerler.tumunu_incele` -> `set_review_all` | V-67 | accessible name "Emin olanlar dahil her değeri sırayla göster": the command name is only in the menu (F-degerler-31) |
| E-015 | Örnek kontrol (icon, checkable) | ActionButton | `degerler.ornek_kontrol` -> `set_sample` | V-68 | accessible name "Dışa aktarmadan önce rastgele 20 emin değere bak" (F-degerler-31) |
| E-016 | Önceki kontrol (icon, Shift+N) | ActionButton | `degerler.onceki_kontrol` | V-51 | works (lambda with step -1) |
| E-017 | Sonraki kontrol (icon + label, N) | ActionButton | `degerler.sonraki_kontrol` -> `degerler.py:next_check` | V-51 | **jumps to the first Kontrol value, not the next one** (F-degerler-01) |
| E-018 | Seçilenleri onayla (icon, Ctrl+Enter) | ActionButton | `degerler.secilenleri_onayla` -> `accept_selected` | V-58 | enabled with at least one selected row |
| E-019 | Kaynak panelini gizle / göster (F9) | ActionButton | `main_window.py` panel toggle | V-79 | tooltip flips to "göster"; double click ends where it began (P-122) |
| E-020 | Diğer komutlar (…) | QToolButton moreButton | `ui/chrome.py` | V-81 | menu: Tümünü seç, Onayla ve sonrakine geç, Elle yaz, Yeni varyant çiz, Vazgeç, Tüm sayfayı göster (what does not fit) |
| E-021 | Two group separators and a flexible gap | CommandBar items | `main_window.py L115-121` | V-81 | decoration, not exercised |

## 3. Progress and message band (an InfoBar above the card)

`degerler.py` L171 to L200. Hidden until a read starts or a message must stay; the same widgets show progress, then one message, until closed.

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-030 | Band frame (kind "infobar") | QFrame | `degerler.py:progress_band` | V-08, V-15 | at 150 % and 1024x600 the label is elided (RD-081/082, F-degerler-28) |
| E-031 | Status icon (circle-check, info, triangle-alert) | QLabel pixmap | `progress_icon` | V-14 | hidden while reading |
| E-032 | Label "Okunuyor: 3 / 12 belge", or the final message | QLabel (body-strong) | `progress_label` | V-08 | never wraps: a long message is cut by the band |
| E-033 | Progress bar, 240 px, determinate, no text | QProgressBar "Okuma ilerlemesi" | `progress` | V-08 | static between steps; no animation (motion file) |
| E-034 | Hint "bir dakikadan az kaldı, elle yazdıklarınız korunur" | QLabel (secondary) | `progress_hint` | V-08 | the time estimate is "yaklaşık N dk kaldı" from one minute |
| E-035 | Okumayı durdur (Ctrl+.) | QPushButton | `cancel_button`; `degerler.py:cancel` | V-09 | visible only while reading; in the tab order; no visible reaction after the click (F-degerler-07) |
| E-036 | Mesajı kapat (x) | QPushButton, subtle | `dismiss_button` | V-15 | visible only when no task runs; mouse and Tab |

## 4. Card header: view switch, search, template picker

`degerler_parts.py` (HeaderBar L244, ViewSelector L107, SelectorItem L30); `degerler.py` L221 to L238.

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-040 | Card header (52 px, 64 px from 130 % text, 96 to 112 px when it wraps) | HeaderBar | `degerler_parts.py:HeaderBar` | V-47 | one, two or three lines by room; a long template name takes the whole second line (F-degerler-19) |
| E-041 | View switch "Görünüm" | ViewSelector | `degerler_parts.py:ViewSelector` | V-37 | one Tab stop, Left/Right move (wrap), counts in the accessible name |
| E-042 | Item Kontrol gerekenler + count | SelectorItem | `SelectorItem` | V-38 | count is the number of values (206 in `real300` at 60 documents), not documents |
| E-043 | Item İncelenmemiş + count | SelectorItem | `SelectorItem` | V-39 | |
| E-044 | Item Tümü + count | SelectorItem | `SelectorItem` | V-40 | default view |
| E-045 | Item Örnek + count (only while the sample is open) | SelectorItem | `SelectorItem` | V-68 | hidden otherwise |
| E-046 | Selected-item pill (16 x 3 accent under the label) | painted in `SelectorItem.paintEvent` | `degerler_parts.py L89-L93` | V-37 | instant, no animation (checked) |
| E-047 | Search field (placeholder names the first text-like variable) | QLineEdit "Değerlerde ara" | `degerler.py:search` | V-41 | disabled while nothing is read; Esc clears; one placeholder only whatever the number of columns it searches (F-degerler-18) |
| E-048 | Search leading icon (22 x 18, 26 x 22 at 150 %) | QToolButton from `addAction` | `degerler.py:_search_icon` | V-41 | rules AUD-HIT-01, AUD-HIT-02, HIG-CTL-06 fail (F-degerler-22, same as F-yukle-26) |
| E-049 | Search clear button "Temizle" | ClearButton / QToolButton | `ui/widgets.py:ClearButton` | V-41 | declared 24 x 24, measured 38 x 38 in a 32 px field, sits low over the border (F-degerler-11) |
| E-050 | Template picker (drop-down, placeholder "Şablon yok") | SlackComboBox, accessible name "Şablon" | `degerler.py:template_combo` | V-43 | hidden in Örnek; sized to its longest item; a 120-character name takes up to 918 px (F-degerler-19) |
| E-051 | Template picker popup list | QComboBox popup | Qt | V-43 | one item per template used by the job, sorted by name; "Şablon bulunamadı" for a deleted one |
| E-052 | Card frame (kind "table-card") with its 1 px outline | QFrame "Değerler tablosu" | `degerler.py:card` | none | |
| E-053 | Splitter between card and side panel | QSplitter "degerler" | `degerler.py:splitter` | V-44, V-79 | handle 4 px, mouse only; panel may take 890 px, table keeps 428 (P-123 to P-124) |

## 5. Table (main views)

`degerler_table.py`. One delegate paints every cell; no widget per row.

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-060 | Table view "Değerler tablosu" | ValuesTable (QTableView) | `degerler_table.py:ValuesTable L718` | V-17, V-48 | extended selection of whole rows, Tab walks value cells |
| E-061 | Header row (36 px, hairline below) | ValuesHeader | `degerler_table.py:ValuesHeader L634` | V-45, V-46 | sort by click, resize by dragging the edge; sections not movable |
| E-062 | Header: review mark (check-circle icon) | header section 0 | `main_columns` | V-19 | tooltip and spoken name "İnceleme" |
| E-063 | Header: Belge (right aligned) | header section | `main_columns` | V-20 | sort by number |
| E-064 | Header: Sayfa | header section | `main_columns` | V-20 | sort by page position |
| E-065 | Header: one per variable (name with "_" as space) | header sections | `main_columns` | V-18 | elided when narrow ("Organize S...", `real300` 3 of 8); tooltip carries the full title |
| E-066 | Header: Güven | header section | `main_columns` | V-32 | last column; the only place that spells the level word and percent (F-degerler-10) |
| E-067 | Sort chevron (16 px) | painted | `ValuesHeader.paintSection` | V-45 | only on the sorted column |
| E-068 | Column edge (resize handle) | header edge | Qt | V-46 | floor 40 px; widths saved per template; no reset (F-degerler-13) |
| E-069 | Row: review mark cell (check icon when all read values are İncelendi) | delegate cell | `ValuesDelegate.paint` | V-19 | spoken "İncelendi" / "İncelenmedi" |
| E-070 | Row: Belge cell (number, right aligned) | delegate cell | `ValuesDelegate.paint` | V-20 | |
| E-071 | Row: Sayfa cell ("1–3", "7") | delegate cell | `ValuesDelegate.paint` | V-20 | |
| E-072 | Value cell, level Emin (text, no marker) | delegate cell | `degerler_table.py:_value L580` | V-27 | the level is not written in the cell; it is read from the Güven column or the inspector |
| E-073 | Value cell, level Orta | delegate cell | `_value` | V-28 | identical to Emin in the cell; only the Güven column tells (F-degerler-10) |
| E-074 | Value cell, level Kontrol (uncertain characters with wash and 2 px underline) | delegate cell, `paint_marked L340` | `_value` | V-22, V-29 | underline alone in hc and on a selected row |
| E-075 | Value cell, level Okunamadı ("boş", grey) | delegate cell | `_value L586` | V-23, V-30 | |
| E-076 | Value cell, level Okunmadı (blank) | delegate cell | `_value` | V-31 | variable added after the read, or a failed document (F-degerler-05) |
| E-077 | Value cell text kinds: code / number (right aligned) / date / text | delegate cell | `degerler_model.py:column_kind L81` | V-18 | decided per column from its texts; a mixed column is "text" and wraps numbers too |
| E-078 | Wrapped text, at most 3 lines, last line elided | delegate cell | `ValuesDelegate.row_height L505`, `wrap_lines L320` | V-21 | the full text only through the tooltip (E-091) and the inspector |
| E-079 | Güven cell (level icon, word, percent) | delegate cell, `paint_level L412` | `ValuesDelegate.paint` | V-32 | worst level of the row; "Kontrol" word fails DEC-CON-01 in dark (F-degerler-17) |
| E-080 | Row selection fill + 3 px accent bar on the first column | delegate | `ValuesDelegate.paint` | V-26 | hc: highlight colours |
| E-081 | Current-cell focus ring (double ring) | delegate `_focus_ring L596` | `ValuesDelegate` | V-26 | drawn on the current value cell only |
| E-082 | Row hover fill | delegate | `ValuesDelegate.paint` | none | |
| E-083 | Vertical scroll bar | QScrollBar | Qt | V-89 | per-pixel scrolling |
| E-084 | Horizontal scroll bar | QScrollBar | Qt | V-46 | appears from the 6th variable at 1366 wide and 100 % (104 px of range, 314 px at 8 variables) and from the 3rd at 150 %; the Güven column is in that range (F-degerler-10) |
| E-085 | In-place cell editor | QLineEdit (delegate editor) | `ValuesDelegate.createEditor L607`, accessible name "<variable> düzenle" | V-59, V-60 | starts with the suggestion or the value, caret at the end; no length limit, accepts empty text (F-degerler-04) |
| E-086 | Key hint chip under the editor ("Enter onayla, sonraki kontrol   Esc vazgeç") | KeyHint QLabel | `degerler_table.py:KeyHint L691` | V-59 | text from `degerler.py:_hint_keys L885` |
| E-087 | Cell tooltip ("Öneri: ..." or the whole text) | tooltip | `ValuesModel.data` ToolTipRole | V-24 | |
| E-088 | Header tooltip (column title; "İnceleme" for the mark) | tooltip | `ValuesModel.headerData` | V-18 | |
| E-089 | Spoken text of a cell ("Sicil No: 482I3, Kontrol, 1 karakter belirsiz") | AccessibleTextRole | `ValuesModel._spoken L221` | V-25 | |
| E-090 | Row-height pass (rows grow for wrapped text) | `ValuesTable.fit_rows L784` | `degerler_table.py` | V-21 | one pass per burst; 1,000 documents stay under 1.5 s (V-89) |
| E-091 | Accessible name of the table | "Değerler tablosu" | `ValuesTable`, `card` | V-25 | |
| E-092 | Table stays visible during a read | n/a | `degerler.py:_set_busy` | V-08 | but it shows the rows read before; new results appear only when the read ends (F-degerler-33) |

## 6. Örnek kontrol table (sample mode)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-100 | Sample columns Belge, Sayfa, Değişken, Okunan değer, Güven | Column list | `degerler_table.py:SAMPLE_COLUMNS L88` | V-68 | review mark column first |
| E-101 | Up to 20 sampled value rows | model items | `degerler_model.py:draw_sample L364` | V-68 | random but reproducible per job |
| E-102 | Sample progress in the status bar ("Örnek kontrol: 0 / 5 incelendi", "0 hata") | StatusItem x2 | `degerler.py:_update_status` | V-70 | |
| E-103 | Sample note in the inspector ("Sayfadakiyle aynıysa onaylayın...") | ValueCard why | `degerler.py:_describe L1051` | V-71 | |
| E-104 | Error toast "Örnekte hata: N <değişken> değeri Kontrol'e alındı" + Geri al | toast | `degerler.py:_sample_error L1228` | V-69 | |
| E-105 | End message "Örnek kontrol bitti: N değer, E hata." | message | `degerler.py:_sample_progress L1287` | V-70 | |

(The six sample elements are numbered E-100 to E-105 so the shared menu and toast numbers below stay stable across the audit files; they count as six.)

## 7. Empty states (one widget, six texts)

`degerler_parts.py:EmptyState L156`, filled by `degerler.py:_fill L467-L548`. Parts: mark (48 px card with an icon), title, sentence, primary button, secondary button, note.

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-110 | Empty state "Henüz açık iş yok" (mark: folder; button Yükle'ye git) | EmptyState | `degerler.py L476-L478` | V-90 | the search field is still enabled and the picker shows "Şablon yok" (F-degerler-20) |
| E-111 | Empty state "Şablonlu belge yok" (Kontrol'e git, Şablonlar'a git) | EmptyState | `degerler.py L521-L524` | V-91 | |
| E-112 | Empty state "Değerler henüz okunmadı" (N belgeyi oku, Şablonlar'a git, note "Elle yazdıklarınız yeniden okumada korunur.") | EmptyState | `degerler.py L529-L534` | V-92 | the table header row stays above it with every column title unelided (F-degerler-21); the primary button stays enabled during a read (F-degerler-32) |
| E-113 | Empty state "Aramayla eşleşen değer yok" (query quoted, Aramayı temizle) | EmptyState | `degerler.py L536-L538` | V-42 | the whole query is repeated, 5,000 characters make a 5,053-character sentence |
| E-114 | Empty state "Kontrol bekleyen değer yok" / "İncelenmemiş değer yok" (Tümünü göster) | EmptyState | `degerler.py L540-L544` | V-93 | |
| E-115 | Empty-state buttons (primary, secondary) | QPushButton lg | `EmptyState.primary / secondary` | V-90..V-93 | when pressed from the keyboard the focus falls to the title tabs (F-degerler-09) |
| E-116 | Empty-state mark (48 px) and title as accessible name | QLabel | `EmptyState.show_state L223` | V-90..V-93 | |

## 8. Side panel (Kaynak)

`degerler_side.py`. Hidden with F9 (E-019); the handle is remembered.

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-120 | Side panel (min width 252, default 376) | SidePanel "Kaynak" | `degerler_side.py:SidePanel L530` | V-72 | |
| E-121 | Card scroll area | `_Scroll` (QScrollArea), horizontal bar off | `degerler_side.py:_Scroll L508` | V-72 | no accessible name (AUD-A11Y-01, F-degerler-23); takes keyboard focus when the crop is clicked; the content is laid out at its own width, so anything wider than the viewport is cut (F-degerler-02) |
| E-122 | Source card title (variable name) | QLabel body-strong | `degerler_side.py:SourceCard.title L397` | V-72 | no wrap, no elide, no tooltip: a long name is cut at the panel edge (F-degerler-02) |
| E-123 | Source card meta "Belge 2, sayfa 5" | caption QLabel, wrapping | `SourceCard.meta` | V-72 | in Örnek ", örnek 3 / 20" |
| E-124 | Zoom out (Ctrl+-) | QToolButton | `SourceCard.zoom_out` | V-73 | 50 % floor (14 clicks from 400) |
| E-125 | Zoom in (Ctrl++) | QToolButton | `SourceCard.zoom_in` | V-73 | 400 % ceiling |
| E-126 | Sayfanın tamamı (Boşluk) | QToolButton | `SourceCard.whole` | V-80 | opens the page view (E-140) |
| E-127 | Crop well with the page and the chosen box outlined | SourceView | `degerler_side.py:SourceView L106` | V-72 | other variables' boxes are clickable (hand cursor, tooltip "<ad> değerine git") |
| E-128 | Crop well, loading state | SourceView (page image not rendered yet) | `PageImages L62` | V-72 | cache of 12 pages |
| E-129 | Blank well (icon + "Tablodan bir değer seçince sayfadaki yeri, okunan değer ve öneri burada görünür.") | QFrame "well" | `SourceCard.blank` | V-77 | with title "Değer seçilmedi" / "Okunan değerler burada kaynağıyla görünür." |
| E-130 | Value card "Okunan değer" | ValueCard | `degerler_side.py:ValueCard L455` | V-74 | |
| E-131 | "Okunan" label and the read text (uncertain characters marked) | caption + MarkedText | `ValueCard.read` | V-74 | wraps; an 78-character unbroken code wraps by character |
| E-132 | "Öneri" label and the suggestion (large type, changed characters in the accent colour) | caption + MarkedText | `ValueCard.suggestion` | V-74 | 260 characters make a 384 px block (the panel scrolls) |
| E-133 | Level line (icon, word, percent) + note ("1 karakter belirsiz", "İncelendi") | LevelText | `degerler_side.py:LevelText L320` | V-74 | painted; its accessible name "Güven: Kontrol %41 1 karakter belirsiz" |
| E-134 | Reason line ("Bölüm 1 ile okundu: Z yerine 2.") | caption QLabel, wrapping | `ValueCard.why`; text from `degerler_model.py:Cell.why L172` | V-75 | for a failed document the raw engine text is appended (F-degerler-05) |
| E-135 | Onayla ve sonrakine geç (Enter) | QPushButton primary lg | `SidePanel.accept_button` | V-76 | a second click of a double click confirms the next, unseen value (F-degerler-03) |
| E-136 | Elle yaz (F2) | QPushButton | `SidePanel.type_button` | V-76 | |
| E-137 | Yeni kutu çiz (V) | QPushButton | `SidePanel.variant_button` | V-78 | goes to Şablonlar; the menus call the same command "Yeni varyant çiz" (F-degerler-15) |
| E-138 | Disabled variants of the three buttons (nothing selected, unread value) | the same buttons | `SidePanel.set_actions` | V-76 | |
| E-139 | Hidden state of the whole panel (F9) | n/a | `main_window.py` | V-79 | table card takes the width |

## 9. Page view (loupe overlay, shared with Kontrol)

`ui/loupe.py:Loupe`, opened by Space, E-126, the context menu or the palette. Its elements are listed in `kontrol-inventory.md` E-110 to E-120; what is specific here:

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-140 | Loupe overlay over the Değerler tab (fade in 120 ms, out 80 ms) | Loupe | `degerler.py:toggle_whole_page L1093` | V-80 | focus returns to the widget that had it when it opened; close then reopen inside 80 ms ends hidden (F-degerler-26) |
| E-141 | Caption "Belge 2, sayfa 5" and "Sayfa 1 / 7" | Loupe head | `toggle_whole_page` | V-80 | |
| E-142 | Thumbnail strip, previous / next arrows, Sığdır, Genişlik, %100, Kapat | Loupe parts | `loupe.py` | V-80 | |
| E-143 | Status-bar zoom of the page view | ZoomSlider | `ui/widgets.py` | V-73 | the slider drives the loupe while it is open |

## 10. Menus, context menu, palette

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-150 | Düzen menu entries: Onayla ve sonrakine geç, Seçilenleri onayla, Elle yaz, Yeni varyant çiz, Vazgeç, Tümünü seç | QMenu | `actions.py` (menu="duzen") | V-84 | |
| E-151 | Görünüm: Tüm sayfayı göster | QMenu | `actions.py` | V-84 | |
| E-152 | Git: Sonraki kontrol, Önceki kontrol, Belgeye veya sayfaya git (Ctrl+G) | QMenu | `actions.py` | V-84 | the first one is broken (F-degerler-01) |
| E-153 | Araçlar: Değerleri oku, Yalnızca eksikleri oku, Tümünü incele, Örnek kontrol, Okumayı durdur | QMenu | `actions.py` | V-84 | |
| E-154 | Row context menu (9 entries, each with its key) | QMenu "Değer komutları" | `degerler.py:context_menu L341` | V-83 | right click; keyboard event at the current cell works; at the widget centre it opens nothing (F-degerler-29) |
| E-155 | Context menu separators and disabled entries | QMenu | `degerler.py:CONTEXT` | V-83 | |
| E-156 | Palette entries for the degerler.* commands (Ctrl+K) | CommandPalette | `ui/palette.py` | V-86 | hidden keyword "şüpheli uyarı" on both kontrol commands (F-degerler-30) |
| E-157 | Ctrl+G dialog (Belge / Sayfa number) | GoToDialog | `ui/kontrol_dialogs.py` | V-53 | shared with Kontrol; 0 and 9999 are clamped |

## 11. Status bar

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-160 | "Belge 2 / 3" | StatusItem | `degerler.py:attach L311` | V-85 | |
| E-161 | "206 değer kontrol bekliyor" (alert icon) | StatusItem | same | V-85 | |
| E-162 | "69 okunamadı" (x icon) | StatusItem | same | V-85 | |
| E-163 | "68 / 480 incelendi" (check icon) | StatusItem | same | V-85 | |
| E-164 | "12 belgede şablon var, değer okunmadı" | StatusItem | same | V-85 | also shown after a read in which every document failed (F-degerler-05) |
| E-165 | "Örnek kontrol: x / N incelendi" and "N hata" | StatusItem x2 | same | V-70 | |
| E-166 | Zoom group: minus (24 px), slider, plus (24 px), "%200" | ZoomSlider | `window.register_zoom("degerler", ...)` | V-73 | AUD-HIT-02 fails on the buttons (F-degerler-16, same as F-kontrol-09) |
| E-167 | Status message area (left of the zoom group, "Dışa aktarma ya da okuma sürüyor; ...") | QLabel | `main_window.py:message` | V-94 | |

## 12. Toasts, dialogs, system surfaces

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-170 | Toast (icon, text, optional Geri al, close x) at the window's bottom right, 6 s (10 s with Geri al) | Toast | `ui/feedback.py:Toaster` | V-94, V-99 | one line, width capped: "...5 değer incelenmedi. Enter sırada" is cut at 1366 wide (F-degerler-12); fade 240 ms (F-degerler-27) |
| E-171 | Toast "N belge okundu." / "Okuma durduruldu: N belge okundu ve kaydedildi, kalanlar okunmadı." | Toast | `degerler.py:_read_done L1492, _read_cancelled L1500` | V-14 | the count includes documents whose read failed (F-degerler-05) |
| E-172 | Toast "N değer onaylandı; okunamayan M değer atlandı" + Geri al | Toast | `accept_selected L1143` | V-58, V-99 | |
| E-173 | Taskbar progress (set/clear) | OS | `degerler.py:_progress L1457` | V-08 | calls recorded: set(0,12) ... set(12,12), clear (RD-006c); not visible offscreen |
| E-174 | Window alert at the end of a read (QApplication.alert) | OS | `degerler.py:_finish L1505` | V-14 | not visible offscreen |
| E-175 | Close confirmation while reading ("Bir iş sürüyor. Durdurup kapatılsın mı?...") | QMessageBox | `main_window.py:closeEvent` | V-16 | Qt's English Yes/No buttons (F-yukle-39 class) |
| E-176 | "Durduruluyor… Pencere iş durunca kapanır." | status message | `main_window.py:closeEvent` | V-16 | |
| E-177 | Refusals "Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın." | status message | `main_window.py:_switch_refusal` | V-16 | shown for Ctrl+W, Ctrl+N, Ctrl+O, Ctrl+E, Ctrl+S during a read; not for a file drop (F-degerler-34) |
| E-178 | Tooltips of every button and cell | tooltips | many | V-24 | |
