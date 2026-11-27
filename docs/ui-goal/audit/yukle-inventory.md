# Yükle audit: element inventory

Phase 4, Görev A, screen Yükle. Starts from `docs/ui-goal/research/inventory-yukle.md` (feature rows Y-01..Y-60, observations 1..16). That file
answers "what can the user do"; this one answers "what is on the screen". Each element has an ID `E-nnn`, which the other audit files use.
"Y-" names the research row. Code references are checked against the working tree on 2026-11-19 (function names are the stable part).

Element count: **123 numbered elements** in 10 groups (6, 17, 26, 10, 19, 6, 7, 14, 7, 11: shared chrome, command bar, batch table card,
progress and error bar, inspector, status bar, menus, empty page and job list, drop overlay, toasts / dialogs / system surfaces).
Keys, pointer gestures and drags are inputs, not elements: they are in `yukle-paths.md`. Everything in the "Dialogs" block that the OS draws
(file and folder pickers, taskbar) is listed so that its states are accounted for, but only Qt's own dialogs could be driven.

Screen states of Yükle (each has its own set of visible elements): **job open** (table, inspector), **job open and reading** (pending rows,
progress card, İptal et, inspector note), **read failed** (error bar), **job open with no batches**, **no job** (empty page, with or
without remembered jobs), **Tüm işler** (job list over an open job), **drop** (overlay).

Demo data: `tools/screenshots.py:build` (15 pages in 3 documents, 2 QR separators, 1 empty page, 2 templates) plus the synthetic jobs in
`/tmp/claude-0/p4/yukle/longroot` (long names, 120 batches, 40 batches without QR, 29 jobs).

Tab order measured by `keywalk.py --tab yukle` (identical in light, dark, hc, 100, 115, 130 and 150 percent, 1366x768 and 1920x1080):
title tabs, job switch, search box, menu button, command bar (Geri al, Dosya ekle, Klasör ekle, Yeni iş, Partiyi çıkar, Dosya Gezgini,
Kontrol'e geç, panel button, Diğer komutlar), the batch table, the inspector "…", "Rehber'de tarama ayarları", "Kontrol'e geç", "İşi kapat",
back to the title tabs. With one batch the two move buttons are disabled and so out of the order. Not in the order: the splitter handle,
the status bar (F6 reaches it), the drop overlay, the toast and its buttons (mouse and Esc only), the error bar's action and X (they are
buttons but the bar is rebuilt on every read).

## Shared chrome visible on Yükle (audited once in `kontrol-inventory.md` E-001 to E-006; Yükle-specific facts here)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-001 | Tab strip Yükle / Kontrol / Şablonlar / Değerler / Dışa Aktar / Rehber | TitleTabs (QTabBar) | `ui/chrome.py:TitleTabs (L91)` | - | Yükle is the first tab. At 150 % text and 1366 wide only two tabs fit with the demo name, one with a long job name (F-yukle-23) |
| E-002 | Job switch (name, save state "Kaydedildi 14:31") | JobSwitch, ElidedLabel, TitleSaveState | `ui/chrome.py:JobSwitch (L254)`, `ui/titlebar.py` | Y-54 | Shows "İş açılmadı" with no job; opens a menu: Açık iş, Son işler (up to 5), Yeni iş oluştur…, Tüm işler…; width follows the name up to 918 px (F-yukle-23) |
| E-003 | Search box "Ara  Ctrl+K" | SearchBox | `ui/palette.py` | - | Command palette; not Yükle's job search |
| E-004 | Menu button | QToolButton | `ui/titlebar.py` | - | Dosya (Yeni iş, Dosya ekle, Klasör ekle, Kaydet, Gezgin, İşi kapat), Düzen (Yeniden adlandır, Partiyi yukarı/aşağı/çıkar), Araçlar (İptal et) |
| E-005 | Caption buttons (minimise, maximise, close) | CaptionButton x3 | `ui/titlebar.py` | - | NoFocus by design (Alt+Space); close during a read asks first (E-119) |
| E-006 | Title band (drag area) | TitleBand | `ui/titlebar.py` | - | Window title is "Evrakçı 0.0.2 – <job name>" with no length limit |

