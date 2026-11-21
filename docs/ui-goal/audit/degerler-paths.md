# Değerler audit: click paths

Phase 4, Görev A, screen Değerler. Every click, double click, right click, drag, wheel and key on the elements of `degerler-inventory.md`, plus the common mistakes (double click on a
button, drag to the wrong place, cancel in the middle, close or resize during a task) and the Oku (read) flow in full: start, progress, finish, cancel, error in the middle, keys pressed
during a read, close and resize during a read. Driven with QTest on the synthetic demo job (`tools/screenshots.py:build`) and on the long-content jobs (30 documents x 8 variables with long
names, long values, flagged and empty values), window 1366x768, text 100 percent, light theme, offscreen. The read flow used a fake OCR engine (`FakeEngine` in the session scratchpad
`dh.py`): it can be held back one region at a time with a semaphore, made to raise after N regions (an `EngineUnavailable`, an `OSError` or a `RuntimeError`), or to report itself unavailable;
one run used the real Tesseract installed in this container on three synthetic documents (P-203). The file, folder and name dialogs and the close confirmation are replaced by stubs that
record the call and return a scripted answer. Scripts (session scratchpad, not committed): `d_paths.py`, `d_read.py`, `d_read2.py`, `d_read3.py`, `d_drag*.py`; raw tables:
`/tmp/claude-0/p4/degerler/paths/*.tsv`; screenshots of the moments named below: `/tmp/claude-0/p4/degerler/paths/*.png`.

Result: **203 paths tried, 170 pass, 32 fail, 1 gap**. The 32 failures are 15 distinct findings (F-degerler-01, 03, 04, 05, 06, 07, 08, 09, 13, 23, 25, 28, 29, 32, 34); rows with a
finding id and result "pass" are findings found by looking at what the passing path did (the Note column says what). Keywalk (Tab walk, `keywalk.py --tab degerler`) is separate and
passes in 24 of 24 combinations (3 themes x 1366x768 and 1920x1080 x text 100, 115, 130 and 150): no trap, nothing unnamed, work area reached, regions in reading order. By hand:
Tab walks every value cell (240 presses for 30 x 8, P-036) and then leaves the table; F6 moves between regions.

Rules of the table: "Expected" is what the product documents (PRODUCT.md, the research inventory, the tooltip or accessible name of the element) or, where nothing is documented, "records
behaviour" in the Note column. "Actual" is the measured value from the run. Pass means actual matches expected. Offscreen limits: the OS drag loop does not run (drags send
`QDragEnterEvent` and `QDropEvent` to the widget by hand); the Menu key and Shift+F10 as Qt key events open nothing offscreen, so the keyboard context-menu event was sent by hand
(P-014, P-015: whether Windows sends the same event for the keys was not checked); taskbar, Explorer and native dialogs do not exist; the system motion setting was not varied.
A double click on a button is two clicks with no pause (what Windows delivers to a push button); on the table it is a real double-click event.

Already in the ledger and seen again: B-050 (value keys stay enabled during a read: P-172 to P-174, Enter, N and F2 all work while a read runs), B-011 (fixed: P-162 shows the
finished documents kept when a read dies with an unexpected error), B-014 (failed documents look like unread: P-160), B-041 (the title-tab focus ring tool artefact).


