# Kontrol audit: element inventory

Phase 4, Görev A, screen Kontrol. Starts from `docs/ui-goal/research/inventory-kontrol.md` (feature rows K-01..K-124, observations
O-01..O-26). That file answers "what can the user do"; this one answers "what is on the screen". Each element has an ID `E-nnn`, which
the other audit files use. "K-" names the research row; code references are checked against the working tree on 2026-11-19
(line numbers have moved since the research file; the function names are the stable part).

Element count: 108 numbered elements (6 shared chrome, 15 command bar, 8 overview and timeline, 15 page parts, 10 context menu, 20 inspector, 8 status bar, 9 toast, dialogs and menus, 10 loupe, 6 empty state; the E-ids are not contiguous in every block). Inputs (keys, pointer) are listed in section 10 and tested in `kontrol-paths.md`.
Demo job (`tools/screenshots.py:build`): 15 pages in 3 documents, 2 QR separators, 1 empty page, 2 templates.

Tab order measured by `keywalk.py --tab kontrol` (identical in light, dark, hc, 100 and 150 percent, 1366x768 and 1920x1080):
title tabs, job switch, search, menu, command bar (13 buttons + Diğer komutlar), timeline, Diğer belge komutları, Belgeyi onayla,
Değerlerde aç, zoom minus, zoom slider, zoom plus, back to the title tabs. With pages selected two more stops appear between
"Diğer belge komutları" and "Belgeyi onayla": the rows "Şablon uygula" and "Filtre uygula". Not in the order: the overview strip
(mouse only, E-030), the caption buttons (Alt+Space), the toast and its buttons (E-101 to E-103, mouse and Esc only).

## 1. Shared chrome visible on Kontrol (audited once, here, then referenced)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-001 | Tab strip Yükle / Kontrol / Şablonlar / Değerler / Dışa Aktar / Rehber | TitleTabs (QTabBar) | `ui/chrome.py:TitleTabs` | K-76 | Ctrl+1..6; at 150 percent text and 1366 wide only two tabs fit (F-kontrol-20) |
| E-002 | Job switch (name, save state "Kaydedildi 14:18") | JobSwitch, ElidedLabel, TitleSaveState | `ui/titlebar.py` | none | opens a job menu; elides by itself |
| E-003 | Search box "Ara  Ctrl+K" | SearchBox | `ui/palette.py` | none | opens the command palette |
| E-004 | Menu button (three lines) | QToolButton | `ui/titlebar.py` | K-109 | the menus Düzen, Görünüm, Git, Araçlar |
| E-005 | Caption buttons minimise, maximise, close | CaptionButton x3 | `ui/titlebar.py` | none | NoFocus by design (Alt+Space), exempt from AUD-KBD-01 |
| E-006 | Window frame / drag area of the band | TitleBand | `ui/titlebar.py` | none | double click maximises (not exercised) |

## 2. Command bar (Kontrol's own, 13 buttons + overflow)

Every button is an `ActionButton` with a tooltip that names its key (rule HIG-CTL-06 passes for all). Text labels show on two: "Kes"
and "Sonraki kontrol".

| ID | Element | Key | Enabled when | Research |
|---|---|---|---|---|
| E-010 | Geri al (tooltip "Geri al: <step> (Ctrl+Z)") | Ctrl+Z | an undo step exists | K-118 |
| E-011 | Yinele ("Yinele: <step> (Ctrl+Y)") | Ctrl+Y | a redo step exists | K-118 |
| E-012 | Kes, label shown ("Burada kes / kesimi kaldır (K)") | K | a job is open | K-14 |
| E-013 | Birleştir ("Önceki belgeyle birleştir (M)") | M | job open | K-16 |
| E-014 | Sağa döndür (R) | R | job open | K-42 |
| E-015 | Sayfayı sil ("Sayfayı sil (geri alınabilir) (Del)"; label changes to "N sayfayı sil" / "geri getir") | Del | job open | K-43..K-45 |
| E-016 | Şablonu uygula (T) | T | job open | K-48 |
| E-017 | Filtre uygula (F) | F | job open | K-21 |
| E-018 | Sonraki kontrol, label shown (N) | N | job open | K-65 |
| E-019 | Sonraki incelenmemiş (U) | U | job open | K-66 |
| E-019a | Belgeye veya sayfaya git (Ctrl+G) | Ctrl+G | job open | K-70 |
| E-020 | Sayfayı büyük göster (Boşluk) | Space | job open | K-90 |
| E-021 | Ayrıntı panelini gizle / göster (F9) | F9 | always | K-08 |
| E-022 | Diğer komutlar (overflow menu: Tümünü seç, Seçimi kaldır, Belgeyi onayla, Sola döndür, Önceki kontrol, Sonraki belge, Önceki belge, Değerlerde aç) | menu | always | K-107, K-109 |
| E-023 | Separators between groups (3) | QFrame | | K-107 |