## Command bar (Yükle's own: 13 buttons + overflow, 3 separators)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-007 | Geri al (name of the last step in the tooltip) | ActionButton | `ui/main_window.py` COMMANDS (L95) | Y-18 | Ctrl+Z. After the demo build the tooltip reads "Geri al: Şablon uygula" (history is shared by all tabs) |
| E-008 | Yinele | ActionButton | `ui/main_window.py` | Y-18 | Ctrl+Y; disabled with nothing to redo |
| E-009 | Separator after undo/redo | QFrame | `ui/chrome.py` | - | decorative |
| E-010 | Dosya ekle… (icon + label) | ActionButton (label) | `ui/main_window.py:_add_files (L901)` | Y-02 | Ctrl+O; with no job it is "new job" (Y-01) |
| E-011 | Klasör ekle | ActionButton | `ui/yukle.py:_extend_command_bar (L722)`, action `yukle.klasor_ekle` | Y-03 | no key; tooltip has no key |
| E-012 | Yeni iş oluştur | ActionButton | `ui/main_window.py:_new_job (L897)` | Y-01 | Ctrl+N |
| E-013 | Separator | QFrame | `ui/chrome.py` | - |  |
| E-014 | Partiyi yukarı taşı | ActionButton | action `yukle.yukari` | Y-15 | Alt+Up; enabled only with a batch above the selected one |
| E-015 | Partiyi aşağı taşı | ActionButton | action `yukle.asagi` | Y-15 | Alt+Down |
| E-016 | Partiyi çıkar (geri alınabilir) | ActionButton | action `yukle.cikar` | Y-16 | Del; tooltip carries two parentheses (C-05) |
| E-017 | Separator | QFrame | `ui/chrome.py` | - |  |
| E-018 | Dosya Gezgini'nde göster | ActionButton | action `yukle.gezginde_goster` | Y-25 | Ctrl+Shift+O; shows the internal copy bN.pdf |
| E-019 | İptal et (icon + label; visible only while reading) | ActionButton (own) | `ui/yukle.py:_extend_command_bar (L722)` | Y-29 | Ctrl+. |
| E-020 | Kontrol'e geç (icon + label) | ActionButton (gated) | `ui/yukle.py:_go_usable (L754)` | Y-43 | Ctrl+2; off with no batches and while reading |
| E-021 | Separator | QFrame | `ui/chrome.py` | - |  |
| E-022 | Ayrıntı panelini gizle | ActionButton | action `app.yan_panel` | Y-46 | F9 |
| E-023 | Diğer komutlar (overflow) | QToolButton moreButton | `ui/chrome.py` | - | Menu with the bar commands that do not fit |