### Table: clicks, double clicks, right clicks, header, wheel

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-001 | pass | table cell Belge | click | row selected; inspector shows that row's first value to check | current=(2, 'cdedfdea') selected rows=1 |  |  |
| P-002 | pass | table value cell | click | that value current; inspector shows it | current=(3, 'cdedfdea') title='Sicil No' |  |  |
| P-003 | pass | table review column | click | selects the row (no hidden toggle) | current=(1, 'cdedfdea') reviewed unchanged={'cdedfdea': ('48190', False, False, 0.95), '9222687d': ('Ege Kalıp San. Ltd.', False, False, 0.92)} |  |  |
| P-004 | pass | table empty area | click below the last row | selection kept or cleared with a clear sign | current=(1, 'cdedfdea') selected=0 |  | records behaviour |
| P-005 | pass | table row | Ctrl+click a second row | two rows selected | selected=2 |  |  |
| P-006 | pass | table row | Shift+click | range selected | selected=3 |  |  |
| P-007 | pass | table | Esc with several rows selected | reduces to the current row | selected=1 |  |  |
| P-008 | pass | table value cell | double click | opens the in-place editor | editing=True |  |  |
| P-009 | pass | table cell Belge | double click | no editor (not editable) | editing=False |  |  |
| P-010 | pass | table cell Sayfa | double click | no editor | editing=False |  |  |
| P-011 | pass | table row | right click | menu: Onayla..., Elle yaz, Yeni varyant çiz, Seçilenleri onayla, Tümünü seç, Tüm sayfayı göster, Sonraki kontrol, each with its key | ['Onayla ve sonrakine geç', 'Elle yaz', 'Yeni varyant çiz', '', 'Seçilenleri onayla', 'Tümünü seç', '', 'Tüm sayfayı göster', 'Sonraki kontrol']; enabled=[True, True, True, True, True, True, True] |  |  |
| P-012 | pass | context menu | key shown per item | shortcut text on each item | ['Return', 'F2', 'V', 'Ctrl+Return', 'Ctrl+A', 'Space', 'N'] |  |  |
| P-013 | pass | table empty area | right click | no menu | menu=None |  |  |
| P-014 | pass | table | keyboard context-menu event at the current cell centre (what Windows sends for a focused item view) | opens the menu for the current row | menu items=[['Onayla ve sonrakine geç', 'Elle yaz', 'Yeni varyant çiz']]; current (2, 'cdedfdea') -> (2, 'cdedfdea') |  | Key_Menu / Shift+F10 as Qt key events open nothing offscreen |
| P-015 | FAIL | table | keyboard context-menu event at the widget centre (the fallback) | opens the menu for the current row | menu items=[[]]; current (2, 'cdedfdea') -> (2, 'cdedfdea') | F-degerler-29 | unverified: Windows sends the position; offscreen the fallback is the widget centre |
| P-016 | pass | header Belge | click 1, 2, 3 times | asc, desc (documented: second click reverses) | before=(1, <SortOrder.AscendingOrder: 0>) after1=(1, <SortOrder.DescendingOrder: 1>) after2=(1, <SortOrder.AscendingOrder: 0>) after3=(1, <SortOrder.DescendingOrder: 1>) |  |  |
| P-017 | pass | header Sicil No | click 1, 2, 3 times | asc, desc (documented: second click reverses) | before=(1, <SortOrder.DescendingOrder: 1>) after1=(3, <SortOrder.AscendingOrder: 0>) after2=(3, <SortOrder.DescendingOrder: 1>) after3=(3, <SortOrder.AscendingOrder: 0>) |  |  |
| P-018 | pass | header review mark | click 1, 2, 3 times | asc, desc (documented: second click reverses) | before=(3, <SortOrder.AscendingOrder: 0>) after1=(0, <SortOrder.AscendingOrder: 0>) after2=(0, <SortOrder.DescendingOrder: 1>) after3=(0, <SortOrder.AscendingOrder: 0>) |  |  |
| P-019 | pass | header Güven | click 1, 2, 3 times | asc, desc (documented: second click reverses) | before=(0, <SortOrder.AscendingOrder: 0>) after1=(5, <SortOrder.AscendingOrder: 0>) after2=(5, <SortOrder.DescendingOrder: 1>) after3=(5, <SortOrder.AscendingOrder: 0>) |  |  |
| P-020 | pass | header | sections movable by drag? | no reordering (fixed order) | movable=False |  |  |
| P-021 | pass | header edge | drag right 60 px | column wider by about 60 | 150 -> 210 |  |  |
| P-022 | pass | header edge | drag far left (shrink to nothing) | column stops at a minimum | width 150 -> 40 after dragging the edge 320 px left; min=40; title 'Sicil No' is cut | F-degerler-13 | measured separately: dragged to the 40 px floor (the first attempt missed the edge) |
| P-023 | pass | header edge | double click | (common in tables) fit column to content, or nothing | 210 -> 210 |  | double click on the edge: nothing (no auto-fit) |
| P-024 | FAIL | header | way to reset column widths | a command to restore the default widths | none found: widths are saved per template (prefs) and there is no menu item or header menu | F-degerler-13 |  |
| P-025 | pass | table | wheel down | scrolls vertically if rows overflow | vscroll 0 -> 0 max=0 |  | demo has 3 rows: nothing to scroll |
| P-026 | pass | table | Ctrl+wheel | zooms the crop (status bar slider) or nothing | zoom None -> None |  | records behaviour |

### Table: keyboard

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-027 | pass | table | Down | moves the current cell | (0, 3) -> (1, 3) |  |  |
| P-028 | pass | table | Up | moves the current cell | (1, 3) -> (0, 3) |  |  |
| P-029 | pass | table | Right | moves the current cell | (0, 3) -> (0, 4) |  |  |
| P-030 | pass | table | Left | moves the current cell | (0, 4) -> (0, 3) |  |  |
| P-031 | pass | table | PageDown | moves the current cell | (0, 3) -> (7, 3) |  |  |
| P-032 | pass | table | PageUp | moves the current cell | (7, 3) -> (0, 3) |  |  |
| P-033 | pass | table | End | moves the current cell | (0, 3) -> (0, 11) |  |  |
| P-034 | pass | table | Home | moves the current cell | (0, 11) -> (0, 0) |  |  |
| P-035 | pass | table | Ctrl+End then Ctrl+Home | last row then first row | (29, 11) then (0, 0) |  |  |
| P-036 | pass | table | Tab repeatedly | walks every value cell then leaves the table (no trap) | 240 presses, 239 cells seen, focus left to QToolButton; value cells total=240 |  |  |
| P-037 | pass | table | Shift+Tab from the next control | focus returns to the last value cell | focus=ValuesTable cur=(29, 10) |  |  |
| P-038 | pass | table | Enter on a Kontrol value with a suggestion | accepts the suggestion, İncelendi, moves to the next Kontrol | (1, '891612d1') -> (1, 'bedd39ce'); changed=[(1, '891612d1')]; kontrol 44 -> 43 |  |  |
| P-039 | pass | table | Enter on an Okunamadı value | opens the editor | editing=True |  |  |
| P-040 | FAIL | editor | Enter with an empty text on an Okunamadı value | stays Kontrol / Okunamadı (nothing typed) | stored='' flagged=False edited=True level now=emin | F-degerler-04 |  |
| P-041 | pass | table | F2 | editor opens with the value (or the suggestion) | editing=True text='48001' |  |  |
| P-042 | pass | editor | Esc | drops the edit, focus back on the table | editing=False focus=ValuesTable |  |  |
| P-043 | pass | table | type a character on a value cell (type-to-edit) | starts editing, or nothing | editing=False; changed=False |  | records behaviour |
| P-044 | pass | table | Delete | nothing (no row deletion here) | changed=False editing=False |  |  |
| P-045 | pass | table | Backspace | nothing | changed=False |  |  |
| P-046 | pass | table | Space then Esc | page view opens; Esc closes and focus returns to the table | opened=True closed=True focus=ValuesTable |  |  |
| P-047 | FAIL | table | N | moves to the next/previous Kontrol value | N: (3, 5) -> (0, 3), then (0, 3) on every further press | F-degerler-01 | N went to the first Kontrol value from the top and stayed there on four presses (4 x N from (3,5): (0,3), (0,3), (0,3), (0,3)); the first run only saw a change of cell |
| P-048 | pass | table | Shift+N | moves to the next/previous Kontrol value | (2, '69a8b06e') -> (30, '1bb54884') |  |  |
| P-049 | pass | table | Ctrl+A | all rows selected | selected=30/30 |  |  |
| P-050 | pass | table | Ctrl+Enter with all rows selected | confirms every value as one undo step, toast with Geri al | changed 195 values; toast='195 değer onaylandı; okunamayan 21 değer atlandı'; undo text= |  | by design (V-58): one key confirms all 195 values incl. Emin and Orta; the toast names the number and carries Geri al |
| P-051 | pass | table | Ctrl+Z after Ctrl+Enter | all confirmations undone in one step | back to start=True |  |  |
| P-052 | pass | table | Ctrl+F | search field focused | focus=QLineEdit |  |  |
| P-053 | pass | table | F6 | focus moves to another region | focus=QToolButton |  | focus leaves the table on F6 (as designed) |
| P-054 | pass | Ctrl+G dialog | go to 12 | selects that document, or says it is not in this view | current=(12, '1bb54884') message='' toast='195 değer onaylandı; okunamayan 21 değer atlandı' |  | stale toast text from the Ctrl+Enter step |
| P-055 | pass | Ctrl+G dialog | go to 0 | selects that document, or says it is not in this view | current=(1, '1bb54884') message='' toast='195 değer onaylandı; okunamayan 21 değer atlandı' |  | stale toast text |
| P-056 | pass | Ctrl+G dialog | go to 9999 | selects that document, or says it is not in this view | current=(30, '1bb54884') message='' toast='195 değer onaylandı; okunamayan 21 değer atlandı' |  | stale toast text |
| P-057 | pass | Ctrl+G dialog | go to page 25 | selects that document, or says it is not in this view | current=(9, '1bb54884') message='' toast='195 değer onaylandı; okunamayan 21 değer atlandı' |  | stale toast text |
| P-058 | pass | table | F9 twice | hides then shows the source panel | hidden after first=True visible after second=True |  |  |
| P-059 | pass | window | Ctrl+K | palette opens | ['CommandPalette'] |  |  |

