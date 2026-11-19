# Dışa Aktar audit: element inventory

Phase 4, Görev A, screen Dışa Aktar. Starts from `docs/ui-goal/research/inventory-disa-aktar.md` (feature rows D-01..D-64, observations 1-18). That file answers "what can the user do"; this one answers "what is on the screen". Each element has an ID `E-nnn` used by the other files of this audit. Keys, pointer gestures and drags on the elements are in `disa-aktar-paths.md`, states in `disa-aktar-states.md`, motion in `disa-aktar-motion.md`, strings in `disa-aktar-copy.md`.

Element count: **132 numbered elements** in 10 groups (6 shared chrome, 11 command bar, 3 column frame, 6 progress card, 14 outcome card, 19 Ön kontrol, 31 file list, 24 Ayarlar panel, 5 status bar, 13 dialogs, toasts and system surfaces).

Screen states (each has its own set of visible elements, `_compute_state`): **empty** (no document: empty pane, one Bilgi row), **main** (Ön kontrol and the list, export on), **blocked** (an Engel row, export off with "Önce engeli giderin."), **running** (progress card, locked panel, list in run mode, Ön kontrol hidden) and **done** (outcome card, "Yazılan dosyalar", "Yeniden dışa aktar…"). A stopped or failed run returns to main or blocked with an outcome card on top (the folder is then full, so the next state is usually blocked).

Demo data: `tools/screenshots.py:build` (3 documents of 3, 2 and 2 pages, 2 templates, one value that needs a check) for the default states, plus the synthetic cases built for this audit and never committed: 3 to 400 documents with 110 to 200 character names, a 150-character unknown variable, target paths of 47 to 234 characters, a 320-character job name, big counts injected into the cards, long reasons injected into the file model, read-only and unlistable folders (run as `nobody`).

Tab order measured by `keywalk.py --tab disa_aktar` (identical in light, dark, hc, 100, 115, 130 and 150 percent, 1366x768 and 1920x1080, 24 of 24 clean, 21 stops): job switch, search box, menu button, command bar (Geri al, Dışa aktar, Yenile, Dizini yazdır, Ayarlar paneli, Diğer komutlar), then the work area: Klasör seç (Ön kontrol link), Sonraki kontrol, Değerler'e git, Yalnızca kontrol gerekenler, the file table, Hedef klasör, the folder button, Dosya adı kalıbı, Değişken ekle, Metin katmanı ekle (OCR), Geçersiz karakterleri değiştir, Dışa aktar, then back to the tabs. The disabled index.xlsx checkbox and the two Aç buttons of the command bar are not in the walk (disabled in the demo state).

## 0. Shared chrome visible on Dışa Aktar (audited once in `kontrol-inventory.md` E-001 to E-006)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-001 | Tab strip Yükle / Kontrol / Şablonlar / Değerler / Dışa Aktar / Rehber | TitleTabs (QTabBar) | ui/chrome.py:TitleTabs | D-62 | Dışa Aktar is the fifth tab; at 150 % text and 1366 wide the tabs after Kontrol move into a « menu |
| E-002 | Job switch (job name, save state) | JobSwitch | ui/titlebar.py | D-60 | shows the job; a 160-character job name is elided with no wrap (L1) |
| E-003 | Search box "Ara  Ctrl+K" | SearchBox | ui/palette.py | none | draws the key as "Kontrol+K" (F-disa-aktar-19) |
| E-004 | Menu button (Dosya, Düzen, Görünüm, Araçlar ...) | QToolButton | ui/titlebar.py | D-52, D-53 | Dosya holds index.xlsx'i aç, Dosya Gezgini'nde göster, Dizini yazdır; Araçlar holds Dışa aktarmayı durdur |
| E-005 | Caption buttons (3) | CaptionButton | ui/titlebar.py | none | NoFocus by design |
| E-006 | Window title / drag area | TitleBand | ui/titlebar.py | none | not exercised |