## 3. Work area

| ID | Element | Kind | Where in code | Research | Notes |
|---|---|---|---|---|---|
| E-030 | Overview strip: one square per document | OverviewStrip | `ui/kontrol_overview.py` | K-72, K-73 | mouse click and drag jump; NoFocus; no tooltip (F-kontrol-10) |
| E-031 | Overview "where" text "Belge 1–2 / 3" | part of E-030 | `where_text` | K-72 | |
| E-032 | Overview marks: orange Kontrol, accent İncelendi, grey rest; ring for the documents in view | part of E-030 | `paintEvent` | K-72, K-88 | hc: outlines and filled marks |
| E-033 | Timeline (page list, flow layout, scrolls vertically) | TimelineView (QListView) | `ui/timeline.py` | K-01, K-78 | accessible name "Sayfalar" plus description of keys |
| E-034 | Vertical scroll bar of the timeline | QScrollBar | | K-78 | thin (AUD-HIT-01 skip: "thin scroll bar") |
| E-035 | Empty space in the timeline | viewport | `mousePressEvent` | K-39 | click clears, right click uses current page |
| E-036 | Rubber band | painted overlay | `timeline.py:mouseMoveEvent` | K-32 | translucent accent |
| E-037 | Loading overlay of the timeline | none | | | n/a: tiles show their own "Yükleniyor" (E-051) |

### Page parts (what one document stack and one tile are made of)

