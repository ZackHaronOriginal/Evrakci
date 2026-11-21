# Rehber audit: element inventory

Phase 4, Görev A, screen Rehber. Starts from `docs/ui-goal/research/inventory-rehber.md` (feature rows R-01..R-33, observations 1 to 12). That file answers "what can the user do"; this one answers "what is on the screen". Each element has an ID `E-nnn`, which the other audit files use (E-000 is the main window itself, for size, drops and the tools). "Research" names the feature row it belongs to; "Kind" is the Qt class or the kind of surface.

Element count: **76 numbered elements** in 6 groups (6 shared chrome, 10 command bar, 22 reading card, 18 side panel, 6 status bar, 14 dialogs, toasts, menus and outputs) plus E-000. Keys, pointer gestures and drags are not elements: they are in `rehber-paths.md`.

Screen states of Rehber (each has its own set of visible elements): **guide** (the reading card shows the guide, the tip and the contents list marks a section), **search with hits** (hit marks, counts in the contents list, "N sonuç, i / N", status "N sonuç: term"), **search without hits** (the card is replaced by the "no result" state, no contents row is marked), **tip dismissed**, **guide file missing** (one generated section), **side panel hidden** (F9). The tab needs no job: it opens the same with no job (P-004 and the "Rehber without a job" row).

Demo data: `tools/screenshots.py:build` (a job of 3 documents, 15 pages, two templates, one blank page) for the default states; the guide itself is the shipped `docs/tarama-rehberi.md` (6 sections plus the generated "Kısayollar", 1,693 px tall at 100 %). Synthetic variants built for this audit (invented text, never committed, in the session scratchpad): a 30-section guide with long titles and an unbroken run, 8 to 15 short sections, and a missing guide file.

Tab order measured by `keywalk.py --tab rehber` (identical in light, dark, hc, 100, 115, 130 and 150 percent, 1366x768 and 1920x1080, 24 of 24 clean): job switch, search box, menu button, command bar (Bul, Ayıraç sayfasını yazdır, PDF olarak aç, Kısayollar, Yardım konuları, side panel button, Diğer komutlar), reading card, search field, contents list, count box, Yazdır, then the three zoom controls of the status bar. The two chevron buttons and the two command-bar result buttons join the walk only while a search has hits; the title tab strip is the first stop of a full Tab round (Tab from the last zoom control).

## 0 Shared chrome visible on Rehber (audited once in `kontrol-inventory.md` E-001 to E-006)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-000 | Main window (size, drag and drop target, tools) | MainWindow | `ui/main_window.py` | R-01 | minimum size 911x549; takes a PDF dropped anywhere as a scan (P-183) |
| E-001 | Tab strip Yükle / Kontrol / Şablonlar / Değerler / Dışa Aktar / Rehber | TitleTabs (QTabBar) | `ui/chrome.py:TitleTabs` | R-01 | Rehber is the sixth tab; at 150 % text and 1366 wide it sits inside the "»" menu unless it is the current tab (F-yukle-23 applies) |
| E-002 | Job switch (job name, save state) | JobSwitch | `ui/titlebar.py` | none | shows the open job, not the guide |
| E-003 | Entry from outside: Yükle inspector row "Rehber'de tarama ayarları" (job open only), and F1 | `_LinkButton` in `ProfileRows` | `ui/yukle_side.py:162-166`, `main_window.py:697` | R-02 | the empty Yükle page has no link (F-rehber-10) |
| E-004 | Search box "Ara  Ctrl+K" | SearchBox | `ui/palette.py` | R-27 | opens the palette; it is the app's, not the guide's search |
| E-005 | Menu button (Dosya, Düzen, Görünüm, Git, Yardım) | QToolButton | `ui/titlebar.py` | R-27 | holds the print and PDF entries under Dosya |
| E-006 | Caption buttons | CaptionButton x3 | `ui/titlebar.py` | none | NoFocus by design |