### View switch, search, template picker

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-060 | pass | selector kontrol | click | view switches | view=kontrol rows=24 |  |  |
| P-061 | pass | selector incelenmemis | click | view switches | view=incelenmemis rows=30 |  |  |
| P-062 | pass | selector tumu | click | view switches | view=tumu rows=30 |  |  |
| P-063 | pass | selector | Right | next view (wraps) | view=kontrol |  |  |
| P-064 | pass | selector | Left | previous view (wraps) | view=tumu |  |  |
| P-065 | pass | selector | Space on a focused item | selects it (button) | view=tumu |  |  |
| P-066 | pass | selector kontrol | double click | stays on Kontrol | view=kontrol |  |  |
| P-067 | pass | selector kontrol | click the selected item again | stays selected (no toggle off) | view=kontrol checked=True |  |  |
| P-068 | pass | search | type 'ege' | rows filter | rows=7 |  |  |
| P-069 | pass | search | Down | (no documented key; Yükle moves to the first row) | focus=QLineEdit |  | records behaviour |
| P-070 | pass | search | Esc with text | clears the text (or leaves), documented? | text='' focus=QLineEdit |  | records behaviour |
| P-071 | pass | search | query with no match | empty state with 'Aramayı temizle' | empty visible=True title='Aramayla eşleşen değer yok' text='“zzz-yok” hiçbir değerde geçmiyor. Başka bir sözcük deneyin.' |  |  |
| P-072 | pass | empty state primary | click Aramayı temizle | search cleared, table back | text='' rows=30 focus=TitleTabs | F-degerler-09 | mouse click: focus falls to the title tabs when the button disappears; the keyboard version is RD-105 |
| P-073 | pass | search | i / I / İ / ı (Turkish letters) | i and İ match alike; I and ı match alike (V-41) | rows i=22 I=30 İ=22 ı=30 |  |  |
| P-074 | pass | search | paste 5000 characters | no hang, empty state | rows=0 empty visible=True text len shown=5053 |  |  |
| P-075 | pass | search | clear (x) button | present and 24 px | [('QToolButton', 38, 38, 'Temizle'), ('QToolButton', 22, 18, '')] | F-degerler-11 | the clear button is 38 x 38 in a 32 px field (see states: dbg-search) |
| P-076 | pass | table | Ctrl+F | search focused, text selected | focus=QLineEdit True |  |  |
| P-077 | pass | template combo | wheel over it (one template) | no change | index 0 -> 0 count=1 |  |  |
| P-078 | pass | template combo | two templates in use | both listed | ['Faaliyet Belgesi', 'Kapasite Raporu'] |  |  |
| P-079 | pass | template combo | wheel over the combo while not focused | should not change the template (scroll accident) | 'Kapasite Raporu' -> 'Kapasite Raporu' |  | Qt default: a mouse wheel over a combo changes the template, which changes every column and the rows |
| P-080 | pass | template combo | open popup then Esc | closes, no change | popup visible=True |  |  |
| P-081 | pass | template combo | switch template | table rebuilt for the other template; selection starts at its first value | template='Faaliyet Belgesi' rows=1 cols=5 current=(3, '05b2d99d') |  |  |

