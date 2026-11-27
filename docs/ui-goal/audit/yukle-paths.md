# Yükle audit: click paths

Phase 4, Görev A, screen Yükle. Every click, double click, right click, drag, wheel and key on the elements of `yukle-inventory.md`, plus the common
mistakes (double click on a button, drag to the wrong place, cancel in the middle, close or resize during a task). Driven with QTest on the synthetic
demo job (`tools/screenshots.py:build`) and on the long-content store, window 1366x768, text 100 percent, light theme, offscreen. Scripts (session
scratchpad): `paths.py`, `paths2.py`; raw table: `/tmp/claude-0/p4/yukle/paths/paths.tsv`; screenshots of the moments named below:
`/tmp/claude-0/p4/yukle/paths/*.png`. The file, folder and name dialogs and the close confirmation are replaced by stubs that record the call and
return a scripted answer; a real second click on a button cannot reach a modal dialog's parent, so double clicks on dialog-opening buttons only show
that the handler runs once per click.

Result: **151 paths tried, 130 pass, 21 fail**. The 21 failures are 12 distinct findings (F-yukle-02, F-yukle-03, F-yukle-04, F-yukle-13, F-yukle-14, F-yukle-15, F-yukle-16, F-yukle-17, F-yukle-18, F-yukle-19, F-yukle-20, F-yukle-36).
Keywalk (Tab walk, `keywalk.py --tab yukle`) is separate and passes in 14 of 14 combinations (3 themes x 1366x768 and 1920x1080 x text 100 and 150, plus text 115 and
130 in light): no trap, nothing unnamed, work area reached, regions in reading order. By hand: Tab on the empty page goes Yeni iş oluştur, Dosya ekle…,
the search field, the three job rows, then the title tabs (P-080); Down in the search field moves to the first row (P-081).