## Batch table card (left pane)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-024 | Card frame "Partiler" | QFrame kind=table-card | `ui/yukle.py:YukleScreen.__init__ (L228)` | Y-19 | accessible name "Partiler" |
| E-025 | Heading "Partiler" | QLabel | `ui/yukle.py:_heading_row (L74)` | Y-19 | 52 px bar |
| E-026 | Heading hint "Sürükleyin ya da Alt+↑ / Alt+↓ ile sıralayın." | QLabel (secondary) | `ui/yukle.py:_heading_row (L80)` | Y-19 | visible even with one batch |
| E-027 | Table (BatchTable) | QTableView | `ui/yukle_table.py:BatchTable (L328)` | Y-19 | single selection, whole row; accessible name and description; Tab leaves it |
| E-028 | Header bar | BatchHeader | `ui/yukle_table.py:BatchHeader (L218)` | Y-19 | 36 px; not clickable, not movable, resizable; minimum section 40 px (F-yukle-13) |
| E-029 | Header: grip column (tooltip "Sürükle") | header section 0 | `yukle_table.py:TITLES` | Y-19 | 44 px, resizable (should be fixed) |
| E-030 | Header: No | header section 1 | `yukle_table.py:TITLES` | Y-19 | 56 px, right-aligned |
| E-031 | Header: Dosya | header section 2 | `yukle_table.py:TITLES` | Y-19 | stretches; the only column that takes the rest |
| E-032 | Header: Sayfa | header section 3 | `yukle_table.py:TITLES` | Y-19 | 96 px at every text size |
| E-033 | Header: QR ayıraç | header section 4 | `yukle_table.py:TITLES` | Y-19 | 116 px |
| E-034 | Header: Durum | header section 5 | `yukle_table.py:TITLES` | Y-19 | 148 px at every text size (F-yukle-05) |
| E-035 | Batch row: grip cell (drag handle, move cursor) | delegate cell | `yukle_table.py:BatchDelegate.paint (L265)`, `mouseMoveEvent (L419)` | Y-14 | SizeAllCursor over the grip |
| E-036 | Batch row: No cell | delegate cell | `yukle_table.py:BatchModel.text (L130)` | Y-19 | plain digits |
| E-037 | Batch row: Dosya cell (file name) | delegate cell | `yukle_table.py:_cell (L298)` | Y-19 | elided at the right, no tooltip (F-yukle-04) |
| E-038 | Batch row: Sayfa cell | delegate cell | `yukle_table.py:BatchModel.text (L136)` | Y-19 | no thousands dot (F-yukle-27) |
| E-039 | Batch row: QR ayıraç cell | delegate cell | `yukle_table.py:BatchModel.text (L138)` | Y-19 | "…" while reading |
| E-040 | Batch row: Durum cell (icon + word Hazır / Kontrol) | delegate cell | `yukle_table.py:_status (L313)` | Y-21 | word not elided (F-yukle-05); Kontrol colour 6.12:1 (F-yukle-22) |
| E-041 | Pending row (one per file being read): Okunuyor / Sırada | delegate row | `yukle_table.py:STATUSES (L46)`, `yukle.py:_Reading.rows (L156)` | Y-20 | cannot be selected or dragged; finished files keep "Okunuyor" (F-yukle-31) |
| E-042 | Toplam row (pages, QR, "N parti") | delegate row | `yukle_table.py:BatchModel._rebuild (L93)` | Y-20 | enabled but not selectable: takes the keyboard current index (F-yukle-02) |
| E-043 | Row focus ring (2 px outer + 1 px inner, inside the row) | paintEvent | `yukle_table.py:BatchTable.paintEvent (L427)` | Y-23 | drawn for batch rows only |
| E-044 | Selected-row fill and left edge | delegate | `yukle_table.py:BatchDelegate.paint (L265)` | Y-23 | single selection |
| E-045 | Drop indicator while dragging a batch | QTableView drop indicator | `BatchTable.setDropIndicatorShown` | Y-14 | between rows, onto a row, below the rows |
| E-046 | Vertical scroll bar | QScrollBar | Qt | - | appears from about 12 rows |
| E-047 | Empty area below the rows | viewport | `yukle_table.py` | Y-14 | drop target "to the end" |
| E-048 | Dropline: icon + "PDF'leri pencerenin herhangi bir yerine bırakın…" | _Dropline | `ui/yukle.py:_Dropline (L90)` | Y-47 | 52 px strip at the foot of the card, always shown |
| E-049 | Splitter handle between table and inspector | QSplitterHandle | `yukle.py: self.splitter (L219)` | Y-22 | remembered per user; inspector minimum 156 px (F-yukle-12) |

## Reading progress card and error bar (under or above the table)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-050 | Progress card frame | ProgressCard (QFrame card) | `ui/yukle_parts.py:ProgressCard (L110)` | Y-28 | live region; accessible name "Okuma ilerlemesi" |
| E-051 | Progress icon (scan-text) | QLabel | `yukle_parts.py:_restyle (L152)` | Y-28 |  |
| E-052 | Progress title "Sayfalar okunuyor: 33 / 80" / "Dosyalar inceleniyor: N" / "İptal ediliyor…" | QLabel | `yukle_parts.py:show_progress (L160)`, `show_waiting (L174)` | Y-27/28/29 |  |
| E-053 | Current file name (elided, tooltip with the full name) | ElidedLabel | `yukle_parts.py (L128)` | Y-28 | tooltip present (measured) |
| E-054 | Progress bar (determinate and indeterminate) | QProgressBar | `yukle_parts.py (L138)`, `show_waiting (L176)` | Y-28 | indeterminate animates in reduced motion (F-yukle-29) |
| E-055 | Percent "%41" | QLabel | `yukle_parts.py` | Y-28 |  |
| E-056 | Time left "Süre hesaplanıyor…" / "Yaklaşık 40 sn kaldı" | QLabel | `yukle_parts.py:eta_text (L60)` | Y-28 |  |
| E-057 | Speed "3,2 sayfa/sn" | QLabel | `yukle_parts.py:rate_text (L55)` | Y-28 | hidden until known |
| E-058 | Note "İptal ederseniz hiçbir şey değişmez." | QLabel | `yukle_parts.py (L145)` | Y-28 | does not name Ctrl+. or the İptal et button |
| E-059 | Error bar: icon, title "Okunamadı", text, action "Dosya ekle…", close X | InfoBar (error) | `ui/yukle.py:_fail (L1008)` | Y-31 | inserted at the top of the pane: the table moves down 70 px (F-yukle-24); action and X are buttons, the bar itself is NoFocus |