## 1 Command bar

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-007 | Bul (Ctrl+F) | ActionButton | `main_window.py:COMMANDS['rehber']`, `app.bul` | R-11 | focuses the search field; shows the side panel if F9 hid it |
| E-008 | Önceki sonuç (Shift+F3) | ActionButton | `app.onceki_sonuc` | R-14 | grey with no hits (not in the Tab walk then) |
| E-009 | Sonraki sonuç (F3) | ActionButton | `app.sonraki_sonuc` | R-14 | same |
| E-010 | Separators and the grow spacer (2) | QFrame | command bar | R-27 | not focusable |
| E-011 | Ayıraç sayfasını yazdır (Ctrl+P) | ActionButton, printer icon | `rehber.yazdir` | R-21 | opens the system print dialog |
| E-012 | PDF olarak aç | ActionButton, external-link icon | `rehber.pdf_ac` | R-23 | no key; also in Dosya |
| E-013 | Kısayollar (labelled, Shift+F1) | ActionButton | `app.kisayollar` | R-27 | opens the shortcut sheet for the whole app |
| E-014 | Yardım konuları (F1) | ActionButton, help icon | `app.yardim` | R-02 | switches to this tab (already here: no change) |
| E-015 | Yan paneli gizle (F9) | ActionButton | `app.yan_panel` | R-30 | tooltip turns to "Yan paneli göster (F9)" while hidden |
| E-016 | Diğer komutlar (overflow) | QToolButton + menu | `ui/chrome.py` | R-27 | holds what does not fit at 150 % text |

## 2 Reading card (left)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-017 | Card frame ("Tarama rehberi") | QFrame kind=card | `rehber.py:99-110` | R-01 | takes the focus ring when the reader has focus (2 px outer, 1 px inner) |
| E-018 | Reader scroll bar | QScrollBar (9 px) | Reader | R-09 | vertical only; horizontal is off; AUD-WIN-02 fails on it (F-rehber-16) |
| E-019 | Reader (the guide text) | `Reader` (QTextBrowser), read-only | `rehber_reader.py` | R-09 | wheel, PgUp/PgDn, Home/End, arrows, Space scroll; Tab leaves; Ctrl+wheel and Ctrl+plus/minus zoom |
| E-020 | Title "Tarama rehberi" | heading level 1, page-title size | `rehber_content.py:guide_html` | R-04 | |
| E-021 | Lead sentence (secondary colour) | paragraph | same | R-04 | wraps to 2 lines at 1366x768 |
| E-022 | Tip icon (info) | image resource `rehber:info` | `rehber_reader.py:show_guide` | R-08 | |
| E-023 | Tip banner "Ctrl+F ile rehberde arayın, Ctrl+tekerlek ile yazıyı büyütün." | table with `well` fill | `rehber_content.py:281-300` | R-08 | no box in hc (F-rehber-27); searchable text |
| E-024 | Section headings x7 (Hazırlık, QR ayıraç sayfaları, Küçük makbuzlar, Tarayıcı ayarları, Yükleme, Sonrası, Kısayollar) | heading level 2 | same | R-04 | the contents list and the status line follow them |
| E-025 | Numbered step lists (3 lists, 9 steps) | table with number column | `rehber_content.py:_block_html` | R-04 | number in its own 32 px column |
| E-026 | Bullet lists (3 lists) | table with bullet column | same | R-04 | |
| E-027 | Sub-heading "Bilmeniz gerekenler" | semibold paragraph | same | R-04 | |
| E-028 | Inline code span (`evrakci ayirac ayirac.pdf --adet 10`) | span, fixed-width font | `rehber.py:mono_stack` | R-04 | on a `well` fill; staff-facing command in a guide (F-rehber-30) |
| E-029 | Bold runs (orijinal sırasıyla, zımba sökücü, cam üzerinden) | span weight 600 | `rehber_content.py:inline` | R-04 | |
| E-030 | Table "Tarayıcı ayarları" (Ayar / Önerilen, 4 rows) | table | `rehber_content.py:_block_html` | R-05 | |
| E-031 | Table "Kısayollar" (Kısayol / Ne yapar, 9 rows, generated from the registry) | table | `rehber_content.py:157-190` | R-06 | writes key names through Qt's Turkish translation (F-rehber-05, -06) |
| E-032 | Hit marks (other hits: soft fill and accent underline; current hit: accent fill, light text) | extra selections | `rehber_reader.py:_paint` | R-13 | contrast 13.40 / 7.56 (light), 8.97 / 8.70 (dark), 21.00 / 14.37 (hc) |
| E-033 | Sentence under "Kısayollar" ("Bu sekmede geçerli tuşlar. Diğer sekmelerin tuşları için **Üst Karakter+F1** tuşuna basın.") | generated paragraph | `rehber_content.py:KEYS_LEAD` | R-06 | |
| E-034 | Default text context menu (Kopyala, Bağlantı Konumunu Kopyala, Tümünü Seç) | QMenu (Qt) | none of our own | R-31 | not drivable offscreen; keys shown as "Kontrol+C" |
| E-035 | Text selection (mouse, Ctrl+A, Ctrl+C) | QTextCursor | Reader | R-31 | read-only |
| E-036 | Tip link "Bir daha gösterme" | anchor `rehber:gizle` | `rehber.py:_link` | R-08 | reachable by mouse only (F-rehber-08) |
| E-037 | "No result" state: 48 px mark, title "“x” için sonuç yok", sentence, buttons "Aramayı temizle" (primary) and "Kısayolları göster", "Sık aranan konular: ayıraç, çözünürlük, zımba, makbuz" | `EmptyResults` | `rehber_parts.py:176-250` | R-16 | replaces the reader while the query has no hit |
| E-038 | "Guide file missing" state: title and "Rehber dosyası bulunamadı." in the reader | generated | `rehber_content.py:MISSING` | R-03 | still adds the Kısayollar section |