### Inspector (source card, value card, buttons)

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-082 | FAIL | inspector Onayla ve sonrakine geç | double click (two quick clicks) | one value accepted; the second click must not confirm a value the person has not looked at | started on (2, '2803f9d6'); now (3, '2803f9d6'); values changed=[(2, '2803f9d6'), (2, '106aa4c8')] | F-degerler-03 |  |
| P-083 | FAIL | inspector Onayla | Ctrl+Z after the double click | restores the values | 2 undo presses needed to get back | F-degerler-03 |  |
| P-084 | pass | inspector Elle yaz | click | editor opens in the table with focus in it | editing=True focus=QLineEdit |  |  |
| P-085 | pass | inspector Elle yaz | double click | editor open once | editing=True |  |  |
| P-086 | pass | inspector zoom_in | click 14 times | stops at the limit (50..400) | 200 -> 400 min=50 max=400 enabled=True |  |  |
| P-087 | pass | inspector zoom_out | click 14 times | stops at the limit (50..400) | 400 -> 50 min=50 max=400 enabled=True |  |  |
| P-088 | pass | crop | Ctrl+wheel | zoom the crop | 200 -> 225 |  | records behaviour |
| P-089 | pass | crop | wheel (plain) | scrolls the side panel (not the crop) | side vscroll=0 |  | records behaviour |
| P-090 | pass | crop | click empty page area | nothing | current=(2, '2803f9d6') |  |  |
| P-091 | pass | crop | double click | nothing | editing=False |  | records behaviour |
| P-092 | pass | crop | click another variable's box | selects that value in the table | current=(2, '106aa4c8') |  |  |
| P-093 | pass | inspector whole-page button | click | page view opens | open=True |  |  |
| P-094 | FAIL | page view | Esc | closes; focus returns to the button that opened it | focus=_Scroll False | F-degerler-23 | a click in the crop gave the side panel's scroll area the keyboard focus; the page view returned focus there |
| P-095 | pass | inspector Yeni kutu çiz | click | goes to Şablonlar with the variable selected | tab=2 |  |  |
| P-096 | pass | Şablonlar -> Değerler | come back | same value still selected | current=(2, '106aa4c8') |  |  |
| P-097 | pass | inspector Elle yaz | Space while the button has focus | presses the button (not the page view) | editing=True loupe=False |  |  |
| P-098 | pass | inspector Onayla | state on an unread value | disabled | enabled=False type enabled=True |  |  |

### Value editor and Örnek kontrol

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-099 | pass | editor | type 3000 characters, Enter | stored (no limit) and the row stays usable | stored len=3000 edited=True; row height=77 |  | no length limit: a 3000-character Sicil No is accepted (V-61) |
| P-100 | pass | editor | text with spaces and a newline | trimmed and joined | stored='48 190 x' |  | records behaviour |
| P-101 | pass | editor | type, then Tab | documented: Tab does not accept a typed text? (V-60: only typed text is stored) | stored=('TABBED', False, True, 1.0) editing=True current=(2, '4a0f4922') |  | records behaviour |
| P-102 | pass | editor | type, then click another cell | stores what was typed (V-60) | stored=('CLICKAWAY', False, True, 1.0) editing=False |  |  |
| P-103 | pass | editor | type, then switch tab and come back | typed text stored or kept | stored=('SWITCHTAB', False, True, 1.0) editing=False |  | records behaviour |
| P-104 | pass | editor | resize the window while typing | editor stays with its text | editor open=True text='RESIZED' |  |  |
| P-105 | pass | editor | Enter then Ctrl+Z | value restored | ('SWITCHTAB', False, True, 1.0) |  |  |
| P-106 | pass | editor | close the window with an editor open | typed text kept (stored) or asked | asked=[] stored=('CLOSING', False, True, 1.0) |  | records behaviour |
| P-107 | pass | Örnek kontrol | enter | rows listed (up to 20) | rows=20 cols=['', 'Belge', 'Sayfa', 'Değişken', 'Okunan değer', 'Güven'] |  |  |
| P-108 | pass | Örnek kontrol | type a different value for a sampled value | records one error, other values of that variable go to Kontrol, toast with Geri al | toast="Örnekte hata: 20 açıklama notu değeri Kontrol'e alındı" kontrol count now=64 |  |  |
| P-109 | pass | Örnek kontrol | Ctrl+Z after the error | error and the flagged values undone together | kontrol count=44 |  | records behaviour |

### Command bar, panel toggle, splitter

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-110 | pass | table | Enter on an unread value | nothing, with a hint (Değerleri oku ile okunur) | toast='Kontrol gereken değer kalmadı; 5 değer incelenmedi. Enter sıradakini onaylar.' message='' |  | records behaviour |
| P-111 | FAIL | command bar Sonraki kontrol | double click | moves to the next Kontrol twice (two steps) | two clicks: current stays (1, key); 4 single clicks in a row and a double click all stayed | F-degerler-01 | same cause: the bar button, the menu and the key call next_check(False) |
| P-112 | pass | command bar Tümünü incele | double click | toggles twice: ends where it began | checked=False view=tumu review_all=False |  |  |
| P-113 | pass | command bar Tümünü incele | click | switches to İncelenmemiş, steps every value | view=incelenmemis review_all=True toast='' |  |  |
| P-114 | pass | command bar Tümünü incele | click again | off, back to the previous view | view=tumu review_all=False |  |  |
| P-115 | pass | command bar Örnek kontrol | click | Örnek view with 20 values | view=ornek rows=20 |  |  |
| P-116 | pass | command bar Örnek kontrol | click again | back to the previous view | view=tumu |  |  |
| P-117 | pass | command bar Örnek kontrol | double click | ends where it began (off) | view=tumu |  |  |
| P-118 | pass | command bar Seçilenleri onayla | double click | second click is a no-op (everything already confirmed) | changed=196 undo steps now=2 |  |  |
| P-119 | pass | command bar Geri al | enabled after a confirm | enabled | True Geri al: 196 değeri onayla (Ctrl+Z) |  |  |
| P-120 | pass | command bar Geri al | double click | undoes two steps (documented) | undo index 2 -> 0 |  | two steps are undone with no confirmation; the label names the first step only |
| P-121 | pass | command bar Diğer komutlar | click | menu lists the commands that did not fit | [['&Tümünü seç', 'Onayl&a ve sonrakine geç', '&Elle yaz', 'Yeni &varyant çiz', 'Va&zgeç', '', 'Tüm sayfayı &göster', '']] |  | records |
| P-122 | pass | command bar panel toggle | double click | hidden then shown again | visible=True |  |  |
| P-123 | pass | splitter handle | drag far left | side panel widens up to a maximum, table keeps a minimum | side 376 -> 890 table=428 |  |  |
| P-124 | pass | splitter handle | drag far right | side panel keeps its minimum width | side=252 min=252 |  |  |
| P-125 | FAIL | splitter handle | keyboard focus + Left | (is the handle reachable by keyboard?) | focus policy=0 | F-degerler-25 |  |