## 1. Command bar (`main_window.py:COMMANDS['disa_aktar']`, lines 122-127)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-007 | Geri al | ActionButton | `app.geri_al` | none | acts on the JOB's undo stack, so it undoes steps made on other tabs (F-disa-aktar-01); tooltip "Geri al: Şablon uygula (Kontrol+Z)" |
| E-008 | Yinele | ActionButton | `app.yinele` | none | enabled after an undo |
| E-009 | Dışa aktar (labelled) | ActionButton | `app.disa_aktar` | D-36 | off while an Engel exists or while writing; one owner: `MainWindow._sync_export_action` |
| E-010 | Dışa aktarmayı durdur (icon, circle-x) | ActionButton | `disa_aktar.durdur` | D-40 | on only while writing; Ctrl+. |
| E-011 | Yenile (labelled) | ActionButton | `app.yenile` | D-54 | accessible name "Listeyi ve önizlemeyi yenile (F5)"; off while writing |
| E-012 | Dizini yazdır (icon, printer) | ActionButton | `disa_aktar.yazdir` | D-53 | Ctrl+P; on whenever the list has rows, also while writing |
| E-013 | index.xlsx'i aç (icon, sheet) | ActionButton | `disa_aktar.index_ac` | D-52 | on only when this run wrote index.xlsx and it exists |
| E-014 | Dosya Gezgini'nde göster (icon) | ActionButton | `disa_aktar.gezginde_goster` | D-52 | on when the outcome has a folder or the typed folder exists |
| E-015 | Ayarlar panelini gizle / göster (F9) | ActionButton | `app.yan_panel` | D-61 | hides the whole right column including the folder field and the primary button (F-disa-aktar-11) |
| E-016 | Diğer komutlar (overflow) | QToolButton + menu | `chrome.py` command bar | D-62 | holds what does not fit at 150 % text |
| E-017 | Separators (3) and the grow spacer | QFrame | command bar | none | not focusable |

## 2. Left column frame (`disa_aktar.py:__init__`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-018 | Left scroll area "Dışa aktarma özeti" | QScrollArea | `DisaAktarScreen.left_scroll` | D-62 | horizontal bar off; vertical bar at large text; its content can be wider than the viewport (F-disa-aktar-04) |
| E-019 | Splitter handle (list / Ayarlar) | QSplitter handle | `DisaAktarScreen.splitter` | D-35 | dragged width is remembered; the panel keeps a minimum of 320 px |
| E-020 | Stack host (list or empty pane) | QStackedLayout | `stack_host` | D-01 | list in main, blocked, running, done; empty pane when there are no documents |

## 3. Progress card (`RunBanner`, `disa_aktar_banners.py`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-021 | Progress card | QFrame card | `RunBanner` | D-38 | shown only while writing; Ön kontrol is hidden then |
| E-022 | Spinner icon (loader-circle, 20 px) | QLabel pixmap | `RunBanner.icon` | D-38 | static pixmap |
| E-023 | Count "Yazılıyor: n / N" ("Yazılıyor…" before the first report) | QLabel | `RunBanner.count` | D-38 | restarts at 0 / N when the text layer stage begins (F-disa-aktar-27) |
| E-024 | Stage text (dosyalar yazılıyor / metin katmanı ekleniyor) | QLabel | `RunBanner.stage` | D-38 | secondary text |
| E-025 | Progress bar (8 px, accessible name "Yazma ilerlemesi") | QProgressBar | `RunBanner.bar` | D-38 | range 0..0 (busy) until the first report |
| E-026 | Caption "%33, bir dakikadan az kaldı. Durdur (Ctrl+.) ile ..." | QLabel wrapped | `RunBanner.sub` | D-38, D-40 | changes to "Durduruluyor; o ana kadar yazılanlar kalır…" after Ctrl+. |