## Inspector (right pane; F9 hides it)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-060 | Inspector frame | Inspector (QWidget yukleInspector) | `ui/yukle_side.py:Inspector (L189)` | Y-38 | accessible name "İş ayrıntısı"; default 312 px, minimum 156 px |
| E-061 | Scroll area (horizontal bar off) | QScrollArea | `yukle_side.py (L206-L209)` | Y-38 | hides overflow instead of showing it (F-yukle-01) |
| E-062 | Caption "Açık iş" | QLabel | `yukle_side.py (L222)` | Y-38 |  |
| E-063 | "…" button (Diğer iş komutları) | QToolButton (menu) | `yukle_side.py (L226)` | Y-45 | tooltip "Diğer"; 32 x 32 |
| E-064 | Title "15 sayfa" (page total) | QLabel (page) | `yukle_side.py:show_job (L321)` | Y-38 | no thousands dot (F-yukle-27); "İş açılmadı" before the first job |
| E-065 | Sub line "1 parti, 3 belge bulundu" | QLabel | `yukle_side.py (L322)` | Y-38 |  |
| E-066 | Reason sentence (QR split) | QLabel (wrap) | `yukle_info.py:reason (L54)`, `ordinals (L46)` | Y-38 | names every batch without a separator (F-yukle-11) |
| E-067 | Group label "Ön kontrol" | QLabel | `yukle_side.py (L257)` | Y-39 |  |
| E-068 | Row QR ayıraç: key, value, "şimdilik" | KvRow | `yukle_side.py:KvRow (L67)` | Y-39 | accessible name "QR ayıraç: 2" |
| E-069 | Row Belge: key, value | KvRow | `yukle_side.py (L263)` | Y-39 | "…" while reading |
| E-070 | Row Durum: key, icon, value (Hazır / N belge / Okunuyor) | KvRow | `yukle_side.py:show_job (L328)` | Y-39 | warning shows "N belge", never the word Kontrol (F-yukle-21) |
| E-071 | Group label "Tarama profili" | QLabel | `yukle_side.py (L273)` | Y-41 |  |
| E-072 | Profile line 1 "100 dpi, gri tonlamalı" / "Tarama bilgisi yok" | QLabel + icon | `yukle_side.py:ProfileRows (L119)`, `set_profile (L165)` | Y-41 | not wrapped (F-yukle-01) |
| E-073 | Profile line 2 "A4, dosyalardan okundu" / "Dosyalarda tarama görüntüsü bulunamadı" | QLabel | `yukle_side.py:set_profile (L165)` | Y-41 | not wrapped (F-yukle-01) |
| E-074 | Link row "Rehber'de tarama ayarları" + chevron | QPushButton + icon | `yukle_side.py (L152-L157)` | Y-42 | tooltip "Rehber sekmesinde tarama ayarlarını aç"; lands at the top of Rehber |
| E-075 | Primary button "Kontrol'e geç" | GapButton (primary, lg) | `yukle_side.py:GapButton (L39)`, `(L283)` | Y-43 | Enter does not press it (F-yukle-15) |
| E-076 | Secondary button "İşi kapat" | GapButton (subtle) | `yukle_side.py (L290)` | Y-44 | replaced by the note while reading |
| E-077 | Reading note "Okuma bitince açılır." + icon | QLabel + QLabel | `yukle_side.py (L296-L301)` | Y-40 | layout margins 9 px (F-yukle-32) |
| E-078 | Inspector "…" menu: Yeniden adlandır, Dosya Gezgini'nde göster, İşi kapat | QMenu | `ui/yukle.py:_fill_more (L774)` | Y-45 | 3 entries |