### Window sizes below the matrix

1024x600 and 1280x720 are not in the screenshot matrix (1366x768 and 1920x1080). The clipping check lines are summarised in the Actual column; the full list is in `/tmp/claude-0/p4/degerler/paths/resize-*.png` and the run log.

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-126 | FAIL | window | 1024x600-class size (1024, 600) text 100 % | no clipping (matrix covers 1366x768 and 1920x1080 only) | ["degerler-1024-100 ValuesTable hücre (1, 4) kısaltılmış: 'Akçay Tekstil Sanayi ve Ticaret Limited Şirketi Organize Sanayi Bölgesi Şubesi Ankara Merkez Müdürlüğü Arşiv Birimi' (827>136)", 'degerler-1024-100 ValuesTable sütun 7 görünmüyor (yana kaydırmak gerekiyor)', 'degerler-1024-100 ValuesTable sütun 8 görünmüyor (yana kaydırmak gerekiyor)'] | F-degerler-28 |  |
| P-127 | FAIL | window | 1024x600-class size (1024, 600) text 150 % | no clipping (matrix covers 1366x768 and 1920x1080 only) | ["degerler-1024-150 ElidedLabel#jobName kısaltılmış: 'Kasım 2026 kapasite raporları – çok uzun iş adı için deneme' -> 'Kasım 2026 kapasite raporları …'", 'degerler-1024-150 SourceCard#- kaydırma kenarında yarım görünüyor', "degerler-1024-150 ValuesTable hücre (1, 4) kısaltılmış: 'Akçay Tekstil Sanayi ve Ticaret Limited Şirketi Organize Sanayi Bölgesi Şubesi Ankara Merkez Müdürlüğü Arşiv Birimi' (1269>221)"] | F-degerler-28 |  |
| P-128 | FAIL | window | 1024x600-class size (1280, 720) text 130 % | no clipping (matrix covers 1366x768 and 1920x1080 only) | ["degerler-1280-130 ValuesTable hücre (1, 4) kısaltılmış: 'Akçay Tekstil Sanayi ve Ticaret Limited Şirketi Organize Sanayi Bölgesi Şubesi Ankara Merkez Müdürlüğü Arşiv Birimi' (1104>189)", 'degerler-1280-130 ValuesTable sütun 7 görünmüyor (yana kaydırmak gerekiyor)', 'degerler-1280-130 ValuesTable sütun 8 görünmüyor (yana kaydırmak gerekiyor)'] | F-degerler-28 |  |

### Drag and drop

The OS drag loop does not run offscreen: drag events are sent to the widget by hand. Ids D-nnn here are renumbered in the table below.

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-129 | pass | table (viewport) | PDF dragged over it (QDragEnterEvent, offscreen: the OS drag loop does not run) | the window-wide drop overlay shows what a drop does (documented: "PDF'leri pencerenin herhangi bir yerine bırakın") | accepted=True; overlay visible=True (the Yükle overlay, tab is Değerler) |  |  |
| P-130 | pass | table (viewport) | PDF dropped on it | the batch is added to the open job | batches 1 -> 2; the window switched to Yükle; toast "ek.pdf eklendi."; Değerler rows unchanged |  | the tab switch is the Yükle drop handler's own behaviour |
| P-131 | pass | inspector crop | PDF dropped on it | same as the table | batches 2 -> 3; tab Yükle |  |  |
| P-132 | pass | table | internal drag of a value cell | nothing to drag | dragEnabled=False acceptDrops=False dragDropMode=NoDragDrop |  |  |
| P-133 | FAIL | empty state / table card | PDF dropped while a Değerler read is running | refused with "Dışa aktarma ya da okuma sürüyor; ..." like Ctrl+O, Ctrl+N and Ctrl+W (RD-05x) | accepted; batches 1 -> 2 while the read ran; docs 6 -> 7; tab jumped to Yükle; the read finished normally (6 rows) | F-degerler-34 | the job grows under a running read; results of the finished documents are unaffected |
| P-134 | pass | column header / splitter handle | drag to the wrong place (handle past either end, edge past the left end) | clamped | splitter: side panel 252 px minimum, table card 428 px at the other extreme; column floor 40 px (see P-022) |  |  |
| P-135 | GAP | cell editor | text dropped into the open editor | (Qt default: inserted) | not run: the script's F2 went to Yükle's rename dialog after the previous drop switched the tab; the editor itself has no custom drop code |  |  |

### Read flow (Oku): start, progress, finish, cancel, errors, keys, close, resize