Rules of the table: "Expected" is what the product documents (PRODUCT.md, the research inventory, the tooltip or accessible name of the element). "Actual" is the
measured value from the run. Pass means actual matches expected. Offscreen limits: the OS drag loop does not run (drags call the model's drop handler or send
`QDragEnterEvent`/`QDropEvent` to the window's drop filter); the menu key is sent as a keyboard `QContextMenuEvent` by hand; taskbar, Explorer and
native dialogs do not exist. Whether Windows sends the same event for the Menu key and Shift+F10 was not checked.

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-001 | pass | table row | click row 3 | row 3 selected, inspector keeps the job summary | selected=b3 rows=5 |  |  |
| P-002 | FAIL | table Toplam row | click the Toplam row | selection unchanged (the row is not selectable) | selected=None | F-yukle-02 | a click on Toplam clears the selection and the focus ring; the move and remove buttons go grey |
| P-003 | pass | table empty area | click below the last row | selection unchanged (or cleared with a clear sign) | selected=None |  | selection was already cleared by P-002; the empty area itself changes nothing |
| P-004 | pass | table row | double click row | nothing destructive; ideally opens the batch in Kontrol | names unchanged=True, tab=yukle | F-yukle-37 | double click does nothing (no way into the batch) |
| P-005 | pass | table row | Enter on a row | does something sensible or nothing | tab=yukle | F-yukle-37 | nothing happens |
| P-006 | pass | row context menu | right click row | 4 entries: yukarı, aşağı, çıkar, Dosya Gezgini | ['Partiyi yukarı taşı', 'Partiyi aşağı taşı', 'Partiyi çıkar', "Dosya Gezgini'nde göster"] |  |  |
| P-007 | pass | row context menu | enabled state of the entries on row 2 | yukarı enabled, aşağı enabled | [('Partiyi yukarı taşı', True), ('Partiyi aşağı taşı', True), ('Partiyi çıkar', True), ("Dosya Gezgini'nde göster", True)] |  |  |
| P-008 | pass | row context menu | right click Toplam row | no menu, or a menu with nothing destructive for the shown selection | menu shows ['Partiyi yukarı taşı', 'Partiyi aşağı taşı', 'Partiyi çıkar', "Dosya Gezgini'nde göster"]; selected batch stays b2 |  | menu is built from the previous selection: 'Partiyi çıkar' would remove the earlier selected batch, not the Toplam row |
| P-009 | pass | table | menu key / Shift+F10 on the focused row | context menu opens at the row | menu visible=True (handler gets the event; the real key from Windows was not tried) |  | offscreen: event sent by hand |
| P-010 | pass | table | Down from batch 1 | selects batch 2 | current row 1 (batch), selected batch b2 |  |  |
| P-011 | FAIL | table | Home from batch 4 | jumps to the first batch (list habit) | current row 3 (batch), selected batch b4 | F-yukle-03 | Qt's Home/End move across columns; the whole row is one item so nothing visible happens |
| P-012 | FAIL | table | End from batch 1 | jumps to the last batch (list habit) | current row 0 (batch), selected batch b1 | F-yukle-03 |  |
| P-013 | pass | table | Ctrl+Home from the last batch | first batch | current row 0 (batch), selected batch b1 |  |  |
| P-014 | FAIL | table | Ctrl+End from the first batch | last batch (not the Toplam row) | current row 5 (Toplam), selected batch None | F-yukle-02 | the Toplam row is enabled but not selectable: it takes the current index, the selection is cleared and no focus ring is drawn |
| P-015 | FAIL | table | PageDown with 5 batches (one page) | last batch | current row 5 (Toplam), selected batch None | F-yukle-02 |  |
| P-016 | FAIL | table | Down on the last batch | stays on the last batch | current row 5 (Toplam), selected batch None | F-yukle-02 | selection and focus ring vanish; Del, Alt+Up and Alt+Down then do nothing without a word |
| P-017 | pass | table | Del while the Toplam row has the current index | removes nothing, says why, or never gets here | names unchanged=True, toast '4 parti eklendi.' |  | silent no-op |
| P-018 | pass | table | Up from the Toplam row | back on the last batch | current row 4 (batch), selected batch b5 |  |  |
| P-019 | pass | table | PageUp from batch 2 | first batch | current row 0 (batch), selected batch b1 |  |  |
| P-020 | pass | table | Shift+click row 4 (range) | single selection: only row 4 | selected rows [3] |  | batches cannot be removed or moved together (known: inventory Observation 9) |
| P-021 | pass | table | Ctrl+click row 3 | single selection | selected rows [2] |  |  |
| P-022 | pass | table | Ctrl+A | does not select all (single selection) | selected rows 1 |  |  |
| P-023 | pass | table | Tab | focus leaves the table | focus on QToolButton |  |  |
| P-024 | pass | table | Shift+Tab | focus goes back to the command bar | focus on QToolButton |  |  |
| P-025 | pass | table | type a letter (type-ahead) | nothing breaks | selected b2 |  |  |
| P-026 | pass | table | Alt+Up on the first batch | nothing happens, no message needed | order unchanged=True |  |  |
| P-027 | pass | table | Alt+Down on the first batch | first batch moves to place 2, selection follows | order ['ek-1.pdf', 'tarama-2026-11-04-0912.pdf'], selected row 1 |  |  |
| P-028 | pass | table | Alt+Down on the last batch | nothing happens | unchanged=True |  |  |
| P-029 | pass | table | mouse wheel | scrolls only when rows overflow | vscroll max 0 (5 rows fit) |  |  |
| P-030 | pass | table drag | drag batch 1 into the gap before row 4 | batch 1 moves between 3 and 4, one undo step | [1, 2, 0, 3, 4] |  | drop handler called directly (offscreen cannot run an OS drag loop) |
| P-031 | pass | table drag | drop a batch onto the Toplam row | moves to the end or is refused | order changed=True, end=True |  |  |
| P-032 | pass | table drag | drop a batch below the last row (empty area) | moves to the end | end=True |  |  |
| P-033 | pass | table drag | mouse press on the grip and move to row 4 (QTest) | starts a drag (OS loop: not run here) | cursor shape SizeAllCursor |  | offscreen has no drag loop; only the cursor feedback was read |
| P-034 | pass | table | PDF dragged over the table | overlay shows what a drop does | overlay visible=True: '1 parti, <b>Kasım 2026 kapasite raporları</b> işinin sonuna eklenir.' |  |  |
| P-035 | pass | table | drag leaves the table | overlay hides | visible=False |  |  |
| P-036 | pass | window drop | a .txt dragged over | overlay says there is no PDF | Burada PDF yok. Yalnızca PDF dosyaları ve klasörleri eklenir. |  |  |
| P-037 | pass | header | click 'Sayfa' | nothing (no sorting is offered) | sorting=False; order ['tarama-2026-11-04-0912.pdf'] |  |  |
| P-038 | pass | header | drag the edge of 'Sayfa' 60 px left | column narrows, Dosya takes the room | widths [44, 56, 546, 96, 116, 148] -> [44, 56, 602, 40, 116, 148] |  |  |
| P-039 | FAIL | header | drag the edge of a column far to the left | stops at a readable minimum (the title still fits) | Sayfa column 40px; its title needs about 64px; minimumSectionSize 40 | F-yukle-13 | the narrowed width is saved (300 ms later) and comes back at the next start; there is no way to reset the columns |
| P-040 | pass | header | drag a header to another place (movable?) | columns cannot be reordered | sectionsMovable=False |  |  |
| P-041 | pass | header | double click the edge of 'Dosya' | no crash | Dosya width 602 |  |  |
| P-042 | pass | header | grip column resizable? | fixed (it is a handle) | resize mode grip=Interactive |  | grip is interactive: its width can be dragged (header allows it) |
| P-043 | pass | splitter | drag the handle 600 px right | inspector stops at its minimum (156 px), nothing is cut | sizes [1030, 312] -> [1186, 156], inspector min 156 |  |  |
| P-044 | pass | splitter | drag the handle 900 px left (table narrow) | table keeps a usable width (Dosya >= 200 px) | sizes [650, 692], Dosya column 222px |  |  |
| P-045 | pass | inspector | F9 / panel button | inspector hides, table takes the room | inspector visible=False |  |  |
| P-046 | pass | inspector | F9 again | inspector shows again | visible=True |  |  |
| P-047 | pass | command bar 'Dosya ekle…' | double click | one dialog, one add | stub dialog called 2x, batches 2 |  | the dialog is modal: a real second click cannot reach the button while it is open; the stub returns at once, so this only shows the handler runs once per click |
| P-048 | pass | command bar 'Dosya ekle…' | click, then cancel the dialog | nothing changes, no message | batches 2, toast 'cb1.pdf eklendi.' |  |  |
| P-049 | pass | command bar 'Klasör ekle' | click, choose a folder with no PDF | message 'PDF bulunamadı…'  | last message 'PDF bulunamadı. Yalnızca PDF dosyaları ve klasörleri eklenir.' |  |  |
| P-050 | pass | command bar 'Klasör ekle' | click, cancel the dialog | nothing happens | calls 1 |  |  |
| P-051 | pass | command bar 'Yeni iş oluştur' | click with a job open | a new job is made and opened; the old one stays in the list | now job 'Yeni iş A', batches 1 |  |  |
| P-052 | FAIL | command bar 'Partiyi çıkar' | double click | removes one batch | 3 -> 1 batches | F-yukle-14 | selection moves to the next batch after the first click, so the second click removes a batch the user has not looked at |
| P-053 | pass | command bar 'Partiyi aşağı taşı' | double click | moves two places (one per click) | row of the batch 2 |  |  |
| P-054 | pass | command bar Geri al | click after adding a batch | undoes the add | batches 4 -> 3 |  |  |
| P-055 | pass | command bar Yinele | click after Geri al | redoes it | batches 4 |  |  |
| P-056 | pass | keys | Ctrl+Z then Ctrl+Y on Yükle | undo and redo the edit | batches 4 -> 3 -> 4 |  |  |
| P-057 | pass | command bar Kontrol'e geç | click | switch to Kontrol | kontrol |  |  |
| P-058 | pass | command bar Kontrol'e geç | double click | ends on Kontrol | kontrol |  |  |
| P-059 | pass | keys | Ctrl+2 | Kontrol tab | kontrol |  |  |
| P-060 | pass | command bar Gezgin | click (Linux: opens the batches folder) | opens the job's batches folder | ['/tmp/claude-0/p4/yukle/tmpkldrnzss/w51/jobs/98c365158ca6/batches'] |  | on Windows Explorer would highlight the internal copy bN.pdf |
| P-061 | pass | command bar Kontrol'e geç | focus + Space | activates | kontrol |  |  |
| P-062 | FAIL | command bar Kontrol'e geç | focus + Enter | activates | yukle | F-yukle-15 | same cause as F-kontrol-04 |
| P-063 | pass | inspector 'Kontrol'e geç' | focus + Space | activates | kontrol |  |  |
| P-064 | FAIL | inspector 'Kontrol'e geç' | focus + Enter | activates | yukle | F-yukle-15 |  |
| P-065 | pass | inspector 'Kontrol'e geç' | click | activates | kontrol |  |  |
| P-066 | pass | inspector 'Kontrol'e geç' | double click | ends on Kontrol | kontrol |  |  |
| P-067 | pass | inspector 'Rehber'de tarama ayarları' | focus + Space | switches to Rehber | rehber |  |  |
| P-068 | pass | inspector 'Rehber'de tarama ayarları' | click | switches to Rehber (top of the page) | rehber |  | lands at the top of Rehber, not on the scanner-settings section |
| P-069 | pass | inspector '…' | click | menu: Yeniden adlandır, Dosya Gezgini, İşi kapat | ['Yeniden adlandır', "Dosya Gezgini'nde göster", 'İşi kapat'] |  |  |
| P-070 | pass | inspector '…' | focus + Space | menu opens | open=True |  |  |
| P-071 | pass | inspector '…' menu | Esc | closes, focus returns to the button | open=False, focus=QToolButton |  |  |
| P-072 | FAIL | inspector 'İşi kapat' | focus + Enter | closes the job | controller=<evrakci.ui.controller.JobController(0x3b441ab0) at 0x7fd376c50780> | F-yukle-15 |  |
| P-073 | pass | inspector 'İşi kapat' | click | closes the job | controller=None |  |  |
| P-074 | pass | empty page (no jobs at all) | open Yükle in a fresh install | mark, 'Henüz iş yok', two buttons, no search, no list | search visible=False, recent box visible=False, buttons True/True |  |  |
| P-075 | pass | empty page 'Yeni iş oluştur' | click, cancel the file dialog | nothing happens, no message | dialog calls 1, last message '' | F-yukle-16 | Y-01: a cancelled or empty-named dialog is silent; judged OK for a cancel, noted for an empty name |
| P-076 | FAIL | empty page 'Yeni iş oluştur' | choose a file, then confirm the name dialog with only spaces | a message that a name is needed, or the dialog stays open | job created=False, message '' | F-yukle-16 | empty name ends silently (the user picked files and nothing happens) |
| P-077 | pass | empty page 'Yeni iş oluştur' | choose a file, cancel the name dialog | nothing happens | job=False |  |  |
| P-078 | pass | new job dialog | a 300 character name | accepted or limited with a message; the title band stays usable | name length 300; job switch width 364px; window title length 316 |  | no length limit anywhere (see long-content table) |
| P-079 | pass | empty page | start with remembered jobs but no last job | empty page with Son işler | rows 3, more '26 iş daha var; aramak için adını yazın.' |  |  |
| P-080 | pass | empty page | Tab order from 'Yeni iş oluştur' | Dosya ekle, search, 3 job rows, then leaves the page | ['QPushButton:Dosya ekle', '_Search:İş adı ara', '_JobRow:Eski iş 25 uzun ad uzun a', '_JobRow:Eski iş 24 uzun ad uzun a', '_JobRow:Eski iş 23 uzun ad uzun a', 'TitleTabs:Sekmeler', 'JobSwitch:', 'SearchBox:Ara (Ctrl+K)'] |  |  |
| P-081 | pass | job search | Down | focus on the first job row | _JobRow |  |  |
| P-082 | pass | job row | Down | next row (arrow navigation inside the list) | focus on Eski iş 24 uzun ad uzun ad uzun ad  işin |  | rows are buttons: only Tab moves between them |
| P-083 | pass | job row | Up | previous row, or back to the search at the first row | focus on _JobRow |  |  |
| P-084 | pass | job search | Esc with text | clears the text | text '' |  |  |
| P-085 | pass | job search | only spaces | behaves as empty | rows 3, none-label visible=False |  |  |
| P-086 | pass | job search | regex characters '*.[(\' | no error, 'eşleşen iş yok' | '“*.[(\\” ile eşleşen iş yok.' |  |  |
| P-087 | pass | job search | 500 character query | no error, message shown and readable | label 440x38 wraps=True |  | message repeats the whole query in curly quotes: see long-content table |
| P-088 | pass | job search | click 'Aramayı temizle' | clears, list back | text '', rows 3 |  |  |
| P-089 | pass | job search | Enter with one match | opens that job | controller job 'Eski iş 05 uzun ad uzun ad uzun ad uzun ad ' |  |  |
| P-090 | pass | job search | Enter with no match | nothing happens, no message needed (the page already says no match) | job=False |  |  |
| P-091 | pass | job row | click | opens the job | 'Eski iş 25 uzun ad uzun ad uzun ad uzun ad ' |  |  |
| P-092 | FAIL | job row | focus + Enter | opens the job | open=False | F-yukle-15 |  |
| P-093 | pass | job row | focus + Space | opens the job | open=True |  |  |
| P-094 | pass | job row | double click | opens the job once | open=True, tab yukle |  |  |
| P-095 | pass | job row context menu | right click a job | İşi aç, Klasörünü Dosya Gezgini'nde göster | ['İşi aç', "Klasörünü Dosya Gezgini'nde göster"] |  |  |
| P-096 | pass | job row context menu | İşi aç | opens the job | open=True |  |  |
| P-097 | pass | job row context menu | Klasörünü Dosya Gezgini'nde göster | opens the job's folder | ['/tmp/claude-0/p4/yukle/tmpkldrnzss/lr78/jobs/2f7edfcd5bb6'] |  |  |
| P-098 | pass | job row | menu key / Shift+F10 | context menu opens | visible=True |  | event sent by hand |
| P-099 | pass | Ctrl+F on Yükle | show the job list | 'Tüm işler' with up to 8 jobs | title 'Tüm işler', rows 8 |  |  |
| P-100 | pass | Tüm işler | Esc | back to the empty page | title 'Henüz iş yok' |  |  |
| P-101 | pass | Ctrl+F on Yükle with a job open | press | the job list over the open job, search focused | listing=True, focus _Search |  |  |
| P-102 | pass | Tüm işler over an open job | click another job | opens it, list closes | job 'Eski iş 24 uzun ad uzun ad uzun ad ', listing=False |  |  |
| P-103 | FAIL | job row (damaged job.json) | open a job whose file is broken | message that says what to do | last message 'İş açılamadı: İş dosyası okunamadı: 5139260178f9' | F-yukle-20 | message names the failure and the internal id, not the job and not what to do |
| P-104 | pass | F2 | rename to 'Başka ad' | job renamed, title band and window title follow, one undo step | 'Başka ad', window title 'Evrakçı 0.0.2 – Başka ad' |  |  |
| P-105 | pass | Ctrl+Z after rename | undo | name back | Kasım 2026 kapasite raporları |  |  |
| P-106 | pass | F2 | cancel | nothing changes | Kasım 2026 kapasite raporları |  |  |
| P-107 | FAIL | F2 | only spaces, OK | message or dialog stays; at least no change | 'Kasım 2026 kapasite raporları', message '' | F-yukle-16 | silent |
| P-108 | pass | F2 | same name, OK | no undo step added | undo text 'Şablon uygula' |  |  |
| P-109 | pass | F2 | 250 character name | accepted; title band stays usable | job switch 364px, tabs 628px | F-yukle-23 | title band: long name takes the room of the tabs (see long-content table) |
| P-110 | pass | Ctrl+S | save | toast 'İş kaydedildi 14:32. Değişiklikler zaten kendiliğinden…' | toast 'İş kaydedildi 14:50. Değişiklikler zaten kendiliğinden kaydedilir.' |  |  |
| P-111 | pass | Ctrl+W | close job | empty page, job stays in the list | controller=None, list rows 2 |  |  |
| P-112 | pass | recent job row | reopen the job just closed | opens with its batches and selection on the first batch | batches 1, selected b1 |  |  |
| P-113 | pass | Ctrl+W | twice (no job open the second time) | second press does nothing | controller=None |  |  |
| P-114 | FAIL | F2 with no job | press | a message that no job is open (the Yükle inventory says every key that needs a job answers) | action enabled=False, status message '', toast 'İş kaydedildi 14:50. Değişiklikler zaten kendiliğinden kaydedilir.' | F-yukle-36 | the Yükle actions are disabled with no job, so F2, Del, Alt+arrows and Ctrl+Shift+O say nothing; the NO_JOB_TEXT branch in rename_job / show_in_explorer is never reached |
| P-115 | pass | Del with no job | press | nothing happens | no error | F-yukle-36 |  |
| P-116 | pass | Ctrl+2 with no job | press | goes to Kontrol (placeholder with text) | kontrol |  |  |
| P-117 | pass | reading | start a 3 file read | progress card, Okunuyor rows, cancel button visible, Kontrol'e geç disabled | progress visible=True, cancel visible=True, go enabled=False, bar go enabled=False |  |  |
| P-118 | pass | reading | Esc | does not cancel (documented) | task running=True |  | Esc does nothing during a read; Ctrl+. or the İptal et button cancel; the progress card does not name Ctrl+. |
| P-119 | FAIL | Ctrl+O during a read | choose a file in the dialog | file is queued with a message | dialog calls 1, queued 0, message '' | F-yukle-17 | known ledger B-001: add_batches returns silently while a task runs |
| P-120 | pass | Ctrl+N during a read | press | message 'Okuma sürüyor; bitince yeni iş oluşturun.' | dialog calls 0, message 'Okuma sürüyor; bitince yeni iş oluşturun.' |  | with a job open Ctrl+N opens the file dialog even while reading (choose_new_job refuses only when busy: it does refuse) |
| P-121 | pass | drop during a read | drop a PDF | queued, message 'sıraya alındı' | queued 1, message '1 dosya sıraya alındı; okuma bitince eklenir.' |  |  |
| P-122 | pass | drop during a read | the same PDF again | not queued twice | queued 1 |  |  |
| P-123 | pass | reading | Del on the first batch while reading | batch removed, read continues | batches 1 -> 0, task=True |  | edits are allowed while reading (documented) |
| P-124 | pass | reading | Ctrl+Z during a read | undoes the delete, read continues, nothing is lost | task=True, batches 1 |  |  |
| P-125 | pass | reading | F2 rename while reading | allowed | Okurken ad |  |  |
| P-126 | pass | reading | switch to Kontrol during the read | allowed; the read continues | task=True, tab kontrol |  |  |
| P-127 | pass | reading | Ctrl+W during a read | refused with a message | controller kept=True, message 'Dışa aktarma ya da okuma sürüyor; bitince başka bir iş açın.' | F-yukle-35 |  |
| P-128 | pass | reading | resize the window to 1000x600 during a read | layout adapts, progress card visible | progress 668x92 visible=True |  |  |
| P-129 | pass | reading | open another job while reading | refused with 'Bir iş sürüyor; bitince açın.' | same job True | F-yukle-35 |  |
| P-130 | pass | reading | Ctrl+. | title 'İptal ediliyor…' | title 'İptal ediliyor…' |  |  |
| P-131 | pass | reading | Ctrl+. twice | second press harmless | task=True |  |  |
| P-132 | pass | reading | close the window, answer No | window stays, read continues | close ignored=True, task=True |  |  |
| P-133 | pass | reading | close the window, answer Yes | read stops, window closes when it has stopped, message 'Durduruluyor…' | message 'Durduruluyor… Pencere iş durunca kapanır.', close ignored for now=True |  |  |
| P-134 | pass | reading | after cancel | toast 'İptal edildi; hiçbir şey değişmedi.', queued files reported with 'Yine de ekle' | last message 'Sıradaki 1 dosya eklenmedi; önceki okuma iptal edildi.', task=None |  |  |
| P-135 | FAIL | failed read | one good and one broken file in one add | good file is kept or the user is told that nothing was added | batches 1 (before 1), info bar True | F-yukle-19 | the good file is discarded with the bad one |
| P-136 | pass | info bar | click 'Dosya ekle…' | file dialog opens | calls 1 |  |  |
| P-137 | pass | info bar | after a successful add | bar is gone | bar visible=False |  |  |
| P-138 | pass | info bar | close with the X | bar disappears | visible=False |  |  |
| P-139 | FAIL | add | add the same file twice (two separate adds) | a warning or a skip; at least not silent | batches 2 -> 4, last message 'iyi.pdf eklendi.' | F-yukle-18 | no duplicate warning (documented O-7); two copies of the same scan double the pages in Kontrol and the export |
| P-140 | pass | add | a path that does not exist | 'Okunamadı' bar with a way forward | bar text 'Dosya bulunamadı: yok.pdf. Dosyayı kontrol edip yeniden ekleyin.' |  |  |
| P-141 | pass | window drop | drop 2 PDFs while on Şablonlar | jumps to Yükle, adds 2 batches in the given order | tab yukle, batches 1 -> 3, last two ['dr1.pdf', 'dr2.pdf'] |  |  |
| P-142 | pass | window drop | drop a folder with b-10, b-2, alt/c and a .txt | 3 PDFs in natural order, .txt skipped | ['c.pdf', 'b-2.pdf', 'b-10.pdf'] |  | natural order: alt/c.pdf sorts before b-* (path sort) |
| P-143 | pass | window drop | drop a .txt only | message 'PDF bulunamadı…', nothing added | message 'PDF bulunamadı. Yalnızca PDF dosyaları ve klasörleri eklenir.', batches 0 added |  |  |
| P-144 | pass | window drop | drop plain text (no URLs) | ignored | handled=False |  |  |
| P-145 | pass | window drop | drop a web link ending in .pdf | ignored or a clear message | batches added 0, message 'PDF bulunamadı. Yalnızca PDF dosyaları ve klasörleri eklenir.' |  | a non-file URL is dropped silently (find_pdfs gets an empty list -> 'PDF bulunamadı') |
| P-146 | pass | window drop | drop 2 PDFs with no job open | creates a job named after the first file | job 'dr1', batches 2 |  |  |
| P-147 | FAIL | window | resize to 1024x600 at text 100 % | no clipping, nothing unreachable | minimumSize 1024x600, actual 1024x600, clipping lines 1: ["yukle-1024x600-100 BatchTable hücre (0, 2) kısaltılmış: 'tarama-2026-11-04-0912.pdf' (207>"] | F-yukle-04 | sizes below 1366x768 are outside the supported range in PRODUCT.md; listed for information |
| P-148 | FAIL | window | resize to 1024x600 at text 150 % | no clipping, nothing unreachable | minimumSize 1024x600, actual 1024x600, clipping lines 2: ["yukle-1024x600-150 BatchTable hücre (0, 2) kısaltılmış: 'tarama-2026-11-04-0912.pdf' (317>", 'yukle-1024x600-150 QLabel#- kısaltılmış: "PDF\'leri pencerenin herhangi bir yerine bırakın '] | F-yukle-04 | sizes below 1366x768 are outside the supported range in PRODUCT.md; listed for information |
| P-149 | pass | window | resize to 800x600 at text 100 % | no clipping, nothing unreachable | minimumSize 1024x600, actual 1024x600, clipping lines 1: ["yukle-800x600-100 BatchTable hücre (0, 2) kısaltılmış: 'tarama-2026-11-04-0912.pdf' (207>1"] |  | the window refuses to go below 1024x600 (minimumSize), so this is the 1024x600 case |
| P-150 | pass | window | resize to 800x600 at text 150 % | no clipping, nothing unreachable | minimumSize 1024x600, actual 1024x600, clipping lines 2: ["yukle-800x600-150 BatchTable hücre (0, 2) kısaltılmış: 'tarama-2026-11-04-0912.pdf' (317>2", 'yukle-800x600-150 QLabel#- kısaltılmış: "PDF\'leri pencerenin herhangi bir yerine bırakın y'] |  | the window refuses to go below 1024x600 (minimumSize), so this is the 1024x600 case |
| P-151 | pass | window | maximize | layout follows | 800x800 |  |  |

## Not exercised

- A real mouse drag of a batch row or of PDFs from Explorer (no OS drag loop offscreen); the drop handlers and the overlay were driven directly (P-030 to P-036, P-141 to P-146).
- Taskbar progress, flash and the Explorer highlight (Windows only).
- Real file and folder dialogs, and the focus that returns after them (only the stubbed calls and the menu case P-071).
- Reading a very large folder (5000 PDFs) and a password-protected PDF (the error text for it was read from code, not run).
- Dragging a batch with the keyboard-only user's alternative (Alt+Up / Alt+Down) over 120 rows: covered by P-026 to P-028 on 5 rows only.