## Status bar (Yükle's slot)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-079 | Part "N parti" | StatusPart | `ui/yukle.py:_sync_status (L798)` | Y-34 |  |
| E-080 | Part "N sayfa" | StatusPart | `yukle.py (L818)` | Y-34 | no thousands dot |
| E-081 | Part "N belge" | StatusPart | `yukle.py (L825)` | Y-34 |  |
| E-082 | Part warning "N belge kontrol bekliyor" (icon + text) | StatusPart | `yukle.py (L828)` | Y-34 |  |
| E-083 | Part busy "Okunuyor: x / y" (spinner icon) | StatusPart | `yukle.py (L822)` | Y-34 | icon static |
| E-084 | Part text "Ctrl+N ile yeni iş oluşturabilirsiniz" | StatusPart | `yukle.py (L809)` | Y-34 | empty page only |

## Context menus and popups

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-085 | Batch row menu: Partiyi yukarı taşı | QAction in QMenu | `yukle.py:_context_menu (L784)` | Y-24 | built from the previous selection when opened on the Toplam row |
| E-086 | Batch row menu: Partiyi aşağı taşı | QAction | `yukle.py:_context_menu` | Y-24 |  |
| E-087 | Batch row menu: Partiyi çıkar | QAction | `yukle.py:_context_menu` | Y-24 |  |
| E-088 | Batch row menu: Dosya Gezgini'nde göster | QAction | `yukle.py:_context_menu` | Y-24 | after a separator |
| E-089 | Job row menu: İşi aç | QAction | `yukle_parts.py:EmptyPage.job_menu (L490)` | Y-51 |  |
| E-090 | Job row menu: Klasörünü Dosya Gezgini'nde göster | QAction | `yukle_parts.py:job_menu (L496)` | Y-51 |  |
| E-091 | Job switcher menu (title band): Açık iş, Son işler, Yeni iş oluştur…, Tüm işler… | QMenu | `ui/main_window.py:open_job_switcher (L1079)` | Y-54 | menu 800 px wide with a long name |

## Empty page (no job) and "Tüm işler"

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-092 | Mark (upload icon in a card) | QLabel | `yukle_parts.py:EmptyPage (L385)` | Y-47 |  |
| E-093 | Title "Henüz iş yok" / "Tüm işler" | QLabel (panel) | `yukle_parts.py:set_mode (L479)` | Y-47/50 |  |
| E-094 | Sentence "Taradığınız PDF'leri bırakın ya da yeni bir iş oluşturun." / "Açmak için bir iş seçin ya da adını yazın." | QLabel | `yukle_parts.py (L396, L484)` | Y-47/50 |  |
| E-095 | Button "Yeni iş oluştur  Ctrl+N" (icon, label, key) | QPushButton primary lg | `yukle_parts.py (L407-L421)` | Y-47 |  |
| E-096 | Button "Dosya ekle…" | QPushButton lg | `yukle_parts.py (L423)` | Y-47 | label starts with a space for the icon |
| E-097 | Search field "İş adı ara" (placeholder) | _Search (QLineEdit) | `yukle_parts.py:_Search (L349)` | Y-48 | Enter opens the first match, Down moves to the rows, Esc clears |
| E-098 | Search leading icon (decorative) | QToolButton (line edit action) | `yukle_parts.py (L441)` | Y-48 | 22 x 18, no tooltip, NoFocus (F-yukle-26) |
| E-099 | Search clear button | QToolButton | `yukle_parts.py (L440)` add_clear_button | Y-48 | 38 x 38, tooltip "Temizle" |
| E-100 | Group label "Son işler" / "İşler" | QLabel | `yukle_parts.py (L447)` | Y-49 |  |
| E-101 | Job row: folder icon, name (elided), "15 sayfa, az önce" | _JobRow (RecentJobRow) | `yukle_parts.py:_JobRow (L332)`, `ui/chrome.py:RecentJobRow (L404)` | Y-49 | tooltip "<name> işini aç"; Enter does not open (F-yukle-15) |
| E-102 | Card holding the job rows (3 rows, 8 in "Tüm işler") | QFrame card | `yukle_parts.py (L450)` | Y-49 | no scrolling: eight rows cut at 150 % (F-yukle-10) |
| E-103 | "N iş daha var; aramak için adını yazın." | QLabel | `yukle_parts.py:rebuild (L531)` | Y-49 |  |
| E-104 | No-match text "“x” ile eşleşen iş yok." | QLabel (wrap) | `yukle_parts.py:rebuild (L528)` | Y-48 | repeats the whole query |
| E-105 | Link "Aramayı temizle" | QPushButton link | `yukle_parts.py (L463)` | Y-48 |  |