## 3 Side panel (right, 368 px at 100 %, 440 px at 150 %)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-039 | Side panel with its card scroller (scrolls card by card at 150 %) | QWidget + QScrollArea + `CardScroll` | `rehber.py:111-142`, `card_scroll.py` | R-01 | hidden by F9; hides a card that is taller than the panel (F-rehber-11) |
| E-040 | Search field: lead icon, placeholder "Rehberde ara", key hint "Kontrol+F" at the right, x button "Aramayı temizle" | `SearchField` (QLineEdit) | `rehber_parts.py:33-107` | R-11 | x is 22x18 (F-rehber-14); hint drawn in the field |
| E-041 | Result line ("7 bölüm, 2 dakikalık okuma" or "N sonuç, i / N") | QLabel | `rehber.py:_counts` | R-15 | announced 500 ms after a change |
| E-042 | Önceki sonuç chevron (Shift+F3) | QToolButton sm | `rehber.py:_small_button` | R-14 | disabled with no hits |
| E-043 | Sonraki sonuç chevron (F3) | QToolButton sm | same | R-14 | same |
| E-044 | Group label "İçindekiler" | QLabel | `rehber.py:_group` | R-18 | |
| E-045 | Contents card | QFrame kind=card | `rehber.py:_build_toc` | R-18 | fixed height = rows x row height |
| E-046 | Contents rows x7 | `TocList` (QListWidget) | `rehber_parts.py:113-170` | R-18 | click, arrows, type-ahead jump; follows scrolling; Enter does nothing (F-rehber-23) |
| E-047 | Hit counts at the right of each row (caption numerals) | delegate paint | `rehber_parts.py:_TocDelegate` | R-13 | 6.22:1 light, 4.98:1 dark on the marked row |
| E-048 | Group label "Ayıraç sayfası" | QLabel | `rehber.py:_group` | R-19 | |
| E-049 | Print card | QFrame kind=card | `rehber.py:_build_print` | R-19 | below the fold of the panel at 150 % and 1366x768 |
| E-050 | Label "Kaç adet" | QLabel (buddy of the box) | same | R-19 | |
| E-051 | Count box (1 to 200, default 20, no spin buttons) | QSpinBox | `rehber.py:229-244` | R-19 | tooltip "Yazdırılacak ayıraç sayfası sayısı (1 ile 200 arası)"; not remembered |
| E-052 | Unit label "sayfa" | QLabel | same | R-19 | counts sheets, not pages (F-rehber-03) |
| E-053 | Label "Kâğıt" | QLabel | same | R-20 | |
| E-054 | Paper line "A4, iki yüze aynı QR" | QLabel | `rehber.py:253` | R-20 | fixed text; no paper or duplex choice |
| E-055 | Yazdır (primary, printer icon, key hint "Kontrol+P") | `PartsButton` | `rehber.py:257-262` | R-21 | Space presses, Enter does not (F-rehber-07) |
| E-056 | Splitter handle between the reading card and the side panel | QSplitterHandle | `rehber.py:84-89` | R-29 | mouse only; remembered |