## 4. Outcome card (`OutcomeBanner`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-027 | Outcome card | QFrame card | `OutcomeBanner` | D-47..D-49 | three kinds; the done card has no close button, the others do |
| E-028 | Outcome icon (24 px: folder-check ok, info, circle-x danger) | QLabel pixmap | `OutcomeBanner.icon` | D-47 | kind shown by icon and title, not colour alone |
| E-029 | Title ("N belge yazıldı" / "Dışa aktarma durduruldu" / "Dışa aktarma tamamlanamadı") | QLabel | `OutcomeBanner.title` | D-47..D-49 | panel type |
| E-030 | Sentence (folder, time, what happens to the job / the core's error text) | QLabel wrapped, selectable | `OutcomeBanner.message` | D-47..D-49 | carries raw OS error text in the failed kind (F-disa-aktar-06) |
| E-031 | Kontrol line: warning icon | QLabel pixmap | `OutcomeBanner.check_icon` | D-47 | only when needing_check > 0 |
| E-032 | Kontrol line: word "Kontrol" | QLabel | `OutcomeBanner.check_word` | D-46 | orange `check-text` |
| E-033 | Kontrol line: "N belge kontrol gerektiriyor; index.xlsx'te işaretli, nedeni yazılı." | QLabel wrapped | `OutcomeBanner.check_text` | D-47 | - |
| E-034 | Klasörü aç (primary) | PartsButton | `OutcomeBanner.folder_button` | D-52 | takes focus when the run ends; silent if the folder is gone (F-disa-aktar-16) |
| E-035 | index.xlsx'i aç | PartsButton | `OutcomeBanner.index_button` | D-52 | only when index.xlsx was written; silent if it is gone |
| E-036 | Dosya Gezgini'nde göster | PartsButton | `OutcomeBanner.reveal_button` | D-52 | done kind only |
| E-037 | Close button "Mesajı kapat" (x icon) | QPushButton subtle | `OutcomeBanner.close_button` | D-48, D-49 | stopped and failed kinds; focus goes to the export button |
| E-038 | Kind: done | variant | `show_outcome(kind="done")` | D-47 | stays until Yeniden dışa aktar |
| E-039 | Kind: stopped | variant | `show_outcome(kind="stopped")` | D-48 | "N dosya yazıldı, index.xlsx yazılmadı" |
| E-040 | Kind: failed | variant | `show_outcome(kind="failed")` | D-49 | settings and typed folder stay |

## 5. Ön kontrol card (`PreflightCard`, `CheckRow`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-041 | Ön kontrol card | QFrame table-card | `PreflightCard` | D-03 | hidden while writing and when done |
| E-042 | Head title "Ön kontrol" | HeadBar label | `PreflightCard.head` | D-03 | - |
| E-043 | Head caption "N belge, M sayfa (K ayıraç sayfası hariç)" / "belge yok" | HeadBar label | `_left_out_note` | D-03 | three forms |
| E-044 | Row kind Engel (3 px danger bar, icon ban) | CheckRow | `LEVEL_LOOK['engel']` | D-04..D-07 | first rows; the export button is off |
| E-045 | Row kind Kontrol (warning icon, orange word) | CheckRow | `LEVEL_LOOK['kontrol']` | D-10 | never blocks |
| E-046 | Row kind Eksik (dashed circle) | CheckRow | `LEVEL_LOOK['eksik']` | D-11 | - |
| E-047 | Row kind Bilgi (info icon) | CheckRow | `LEVEL_LOOK['bilgi']` | D-08, D-12, D-13 | - |
| E-048 | Row kind Tamam (check icon, green) | CheckRow | `LEVEL_LOOK['tamam']` | D-09 | not shown with an Engel |
| E-049 | Row status: icon + word (96 px at 100 %, 136 at 150 %) | QWidget | `CheckRow.status` | D-62 | never colour alone |
| E-050 | Row sentence: bold title + secondary detail (wrapped) | QLabel rich text | `CheckRow.text` | D-03 | size policy Ignored: an unbroken word is cut, not wrapped (F-disa-aktar-05) |
| E-051 | Row count (bold number, 32 px wide) | QLabel | `CheckRow.count` | D-03 | fixed width: 4 digits and more are cut (F-disa-aktar-15) |
| E-052 | Link "Yeni alt klasör oluştur" | QPushButton link | action `subfolder` | D-17 | creates a folder named after the job (not cut: F-disa-aktar-07) |
| E-053 | Link "Klasör seç" | QPushButton link | action `choose` | D-05, D-08 | opens the folder dialog |
| E-054 | Link "Kalıbı düzelt" | QPushButton link | action `pattern` | D-06 | focuses and selects the pattern field; hidden when the panel is hidden |
| E-055 | Link "Sonraki kontrol" | QPushButton link | action `next_check` | D-10 | opens Kontrol at the first check |
| E-056 | Link "Değerler'e git" | QPushButton link | action `values` | D-11 | - |
| E-057 | Link "Adları göster" | QPushButton link | action `show_names` | D-12 | clears the filter, selects the first changed name |
| E-058 | Link "Kontrol'e git" | QPushButton link | action `kontrol` | D-13 | - |
| E-059 | Empty row "Belge, kontrol ve eksik değer denetimi iş açılınca burada görünür." (count "–") | CheckRow | `_build_findings` | D-02 | with no documents |

## 6. Dosya adları card (`FilesTable`, `FilesModel`, `FilesDelegate`)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-060 | Files card | QFrame table-card | `files_card` | D-27 | - |
| E-061 | Head title "Dosya adları" / "Yazılan dosyalar" | HeadBar label | `files_head` | D-27 | while writing and after: the folder in the caption, middle-elided at 520 x scale px (F-disa-aktar-04) |
| E-062 | Head caption "kontrol gerekenler üstte" / the target folder | HeadBar label | `files_head` | D-27 | tooltip carries the full folder |
| E-063 | Filter button "Yalnızca kontrol gerekenler" + count | PartsButton checkable | `filter_button` | D-30 | only before writing and only when the count is above 0; count cut above 5 digits is not an issue here |
| E-064 | File table | QTableView | `FilesTable` | D-27 | painted by one delegate; accessible name "Dosya adları" |
| E-065 | Header "Durum" | QHeaderView section | `FilesModel.HEADERS` | D-27 | - |
| E-066 | Header "Yazılacak dosya adı" / "Yazılan dosya" | QHeaderView section | `FilesModel.HEADERS` | D-27 | changes after writing |
| E-067 | Header "Sayfalar" (right aligned) | QHeaderView section | `FilesModel.HEADERS` | D-27 | - |
| E-068 | Header "Şablon" | QHeaderView section | `FilesModel.HEADERS` | D-27 | column hidden when the names need the room (F-disa-aktar-14, 33) |
| E-069 | Column edge handles (3) | QHeaderView resize | `_fit_columns` | D-35 | remembered; Durum narrows before the table scrolls |
| E-070 | Durum cell: icon | delegate paint | `FilesDelegate._status` | D-29 | 16 px, 24 at 150 % |
| E-071 | Durum cell: word (Tamam / Bilgi / Kontrol / Bekliyor / Yazılıyor / Yazıldı) | delegate paint | `LOOK` | D-29 | strong for Kontrol |
| E-072 | Durum cell: reason caption ("Sicil_No eksik", "Ad çakışması, (2) eklendi" ...) | delegate paint | `FilesDelegate._status` | D-29 | elided on the right; no tooltip for it (F-disa-aktar-14) |
| E-073 | Name cell (plain) | delegate paint | `FilesDelegate._name` | D-34 | elided in the middle when wider than the column |
| E-074 | Name cell with an accent suffix " (2)" | delegate paint | `FilesDelegate._name` | D-34 | accent + bold |
| E-075 | Sayfalar cell (range "4–5") | delegate paint | `pages_text` | D-29 | a range, not a count (research O-02) |
| E-076 | Şablon cell ("Şablon yok" when none) | delegate paint | `FilesDelegate.paint` | D-27 | elided with no tooltip of its own (the name tooltip carries it) |
| E-077 | Row hairline | delegate paint | `stroke-soft` | D-27 | - |
| E-078 | Selected row fill (hc: accent fill, inverted ink) | delegate paint | `selected` | D-27 | extended selection with Shift and Ctrl |
| E-079 | Current row accent bar (3 px) | delegate paint | `FilesDelegate.paint` | D-27 | column 0 only |
| E-080 | Focus ring | style overlay | `EvrakciStyle` PE_FrameFocusRect | D-62 | drawn inside the row |
| E-081 | Vertical scroll bar | QScrollBar | `FilesTable` | D-64 | per pixel |
| E-082 | Horizontal scroll bar | QScrollBar | `FilesTable` | D-34 | appears when names plus Durum and Sayfalar are wider than the card |
| E-083 | Name tooltip ("<name>\nŞablon: <template>") | ToolTipRole | `FilesModel.data` | D-34 | column 1 only |
| E-084 | Type-ahead on the name column | keyboardSearch | `FilesTable.keyboardSearch` | D-31 | no visible search box; Ctrl+F only moves focus here |
| E-085 | Context menu | QMenu | `_row_menu` | D-33 | opens with the right button; the keyboard way opens it at the viewport centre (F-disa-aktar-13) |
| E-086 | Context menu item "Dosya adını kopyala" (Ctrl+C) | QAction | `copy_names` | D-32 | - |
| E-087 | Context menu item "Dosya Gezgini'nde göster" | QAction | `reveal_selected` | D-33 | after writing only |
| E-088 | Empty pane: mark (48 px) | QLabel | `EmptyPane.mark` | D-02 | - |
| E-089 | Empty pane: heading "Dışa aktarılacak belge yok" and sentence | QLabel | `EmptyPane` | D-02 | also shown for a job with zero documents (research O-05) |
| E-090 | Empty pane: button "Yükle'ye git" (Ctrl+1) | PartsButton primary | `EmptyPane.go` | D-02 | - |

## 7. Ayarlar panel (`SidePanel`, F9)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-091 | Panel (accessible name "Dışa aktarma ayarları") | QWidget | `SidePanel` | D-61 | 368 px at 100 %, 440 at 150 %; minimum 320 |
| E-092 | Lock note icon (lock) | QLabel pixmap | `SidePanel.lock_icon` | D-38 | while writing |
| E-093 | Lock note "Yazma sürerken ayarlar değiştirilemez." | QLabel wrapped | `SidePanel.lock_text` | D-38 | while writing |
| E-094 | Cards scroll area "Ayrıntılar" | QScrollArea | `SidePanel.scroll` | D-62 | horizontal bar off; content can be wider than the viewport (F-disa-aktar-05) |
| E-095 | Group label "Hedef klasör" | QLabel group | `_group` | D-14 | - |
| E-096 | Target folder field (placeholder "Klasör seçilmedi") | QLineEdit | `SidePanel.folder` | D-14 | placeholder contrast 3.29 : 1 light (F-disa-aktar-20); red bottom edge when blocked |
| E-097 | Folder button (icon folder-open, tooltip "Klasör seç") | QPushButton | `SidePanel.choose_button` | D-14 | opens QFileDialog "Boş bir klasör seçin" |
| E-098 | Folder hint icon (info / ok / ban) | QLabel pixmap | `HintLine.icon` | D-15 | - |
| E-099 | Folder hint text (8 sentences) | QLabel wrapped | `HintLine.text` | D-15 | announced to the screen reader |
| E-100 | Group label "Dosya adı kalıbı" | QLabel group | `_group` | D-18 | - |
| E-101 | Pattern field (placeholder "Şablondaki kalıplar kullanılır" / "Kalıp yok") | QLineEdit | `SidePanel.pattern` | D-18 | commits on Enter or focus out |
| E-102 | Değişken ekle button (braces icon, chevron) | PartsButton | `SidePanel.variable_button` | D-19 | off while writing or with no variables |
| E-103 | Değişken menu | QMenu | `SidePanel.variable_menu` | D-19 | sorted without regard to case |
| E-104 | Değişken menu items | QAction | `_fill_variables` | D-19 | insert {name} at the cursor |
| E-105 | Menu item "Değişken yok" (disabled) | QAction | `_fill_variables` | D-19 | - |
| E-106 | Pattern hint ("Örnek: <name>" or the error) | HintLine | `SidePanel.pattern_hint` | D-20 | a long unbroken word widens the panel (F-disa-aktar-05) |
| E-107 | Group label "Seçenekler" | QLabel group | `_group` | D-24 | - |
| E-108 | Checkbox "Metin katmanı ekle (OCR)" (tooltip) | QCheckBox | `SidePanel.layer` | D-24 | checked by default; not remembered |
| E-109 | Checkbox "index.xlsx her zaman yazılır" (checked, disabled) | QCheckBox | `SidePanel.index_box` | D-25 | stays disabled |
| E-110 | Checkbox "Geçersiz karakterleri değiştir" | QCheckBox | `SidePanel.chars_box` | D-26 | snaps back on when unchecked |
| E-111 | Checkbox tooltip "Windows'un kabul etmediği karakterler ... kapatılamaz." | QToolTip | `CHARS_LOCKED` | D-26 | also the accessible description |
| E-112 | Primary "Dışa aktar  Ctrl+E" (download icon) | PartsButton primary lg | `SidePanel.export_button` | D-36 | off while an Engel exists and while writing |
| E-113 | Note "Önce engeli giderin." / "Önce iki engeli giderin." / "Önce N engeli giderin." | HintLine | `SidePanel.note` | D-04 | also the accessible description of the button |
| E-114 | "Yeniden dışa aktar…" button (refresh icon) | PartsButton | `SidePanel.again_button` | D-51 | replaces the primary after writing |

## 8. Status bar

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-115 | Window count "N belge" | StatusItem | `main_window.py` status counts | D-60 | - |
| E-116 | Window count "N sayfa" | StatusItem | same | D-60 | - |
| E-117 | Window count "N belge kontrol bekliyor" | StatusItem | same | D-60 | - |
| E-118 | Tab state item (icon + text) | StatusItem | `DisaAktarScreen.status_items['state']` | D-60 | six texts (Hedef klasör yazılabilir / seçilmedi / N engel var / Yazılıyor: x / y / N belge yazıldı, 14:32 / İşler Yükle sekmesinde açılır (Ctrl+1)) |
| E-119 | Status line with no job | StatusItem | `_sync_status` | D-02 | "İşler Yükle sekmesinde açılır (Ctrl+1)" alone at the left edge |

## 9. Dialogs, toasts and system surfaces

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-120 | Folder dialog "Boş bir klasör seçin" | QFileDialog (native) | `choose_folder` | D-14 | title says empty; a full folder is chosen then refused by the Engel row |
| E-121 | Print dialog "Dizini yazdır" | QPrintDialog (native) | `print_index` | D-53 | also opens while writing |
| E-122 | Printed index (name, "N belge, M sayfa", table Durum / Dosya adı / Sayfalar / Şablon / Not) | QTextDocument | `index_html` | D-53 | prints all rows, not the filtered view |
| E-123 | Close question "Bir iş sürüyor. Durdurup kapatılsın mı? ..." | QMessageBox | `main_window.py:closeEvent` | D-63 | - |
| E-124 | Toast "Dışa aktarılamıyor: <first Engel>" | Toast (info) | `DisaAktarScreen.export` | D-36 | names the first Engel only |
| E-125 | Toast "“x” klasörü oluşturuldu." | Toast (info) | `make_subfolder` | D-17 | - |
| E-126 | Toast "N belge yazıldı" / "Dışa aktarma durduruldu" with "Klasörü aç" | Toast | `_finish` | D-50 | 10 s; 4 px outside the right edge of the window (F-disa-aktar-24) |
| E-127 | Taskbar progress | taskbar | `_progress`, `_failed` | D-39 | not observable offscreen |
| E-128 | Taskbar flash at the end | QApplication.alert | `_attention` | D-50 | not observable offscreen |
| E-129 | Screen-reader announcements (hint lines, outcome card) | announce() | `ui/feedback.py` | D-62 | not observable offscreen |
| E-130 | Launches: default app for the folder / index.xlsx, Explorer selection | QDesktopServices, explorer | `open_path`, `reveal_path` | D-52 | replaced by stubs in the audit |
| E-131 | Ayarlar > Saklama > "İşi sakla" (outside this tab, drives the end of a run) | Settings dialog | `settings_dialog.py`; `_done` | D-55 | "Tam dışa aktarınca sil" deletes the job (B-008) |
| E-132 | Ayarlar > Dışa aktarma > default folder (outside this tab, pre-fills the field) | Settings dialog | `_prefill_folder` | D-59 | - |