## Drop overlay (window-wide)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-106 | Overlay layer with dashed accent edge | DropOverlay | `yukle_parts.py:DropOverlay (L185)` | Y-05 | 82 % opaque (100 % in hc), mouse-transparent |
| E-107 | Card (fixed 560 px wide) | QFrame card | `yukle_parts.py (L198)` | Y-05 | F-yukle-06 |
| E-108 | Mark and heading "PDF'leri bırakın" | QLabel x2 | `yukle_parts.py (L205)` | Y-05 |  |
| E-109 | Summary sentence (rich text, job name in bold) | QLabel (wrap) | `yukle_parts.py:show_drop (L259)` | Y-05 | an unbroken long name does not wrap (F-yukle-06); counts to 200 only (F-yukle-07) |
| E-110 | File rows (up to 5): icon, name (elided), size | _FileRow | `yukle_parts.py:_FileRow (L296)` | Y-05 |  |
| E-111 | "ve N dosya daha" | QLabel | `yukle_parts.py (L274)` | Y-05 |  |
| E-112 | Note "Klasörlerdeki PDF'ler de eklenir… Vazgeçmek için Esc." + icon | QLabel + QLabel | `yukle_parts.py (L222)` | Y-05 | Esc cannot be handled by the app during an OS drag (O-15) |

## Toasts, dialogs and system surfaces used by Yükle

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-113 | Toast: icon, text, "Geri al", close X | _Toast | `ui/feedback.py:Toaster (L180)` | Y-02/16/29 | bottom right; text not wrapped (F-yukle-08); covers the inspector buttons (F-yukle-09) |
| E-114 | Toast queue (one at a time, 6 s; 10 s with an action) | Toaster | `feedback.py:Toaster.show (L193)`, `_tell (yukle.py L996)` | Y-02 | later toasts wait |
| E-115 | File dialog "Taranmış PDF'leri seçin" / "Parti ekle" (filter PDF) | QFileDialog (native) | `yukle.py:choose_new_job (L411)`, `choose_batch (L424)` | Y-01/02 | starts in the last folder |
| E-116 | Folder dialog "PDF klasörü seçin" | QFileDialog (native) | `yukle.py:choose_folder (L437)` | Y-03 |  |
| E-117 | Name dialog "Yeni iş" / "İşin adı:" | QInputDialog | `yukle.py:choose_new_job (L420)` | Y-01 | no length limit; empty name is silent (F-yukle-16) |
| E-118 | Rename dialog "İşi yeniden adlandır" / "İşin adı:" | QInputDialog | `yukle.py:rename_job (L565)` | Y-17 |  |
| E-119 | Close confirmation "Bir iş sürüyor. Durdurup kapatılsın mı?…" (Evet / Hayır) | QMessageBox | `ui/main_window.py:closeEvent (L1450)` | Y-37 | buttons are Qt's standard Yes/No |
| E-120 | Taskbar progress (indeterminate, then done / total) | TaskbarProgress | `yukle.py:_begin (L909)`, `_progress` | Y-33 | Windows only; not seen offscreen |
| E-121 | Taskbar attention flash at the end of a read | QApplication.alert | `yukle.py:_attention (L986)` | Y-33 | Windows only |
| E-122 | Busy cursor over the screen while reading | QCursor | `yukle.py:_begin (L907)` | Y-30 | set at once (F-yukle-30) |
| E-123 | Window title "Evrakçı 0.0.2 – <job>" | QMainWindow | `yukle.py:_name_changed (L682)` | Y-17 | no length limit |