## 4 Status bar (Rehber's own items)

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-057 | "Bölüm 2 / 7" (numbers in the text colour) | `StatusText` | `rehber_parts.py:StatusText` | R-15 | follows the section being read |
| E-058 | "N sonuç: term" (only while searching) | `StatusText` | same | R-15 | long terms widen it (the zoom slider stays visible: S:long-status-light-1366x768-150) |
| E-059 | Zoom out button (-) | QToolButton 24x24 | `ui/zoomview.py:178` | R-10 | F-rehber-15 |
| E-060 | Zoom slider "Rehber yazısı yakınlaştırma düzeyi" (50 to 300) | QSlider | `ui/zoomview.py:ZoomSlider` | R-10 | |
| E-061 | Zoom in button (+) | QToolButton 24x24 | `ui/zoomview.py:196` | R-10 | F-rehber-15 |
| E-062 | Zoom percent ("%100") | QLabel | `ui/zoomview.py` | R-10 | |

## 5 Dialogs, toasts, menus, outputs and invisible things

| ID | Element | Kind | Where | Research | Notes |
|---|---|---|---|---|---|
| E-063 | System print dialog "Ayıraç sayfasını yazdır" | QPrintDialog | `rehber.py:605-616` | R-21 | cannot run offscreen; a stand-in was used |
| E-064 | Toast "N ayıraç sayfası (2N sayfa) yazıcıya gönderildi." (success, 6 s) | feedback `_Toast` | `rehber.py:624` | R-21 | covers Yazdır at 150 % (F-rehber-26) |
| E-065 | Toast "Ayıraç sayfaları yazdırılamadı: <reason>. PDF olarak açıp oradan yazdırabilirsiniz." with the action "PDF olarak aç" | `_Toast` kind info | `rehber.py:620-623` | R-22 | raw English reason (F-rehber-12) |
| E-066 | Toast "Ayıraç sayfaları PDF olarak yazılamadı: <reason>. Açık bir PDF görüntüleyiciyi kapatıp yeniden deneyin." with "Yeniden dene" | `_Toast` kind error | `rehber.py:600-602` | R-23 | |
| E-067 | The PDF viewer that opens `ayirac-sayfalari.pdf` (system) | external | `QDesktopServices.openUrl` | R-23 | not drivable; recorded |
| E-068 | Palette (Ctrl+K) entries for this tab: Ayıraç sayfasını yazdır, PDF olarak aç, Rehber (Git), Bul, Sonraki/Önceki sonuç, Yakınlaştır, Uzaklaştır | CommandPalette | `ui/palette.py` | R-27 | keywords "baskı ayraç" and "ayraç ayıraç sayfası baskı pdf" |
| E-069 | Menu entries: Dosya (Ayıraç sayfasını yazdır…, PDF olarak aç), Düzen (Bul…, Sonraki/Önceki sonuç), Görünüm (zoom), Git (Rehber), Yardım (Yardım konuları) | QMenu | `actions.menu_structure("rehber")` | R-27 | |
| E-070 | Shortcut sheet (Shift+F1) with the Rehber group | ShortcutSheet | `ui/shortcut_sheet.py` | R-06 | S:shortcut-sheet-rehber-light-1366x768-100 |
| E-071 | Screen-reader announcement of the result line (500 ms after a change, "Sonuç yok" on Enter) | accessible name + Alert | `rehber.py:_announce`, `feedback.py:36` | R-15 | not visible |
| E-072 | The printed separator sheet (A4, QR 90 mm, "AYIRAÇ" above, "Bu sayfa çıktıya girmez" below) | image | `pipeline/separator.py:30-58` | R-24 | the two labels print with missing-glyph boxes (F-rehber-02) |
| E-073 | The separator PDF file `ayirac-sayfalari.pdf` to `-20.pdf` in the data folder | file | `rehber.py:581-603` | R-23 | folder not named on screen (F-rehber-25) |
| E-074 | Command line twin `evrakci ayirac CIKTI.pdf --adet N` | CLI | `cli/main.py:27-31,76-78` | R-26 | default 10, unit "yaprak" |
| E-075 | Tooltips of this tab (search field, chevrons, count box, Yazdır, x button, command-bar buttons) | QToolTip | various | R-33 | all present; key names in them are the translated ones |
| E-076 | Remembered between runs: splitter position, zoom, the dismissed tip (not the count) | prefs | `rehber.py:attach` | R-29 | |