Driven with a fake OCR engine that can be held back one region at a time (a semaphore), made to raise after N regions, or to report itself unavailable; one run with the real Tesseract on three synthetic documents. 12 documents x 8 variables unless said.

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-136 | pass | empty state primary | state before reading | Empty state with 12 belgeyi oku button | 'Değerler henüz okunmadı' / ' 12 belgeyi oku' |  |  |
| P-137 | pass | command bar Değerleri oku | click | busy; band shows Okunuyor 0 / 12 and the stop button | busy=True band=True label='Okunuyor: 0 / 12 belge' hint='elle yazdıklarınız korunur' cancel_vis=True dismiss_vis=False bar={'oku': False, 'eksik': False, 'tumunu': False, 'ornek': False, 'sonraki': False} |  |  |
| P-138 | pass | command bar Değerleri oku | state while reading | disabled while reading (no second read) | {'Şablonu olan': False, 'Yalnızca eksikleri': False, 'Emin olanlar': False, 'rastgele': False} |  |  |
| P-139 | FAIL | empty state primary '12 belgeyi oku' | state while reading | empty-state read button disabled while a read runs | primary enabled=True visible=True | F-degerler-32 | the button looks live; a click does nothing and says nothing (next row) |
| P-140 | pass | empty state primary | click while reading | ignored, no second task | busy=True task same=True; no feedback shown: label='Okunuyor: 0 / 12 belge' | F-degerler-32 |  |
| P-141 | pass | progress band | after the first document | Okunuyor: 1 / 12 belge + time hint | busy=True band=True label='Okunuyor: 1 / 12 belge' hint='bir dakikadan az kaldı, elle yazdıklarınız korunur' cancel_vis=True dismiss_vis=False bar={'oku': False, 'eksik': False, 'tumunu': False, 'ornek': False, 'sonraki': False} |  |  |
| P-142 | pass | progress band hint | hint text after document 1 | a time estimate | bir dakikadan az kaldı, elle yazdıklarınız korunur |  |  |
| P-143 | pass | taskbar progress | calls during a read | set(done, total) then clear() | [('set', 0, 12), ('set', 0, 12), ('set', 1, 12)] ... [('set', 12, 12), ('clear',)] (15 calls) |  |  |
| P-144 | pass | table card | during the read | (documented) nothing shown until the read ends | empty visible=True; table visible=True; rows read so far in the job = 0 (stored only at the end) | F-degerler-33 |  |
| P-145 | pass | read run | let it finish | 12 documents stored; toast '12 belge okundu.' | done=True stored=12 toasts=['12 belge okundu.'] band=False label='' |  |  |
| P-146 | pass | table | after the read | table shows rows; a value selected | rows=12 current=(1, 'cf94ffb7') focus=TitleTabs |  | focus is still on the title tabs because the mouse started the read |
| P-147 | pass | Ctrl+Z after a read | press | the whole read is one undo step | stored after undo=0; toasts=['12 belge okundu.'] |  |  |
| P-148 | pass | Ctrl+Y | press | read restored | 12 |  |  |
| P-149 | FAIL | cancel via button | click / key while document 3 is being read | a visible sign that stopping was requested (Yükle shows İptal ediliyor…) | label='Okunuyor: 2 / 12 belge'; hint='bir dakikadan az kaldı, elle yazdıklarınız korunur'; stop button visible=True enabled=True; busy=True | F-degerler-07 |  |
| P-150 | pass | cancel via button | let the running document finish | stops at the next document boundary; 3 documents kept; toast 'Okuma durduruldu: 3 belge okundu ve kaydedildi, kalanlar okunmadı.' | stored=3 toast='Okuma durduruldu: 3 belge okundu ve kaydedildi, kalanlar okunmadı.' band=False |  |  |
| P-151 | FAIL | cancel via ctrl-dot | click / key while document 3 is being read | a visible sign that stopping was requested (Yükle shows İptal ediliyor…) | label='Okunuyor: 2 / 12 belge'; hint='bir dakikadan az kaldı, elle yazdıklarınız korunur'; stop button visible=True enabled=True; busy=True | F-degerler-07 |  |
| P-152 | pass | cancel via ctrl-dot | let the running document finish | stops at the next document boundary; 3 documents kept; toast 'Okuma durduruldu: 3 belge okundu ve kaydedildi, kalanlar okunmadı.' | stored=3 toast='Okuma durduruldu: 3 belge okundu ve kaydedildi, kalanlar okunmadı.' band=False |  |  |
| P-153 | FAIL | cancel via menu | click / key while document 3 is being read | a visible sign that stopping was requested (Yükle shows İptal ediliyor…) | label='Okunuyor: 2 / 12 belge'; hint='bir dakikadan az kaldı, elle yazdıklarınız korunur'; stop button visible=True enabled=True; busy=True | F-degerler-07 |  |
| P-154 | pass | cancel via menu | let the running document finish | stops at the next document boundary; 3 documents kept; toast 'Okuma durduruldu: 3 belge okundu ve kaydedildi, kalanlar okunmadı.' | stored=3 toast='Okuma durduruldu: 3 belge okundu ve kaydedildi, kalanlar okunmadı.' band=False |  |  |
| P-155 | pass | Yalnızca eksikleri oku | after a cancelled read | enabled, reads the rest | enabled=True |  |  |
| P-156 | pass | Yalnızca eksikleri oku | run after the cancel | reads only the 9 missing documents | stored=12 regions=72 (expected 72) toast='Okuma durduruldu: 3 belge okundu ve kaydedildi, kalanlar okunmadı.' | F-degerler-37 | the toast of the second read waits behind the first one's (6 s queue, F-kontrol-06 class) |
| P-157 | pass | Ctrl+Z twice after cancel + rest | undo | two read steps undone (each read is one step) | stored now=0 |  |  |
| P-158 | pass | Okumayı durdur | cancel while document 1 is being read | message names how many documents were kept | toast='Okuma durduruldu: 1 belge okundu ve kaydedildi, kalanlar okunmadı.' stored=1 |  | the running document is finished and kept, so the count is never 0 here; 'Okuma durduruldu: 1 belge okundu ve kaydedildi' is correct |
| P-159 | FAIL | read run | engine reports EngineUnavailable from document 3 on | reading goes on; the summary says how many failed and what to do | toasts=['12 belge okundu.'] band=False:'' errors stored=10 read ok docs=2 | F-degerler-05 |  |
| P-160 | FAIL | table / inspector | select a document whose read failed | the table row and the inspector say it failed and what to do | rows with error=10; first error text='Tesseract çalışmadı (sahte hata)'; inspector why='Bu değer henüz okunmadı. Değerleri oku ile okunur. Tesseract çalışmadı (sahte hata)'; level word=True; status=[('doc', True), ('kontrol', False), ('bad', False), ('seen', True), ('sample', False), ('errors', False), ('unread', False)] | F-degerler-05 | the inspector says 'Bu değer henüz okunmadı. Değerleri oku ile okunur.' and then the raw engine text |
| P-161 | FAIL | status bar | after per-document errors | a count of failed documents | status items visible=['doc', 'seen']; unread text='12 belgede şablon var, değer okunmadı' | F-degerler-05 | no count of failed documents anywhere |
| P-162 | pass | read run | unexpected exception in document 3 (B-011) | documents 1 and 2 kept; band 'Okunamadı: ...'; busy off | stored=2 busy=False band=True label='Okunamadı: beklenmeyen sahte hata' cancel_vis=False dismiss_vis=True |  |  |
| P-163 | FAIL | error band text | read the message | Turkish, says what to do next | 'Okunamadı: beklenmeyen sahte hata' | F-degerler-06 |  |
| P-164 | pass | Mesajı kapat | click | band closes | band=False |  |  |
| P-165 | pass | Yalnızca eksikleri oku | after a failed read | reads the rest | stored=12 regions=80 |  |  |
| P-166 | pass | read run | engine not available | refusal band, nothing touched | busy=False label='Okunamadı: Tesseract programı bulunamadı: tesseract.exe yolda değil' cancel_vis=False stored=0 |  |  |
| P-167 | pass | default engine | available() in this container | (info) real Tesseract state | reason=None |  |  |
| P-168 | FAIL | read run | OSError in documents 2..12 | same as P-159 | toasts=['12 belge okundu.'] errors=11 | F-degerler-05 |  |
| P-169 | pass | read over existing values, engine fails from document 2 | re-read with errors | earlier values and corrections of a failed document are kept | errors=11; docs with values=12; first row level=okunamadi; row 2 cell texts=[('48001', 'emin'), ('Akçay Tekstil Sanayi ve Ticaret Limited Şirketi Organize Sanayi Bölgesi Şubesi Ankara Merkez Müdürlüğü Arşiv Birimi', 'emin'), ('137,50', 'emin')] |  |  |
| P-170 | FAIL | toast after errors | read finishes with 11 failed documents | toast or band says how many failed and what to do | toast='12 belge okundu.' | F-degerler-05 |  |
| P-171 | pass | table | read started over a table that already has values | table stays usable | table visible=True rows=12 |  |  |
| P-172 | pass | Enter during a read | press on a value | accepts and moves on, as without a read | before=(2, '49b3aed6') after=(2, '859c749b') |  | ledger B-050: value keys stay enabled during a read (Enter accepts, N moves, F2 edits); here that is harmless because the read stores through the same undo stack and a typed edit wins |
| P-173 | FAIL | N during a read | press | next kontrol | current=(1, '49b3aed6') | F-degerler-01 | ledger B-050; and N lands on the first Kontrol value (current stays (1, key)), F-degerler-01 |
| P-174 | pass | F2 during a read | press | editor opens | editor=True |  | ledger B-050 |
| P-175 | pass | open editor | read finishes while typing | the typed text and editor survive (V-88) | editor open=True text='48000ELLE' |  |  |
| P-176 | pass | Ctrl+W (close job) | press during a read | refused with a Turkish message, or harmless | busy=True tab=3 job_open=True message='Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın.' toasts=[''] |  |  |
| P-177 | pass | Ctrl+N (new job) | press during a read | refused with a Turkish message, or harmless | busy=True tab=0 job_open=True message='Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın.' toasts=[''] |  |  |
| P-178 | pass | Ctrl+O (add file) | press during a read | refused with a Turkish message, or harmless | busy=True tab=0 job_open=True message='Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın.' toasts=[''] |  |  |
| P-179 | pass | Ctrl+E (export) | press during a read | refused with a Turkish message, or harmless | busy=True tab=0 job_open=True message='Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın.' toasts=[''] |  |  |
| P-180 | pass | Ctrl+S | press during a read | refused with a Turkish message, or harmless | busy=True tab=0 job_open=True message='Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın.' toasts=[''] |  |  |
| P-181 | pass | tab switch | Kontrol then back to Değerler during a read | band and stop button still there | busy=True band=True label='Okunuyor: 1 / 12 belge' hint='bir dakikadan az kaldı, elle yazdıklarınız korunur' cancel_vis=True dismiss_vis=False bar={'oku': False, 'eksik': False, 'tumunu': False, 'ornek': False, 'sonraki': False} |  |  |
| P-182 | pass | Yükle tab | look during a Değerler read | (info) does the app say a read runs elsewhere? | busy screens=['DegerlerScreen'] status message='Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın.' |  |  |
| P-183 | pass | view switch / search / sort during a read | use them | harmless | busy=True view=tumu |  |  |
| P-184 | pass | Ctrl+Z during a read | undo while documents are being read | undo refused or the read stays correct | busy=True undo now enabled=False text='&Geri al' | F-degerler-08 |  |
| P-185 | pass | Ctrl+Z during a read | undo the template application while reading | undo refused during a read, or the result still names what happened | undo enabled now=False; documents with a template now=0 | F-degerler-08 |  |
| P-186 | FAIL | read result after the undo | read finishes | a message that explains the skipped documents | toast='0 belge okundu.'; stored=0; rows=0 | F-degerler-08 |  |
| P-187 | pass | close window, answer no | close during a read | asks once; No keeps everything; Yes stops and closes after the running document | asked=['Bir iş sürüyor. Durdurup kapatılsın mı? Yazılmış dosyalar klasörde kalır.'] visible=True busy=True message='' cancel_vis=True |  |  |
| P-188 | pass | close window, answer yes | close during a read | asks once; No keeps everything; Yes stops and closes after the running document | asked=['Bir iş sürüyor. Durdurup kapatılsın mı? Yazılmış dosyalar klasörde kalır.'] visible=False busy=False message='Durduruluyor… Pencere iş durunca kapanır.' cancel_vis=False |  |  |
| P-189 | pass | close window, Yes | after the running document finishes | window closes; read ones saved | visible=False stored=1 |  |  |
| P-190 | pass | Değerleri oku | double click | one read only | regions read=96 (one read = 96); stored=12 |  |  |
| P-191 | pass | command bar Değerleri oku | Space while focused | read starts | busy=True focus now=TitleTabs:'Sekmeler' | F-degerler-09 | result 'pass' = the read started; the focus finding is in the Actual column |
| P-192 | pass | Okumayı durdur button | Tab order while a read runs | reachable by Tab (Ctrl+. also works) | in tab order=True; focus policy=11; position=7/16 |  |  |
| P-193 | FAIL | keyboard focus after a read started from the command bar | after the read finishes | focus stays on the button or goes to the table | focus=TitleTabs 'Sekmeler' | F-degerler-09 |  |
| P-194 | pass | empty state '12 belgeyi oku' | Space while focused | read starts | busy=True focus=QPushButton |  |  |
| P-195 | FAIL | keyboard focus after the read started from the empty-state button | after the read finishes (button hidden) | focus moves to the table (the work area), not to the title tabs | focus=TitleTabs:'Sekmeler' | F-degerler-09 |  |
| P-196 | FAIL | empty state 'Aramayı temizle' | Space while focused | focus lands in the search field or the table | focus=TitleTabs:'Sekmeler' | F-degerler-09 |  |
| P-197 | pass | progress band | reading at text 150 %, window 1366x768 | no clipping | ['read-band-150-1366 ValuesTable sütun 8 görünmüyor (yana kaydırmak gerekiyor)', 'read-band-150-1366 ValuesTable sütun 9 görünmüyor (yana kaydırmak gerekiyor)', 'read-band-150-1366 ValuesTable sütun 10 görünmüyor (yana kaydırmak gerekiyor)', 'read-band-150-1366 ValuesTable sütun 11 görünmüyor (yana kaydırmak gerekiyor)'] |  |  |
| P-198 | FAIL | progress band | resize the window to 900x560 during a read | no clipping | ["resize ElidedLabel#jobName kısaltılmış: 'Kasım 2026 kapasite raporları – çok uzun iş adı için deneme' -> 'Kasım 2026 kapasite raporları…'", "resize QLabel#- kısaltılmış: 'Okunuyor: 2 / 12 belge' (249>239)", "resize QLabel#- kısaltılmış: 'bir dakikadan az kaldı, elle yazdıklarınız korunur' (518>239)", 'resize SourceCard#- kaydırma kenarında yarım görünüyor'] | F-degerler-28 |  |
| P-199 | FAIL | progress band | reading at text 150 %, window 1024x600 | no clipping | ["read-band-150-1024 ElidedLabel#jobName kısaltılmış: 'Kasım 2026 kapasite raporları – çok uzun iş adı için deneme' -> 'Kasım 2026 kapasite raporları …'", "read-band-150-1024 QLabel#- kısaltılmış: 'Okunuyor: 0 / 12 belge' (250>239)", "read-band-150-1024 QLabel#- kısaltılmış: 'elle yazdıklarınız korunur' (270>239)", 'read-band-150-1024 SourceCard#- kaydırma kenarında yarım görünüyor'] | F-degerler-28 |  |
| P-200 | FAIL | progress band | resize the window to 900x560 during a read | no clipping | ["resize ElidedLabel#jobName kısaltılmış: 'Kasım 2026 kapasite raporları – çok uzun iş adı için deneme' -> 'Kasım 2026 kapasite raporları …'", "resize QLabel#- kısaltılmış: 'Okunuyor: 2 / 12 belge' (249>239)", "resize QLabel#- kısaltılmış: 'bir dakikadan az kaldı, elle yazdıklarınız korunur' (518>239)", 'resize SourceCard#- kaydırma kenarında yarım görünüyor'] | F-degerler-28 |  |
| P-201 | pass | progress band | reading at text 100 %, window 1024x600 | no clipping | ['read-band-100-1024 ValuesTable sütun 8 görünmüyor (yana kaydırmak gerekiyor)', 'read-band-100-1024 ValuesTable sütun 9 görünmüyor (yana kaydırmak gerekiyor)', 'read-band-100-1024 ValuesTable sütun 10 görünmüyor (yana kaydırmak gerekiyor)', 'read-band-100-1024 ValuesTable sütun 11 görünmüyor (yana kaydırmak gerekiyor)'] |  |  |
| P-202 | FAIL | progress band | resize the window to 900x560 during a read | no clipping | ['resize ValuesTable sütun 8 görünmüyor (yana kaydırmak gerekiyor)', 'resize ValuesTable sütun 9 görünmüyor (yana kaydırmak gerekiyor)', 'resize ValuesTable sütun 10 görünmüyor (yana kaydırmak gerekiyor)', 'resize ValuesTable sütun 11 görünmüyor (yana kaydırmak gerekiyor)'] | F-degerler-28 |  |
| P-203 | pass | real Tesseract | read 3 synthetic documents (default engine, no fake) | finishes, flags empty boxes as Okunamadı | took 1.6s; state=''; toasts=['3 belge okundu.']; stored=3; values=[('Sicil No', 'okunamadi'), ('Firma Adi', 'okunamadi'), ('Tutar', 'okunamadi')] |  |  |