| ID | Element | Kind | Where in code | Research | Notes |
|---|---|---|---|---|---|
| E-040 | Guide tab with cut icon, document number, check mark if İncelendi | painted | `timeline.py:_paint_group`, `kontrol_paint.py` | K-79 | tab position tells the cut type |
| E-041 | Lip (line under the tab): solid / dashed / dotted | painted | `kontrol_paint.py:paint_lip` | K-13 | not tested for style (inventory) |
| E-042 | Kontrol rider (warning icon and the word) | painted | `kontrol_paint.py` | K-54 | orange only here |
| E-043 | Page tile (paper, scan, 148 x 209 px at 100 percent; 74 x 105 to 296 x 418) | painted | `TimelineDelegate.paint` | K-84 | |
| E-044 | Page caption ("73") | painted | `_caption` | K-81 | |
| E-045 | Selected look: 2 px ring, 3 px gap, 22 px check badge, bold accent number | painted | `timeline.py` | K-40 | |
| E-046 | Focus (current page) ring | painted | style | K-76 | separate from selection |
| E-047 | Deleted look: dimmed paper, bin disc, caption "N Silinecek", hc hatch | painted | `kontrol_paint.py:paint_hatch` | K-82 | hc hatch uses the hc text-disabled colour, which is bright green (#3ff23f) in this theme |
| E-048 | Dropped-empty look and caption "N Boş" | painted | `_caption` | K-20, K-81 | only with `drop_empty` on |
| E-049 | Separator tile (48 px; QR icon; "Ayraç N" written upwards; no caption) | painted | `timeline.py`, `kontrol_paint.py` | K-80 | |
| E-050 | Loading placeholder (paper and faint "Yükleniyor") | painted | `kontrol_paint.py` | K-83 | |
| E-051 | Failed-render tile (same as E-050 forever) | painted | `thumbnails.py` | K-86, B-024 | open bug |
| E-052 | Dark-theme scan tint | painted | `_scan` | K-87 | |
| E-053 | Page tooltip (same sentence as the screen reader) | tooltip | `TimelineModel.describe` | K-123 | |
| E-054 | Page accessible name | a11y | `describe` | K-117 | "Sayfa 73, Belge 16, kontrol gerekiyor, incelenmedi, silinecek" |

## 4. Context menu (right click, or the keyboard context-menu event)

| ID | Element | Key shown | Notes |
|---|---|---|---|
| E-060 | Header "N sayfa seçili" | | not clickable |
| E-061 | Burada kes | K | |
| E-062 | Önceki belgeyle birleştir | M | |
| E-063 | Sağa döndür | R | |
| E-064 | Sola döndür | Shift+R | |
| E-065 | Şablon uygula (submenu of templates, or disabled hint) | | `kontrol_actions.py:context_menu` |
| E-066 | Filtre uygula… | F | |
| E-067 | Önizle | Space | |
| E-068 | Değerlerde aç | | no key |
| E-069 | Sayfayı sil (red; label follows the count) | Del | `mark_danger` |

## 5. Inspector (right panel, objectName `kontrolInspector`, accessible name "Belge ayrıntısı")

| ID | Element | Kind | Where in code | Research | Notes |
|---|---|---|---|---|---|
| E-070 | Splitter handle between work area and inspector (`kontrol.govde`) | QSplitter handle | `kontrol.py:__init__` | K-02 | width saved in prefs; keyboard resize not exercised |
| E-071 | Rider (when the document needs a check) | widget | `kontrol_paint.py` | K-54 | |
| E-072 | Title "Belge N" / "Belge seçilmedi" | QLabel | `kontrol_inspector.py` L301 | K-99, K-105 | |
| E-073 | Sub line "Şablon adı, sayfa a–b" | QLabel, no wrap | L304 | K-99 | overflows with long names (F-kontrol-03) |
| E-074 | Reason sentence | QLabel, wraps | L306 | K-57 | |
| E-075 | Diğer belge komutları ("..." button) with menu of 4 items | QToolButton + QMenu | L291-L298 | K-104 | tooltip "Diğer" |
| E-076 | Group label "Neden burada başlıyor" | QLabel | L319 | K-100 | |
| E-077 | Row Kesim (icon and word) | `_KvRow` | | K-100 | accessible "Kesim: İşin başı" |
| E-078 | Row Önceki ("Belge N-1, K sayfa" / "Yok") | `_KvRow` | | K-100 | value wraps but widens the column |
| E-079 | Row Durum (İncelendi green check / İncelenmedi dashed circle) | `_KvRow` | | K-63 | icon + word, not colour alone |
| E-080 | Group label "Seçim: N sayfa (a–b)" | QLabel | L433 | K-101 | only with a real selection |
| E-081 | Row Şablon uygula (value template name or "Şablon yok") | ActionRow (focusable) | L343 | K-50 | opens a template menu |
| E-082 | Template menu (sorted names, current checked; disabled hint if none) | QMenu | `kontrol.py:_template_menu` | K-50, K-51 | |
| E-083 | Row Filtre uygula (value "Her N sayfa") | ActionRow (focusable) | L344 | K-27 | opens the same dialog as F |
| E-084 | Group label "Son değişiklikler" | QLabel | L357 | K-102 | card hidden when empty |
| E-085 | History rows (3) with icon, text, time | `_HistRow` | | K-102 | not focusable, accessible name "text, time" |
| E-086 | Card scroller with hairline when more is below | CardScroll | `ui/card_scroll.py` | K-106 | horizontal scroll bar off (F-kontrol-03) |
| E-087 | Pinned button Belgeyi onayla (primary) | GapButton | L373 | K-58 | accessible name "Belge N onayla (Enter)" |
| E-088 | Pinned button Değerlerde aç (subtle) | GapButton | L377 | K-67 | |
| E-089 | Nothing-selected state (title, hint "Bir sayfaya tıklayın ya da oklarla gezinin.", both buttons disabled) | state | `show_nothing` | K-105 | |

## 6. Status bar

| ID | Element | Notes |
|---|---|---|
| E-090 | "Belge 1 / 3" | accessible name |
| E-091 | "Sayfa 1 / 15" | |
| E-092 | "N sayfa seçili" | only above 0 |
| E-093 | "⚠ N belge kontrol bekliyor" | icon + word |
| E-094 | "✓ R / D incelendi" | |
| E-095 | Status message line (`window.message`: "Önce sayfaları seçin." and the other messages of K-114) | plain QLabel, never cleared, not announced (O-05) |
| E-096 | Zoom group: label "%100" (loupe: "%23"), minus button, slider, plus button | ZoomSlider; buttons 24 px (F-kontrol-09); takes over for the loupe (K-96) |
| E-097 | Empty-state line "İşler Yükle sekmesinde açılır (Ctrl+1)" | K-05 |

## 7. Toast, dialogs, menus

| ID | Element | Notes |
|---|---|---|
| E-100 | Toast (icon, text, optional "Geri al", close X) at the window's bottom right, 6 s | `ui/feedback.py`; sits over the inspector buttons (F-kontrol-07) |
| E-101 | Toast "Geri al" button | mouse only (no key for it; Ctrl+Z does the same) |
| E-102 | Toast close X | mouse only |
| E-103 | Toast queue (later toasts wait) | F-kontrol-06 |
| E-104 | Filtre uygula dialog: spin box 1..999 "Her belgedeki sayfa sayısı", intro line, hint "Örnek: önlü arkalı tek yapraklı belgeler için 2.", Vazgeç, Filtreyi uygula | `kontrol_dialogs.py:FilterDialog` |
| E-105 | Belgeye veya sayfaya git dialog: radios Belge / Sayfa, spin box, hint "1 ile N arası", Vazgeç, Git | `GoToDialog` |
| E-106 | Menus Düzen / Görünüm / Git / Araçlar entries for Kontrol | `actions.py:menu_structure` |
| E-107 | Command palette entries for the kontrol.* commands (Ctrl+K) | shared |
| E-108 | Shortcut sheet (Shift+F1) listing Kontrol keys | shared (`shortcut_sheet.py`) |

## 8. Loupe (Önizleme, Space or double click)

| ID | Element | Notes |
|---|---|---|
| E-110 | Loupe overlay (covers the timeline; overview and inspector stay) | `ui/loupe.py:Loupe`, accessible name "Önizleme"; fades in 120 ms |
| E-111 | Head: "Sayfa 5 / 15" | |
| E-112 | Head: place "Belge 2, 1. sayfa" / "QR ayıraç" | dropped at 130 percent text and up (K-89) |
| E-113 | Head: rider | |
| E-114 | Mode buttons Sığdır / Genişlik / %100 (none checked when the zoom is custom) | `_ModeItem` |
| E-115 | Kapat button ("Kapat (Esc)") | tooltip, accessible "Önizlemeyi kapat" |
| E-116 | Page view (scroll area) with the large page | wheel scrolls, Ctrl+wheel zooms |
| E-117 | Chevron buttons "Önceki sayfa (Sol)" / "Sonraki sayfa (Sağ)" | |
| E-118 | Strip of nearby pages with ring on the current one | "Yakındaki sayfalar" |
| E-119 | Loading state inside the loupe | placeholder until the render arrives |
| E-120 | Zoom 10..200 percent via the status-bar slider | K-96 |

## 9. Empty state (no job open)

| ID | Element | Notes |
|---|---|---|
| E-130 | Icon tile and title "Henüz açık iş yok" | accessible "Kontrol: açık iş yok" |
| E-131 | Text "Kesimleri görmek için Yükle'den bir iş açın." | |
| E-132 | Button "Yükle'ye git  Ctrl+1" (primary) | |
| E-133 | Button "Yeni iş oluştur" | tooltip "(Ctrl+N)" |
| E-134 | Card "Son işler" with up to 3 rows (name, "15 sayfa, az önce") | rows focusable |
| E-135 | Command bar and status bar in the empty state (commands disabled, status line E-097) | |

## 10. Keyboard and pointer inputs on the screen (full list with results in `kontrol-paths.md`)

Keys: K, M, R, Shift+R, Del, Enter, Ctrl+A, Esc, F, T, Space, N, Shift+N, U, Ctrl+Left, Ctrl+Right, Ctrl+G, Ctrl+F, arrows, Home,
End, PgUp, PgDn, Shift+arrows, Ctrl+Space, Ctrl+Z, Ctrl+Y, F5, F6, F9, Ctrl+plus, Ctrl+minus, Ctrl+0, Ctrl+1..6, Menu key / Shift+F10.
Pointer: click, Shift+click, Ctrl+click, double click, right click, rubber band, drag of a page, wheel, Ctrl+wheel (timeline, loupe),
overview click and drag, splitter drag, zoom slider drag.
Drag and drop of files onto Kontrol: not handled (only Yükle accepts drops, `yukle.py:dropEvent`); dragging a page does not move it
(no reorder exists, K-53).

Not on this screen although a user might look for it: remove filter (K-28), remove template (K-52), unapprove (K-61), restore blank
pages (K-20), reorder pages (K-53), search (K-77). These are research rows, not audit findings.
