# Şablonlar audit: click paths

Phase 4, Görev A, screen Şablonlar. Every click, double click, right click, drag, wheel and key on the elements of `sablonlar-inventory.md` that could be driven, plus the common mistakes (double click on a button, a drag to the wrong place, cancel in the middle, close or resize during a task) and the damaged-file, long-content and off-sheet cases. Driven with QTest on the synthetic demo job (`tools/screenshots.py:build`) and on the long-content jobs, window 1366x768, text 100 %, light theme (the zoom and canvas rows also at 25 and 400 %), offscreen. The file and name dialogs (`QInputDialog.exec`) are replaced by stubs that record the call and return a scripted answer; OCR is a fake engine (`FakeEngine`: fixed text and confidence, as in `tests/ui/test_sablon_window.py`). Scripts (session scratchpad, not committed): `p_canvas.py`, `p_model.py`, `p_misc.py`, `p_nav.py`, `p_off.py`, `p_trig.py`, plus the small probes `t1`..`t12`; raw tables: `/tmp/claude-0/p4/sablonlar/paths/*.tsv`.

Result: **149 paths tried, 124 pass, 24 fail, 1 not decidable**. The 24 failures are 13 distinct findings (06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 19); rows with a finding id and result "pass" are findings found by looking at what the passing path did (the Note column says what). Keywalk (Tab walk, `keywalk.py --tab sablonlar`) passes in 24 of 24 combinations (3 themes x 1366x768 and 1920x1080 x text 100, 115, 130, 150): no trap, nothing unnamed, work area reached. The B-047 pattern (QAction.triggered into a method with a default parameter) was searched for and not found: last row.

Rules of the table: "Expected" is what the product documents (PRODUCT.md, the research inventory, the tooltip or accessible name of the element) or, where nothing is documented, "records behaviour" in the Note column. "Actual" is the measured value from the run. Pass means actual matches expected. Offscreen limits: the OS drag loop does not run (drags are sent as press, move and release events to the viewport, and `move_variable_to` / `move_section_to` stand in for the tree's `dropEvent`); the Menu key and Shift+F10 open nothing offscreen, so the context-menu event was sent by hand (P-130: what Windows sends was not checked); menu popups and native dialogs cannot be grabbed; the system motion setting was varied only through `motion.set_reduced_motion_override`. A double click on a button is two clicks with no pause (what Windows delivers to a push button).

Already in the ledger and seen again: B-016 (box off the sheet through the inspector: P-070, P-071), B-017 (damaged template files: P-096), B-019 and B-029 are not touched by these paths. Dead helpers from O-16 were not reached by any path (as expected).

Coverage by group: canvas drawing, selecting, moving, resizing and nudging by mouse and keyboard (page, 36 rows), zoom and pan (17), undo and redo of every edit type (15: add variable, Zorunlu, rename, file-name pattern, box page, X field, duplicate, delete box, delete variable, reorder variable and section; each checked for undo, redo and the file on disk), name and pattern rules (11), dialogs (7), keys (15), buttons including double clicks (6), lists, menus and pickers (15), the try-all run with template change, resize, tab switch and window close (5), save failure (3), damaged files (5) and boxes off the sheet (6).

| ID | Element | Path (action) | Expected | Actual | Result | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-001 | drag with Kutu çiz on | draw (100,100)-(150,120) mm | a variant box about 100,100,150,120 | (100.06, 100.06, 149.93, 120.13) | pass |  | undo text: Kutu ekle |
| P-002 | undo of draw | Ctrl+Z after draw | box removed | [(20, 30, 90, 42)] | pass |  |  |
| P-003 | redo of draw | Ctrl+Y | box back | 2 | pass |  |  |
| P-004 | drag < 2 mm with Kutu çiz on | drag 1 mm | refused with a word or ignored | boxes=1 message='' | pass | F-sablonlar-34 | silent drop; passes (nothing added); the silence is the finding |
| P-005 | draw box wholly beside the sheet | drag from 5 mm outside the right edge | no box | 1 | pass | F-sablonlar-34 | passes (no box); silent |
| P-006 | draw box crossing the right edge | drag from 10 mm inside to 15 mm outside | cut to the sheet | (200.11, 49.88, 210.19, 59.91) | pass |  |  |
| P-007 | right-button drag with Kutu çiz on | drag | no box (menu only) | 1 | pass |  |  |
| P-008 | double click on sheet with Kutu çiz on | double click | nothing added | 1 | pass |  |  |
| P-009 | Enter while drawing | B then Enter | 40x10 box placed | (129.93, 165.0, 169.93, 175.0) | pass |  |  |
| P-010 | Esc while drawing | Esc | drawing off | False | pass |  |  |
| P-011 | Kutu çiz with no variable chosen | B | a message says choose a variable | Çizmeden önce soldan bir değişken seçin. | pass |  |  |
| P-012 | drag with no variable chosen | drag | message, no box | 'Önce soldan bir değişken seçin.' | pass |  |  |
| P-013 | move by drag | drag body +30,+40 mm | box moved by 30,40 | (49.8, 70.14, 119.8, 82.14) | pass |  | undo: Kutuyu taşı |
| P-014 | undo of two separate drags | drag, drag, Ctrl+Z once | only the second drag undone | after one undo box=(20, 30, 90, 42) first-drag=(49.8, 70.14, 119.8, 82.14) orig=(20, 30, 90, 42) | FAIL | F-sablonlar-09 | the merge key is the same for every move of this box; two drags are one undo step |
| P-015 | undo of move | Ctrl+Z | back to original | (20, 30, 90, 42) | pass |  |  |
| P-016 | drag a box far past the sheet corner | drag +500,-500 mm | kept on the sheet | (140.19, 0.0, 210.19, 12.0) | pass |  |  |
| P-017 | resize handle tl | drag corner by -5,-5 mm | (15, 25, 90, 42) | (14.83, 24.83, 90.0, 42.0) | pass |  | undo: Kutuyu yeniden boyutlandır |
| P-018 | resize handle tr | drag corner by 5,-5 mm | (20, 25, 95, 42) | (20.0, 24.83, 94.87, 42.0) | pass |  | undo: Kutuyu yeniden boyutlandır |
| P-019 | resize handle bl | drag corner by -5,5 mm | (15, 30, 90, 47) | (14.83, 30.0, 90.0, 47.17) | pass |  | undo: Kutuyu yeniden boyutlandır |
| P-020 | resize handle br | drag corner by 5,5 mm | (20, 30, 95, 47) | (20.0, 30.0, 94.87, 47.17) | pass |  | undo: Kutuyu yeniden boyutlandır |
| P-021 | resize a box through its opposite corner | drag br corner to above-left | kept >= 2 mm | (0.0, 8.07, 2.0, 10.07) | pass |  |  |
| P-022 | Right x4 | 4 presses | +1.0 mm, one undo step | (21.0, 30.0, 91.0, 42.0) steps +0 | FAIL | F-sablonlar-09 | the nudges merged into the earlier move step (steps +0) |
| P-023 | Shift+Down | 1 press | +1 mm | (21.0, 31.0, 91.0, 43.0) | pass |  |  |
| P-024 | Ctrl+Right | 1 press | width +0.25 | (21.0, 31.0, 91.25, 43.0) | pass |  | undo text: Kutuyu yeniden boyutlandır |
| P-025 | Ctrl+Left held (400 presses) | shrink | stops at 2 mm | (21.0, 31.0, 23.0, 43.0) | pass |  |  |
| P-026 | Ctrl+Up at min | no change, no sound or message | silent | True | pass |  | at a limit nothing says so |
| P-027 | undo of nudge+resize steps | undo until before nudging | original box | (20, 30, 90, 42) | pass |  | steps undone: 1 |
| P-028 | Shift+Left x100 at the left edge | slam into edge | x0 stays 0 | (0.0, 30.0, 70.0, 42.0) | pass |  |  |
| P-029 | canvas | Down with no box chosen | page scrolls | 50 -> 78 | pass |  | nothing to scroll when the sheet is fitted |
| P-030 | zoom 25 | slider | canvas zoom equals | 25 | pass |  |  |
| P-031 | move by drag at 25 % | drag 2 mm | moves by about 2 mm | (2.12, 32.12, 72.12, 44.12) | pass |  | px per mm 0.94 |
| P-032 | draw at 25 % | drag 10x6 mm | box ~10x6 | (99.48, 99.48, 110.07, 105.83) | pass |  | px per mm 0.94 |
| P-033 | zoom 400 | slider | canvas zoom equals | 400 | pass |  |  |
| P-034 | move by drag at 400 % | drag 2 mm | moves by about 2 mm | (22.05, 31.98, 92.05, 43.98) | pass |  | px per mm 15.12 |
| P-035 | draw at 400 % | drag 10x6 mm | box ~10x6 | (100.01, 100.01, 110.0, 106.03) | pass |  | px per mm 15.12 |
| P-036 | handle hit area on a 2 mm box at 25 % | hover the box centre | no corner handle under the centre (body drag moves) | handle_at(centre)=0; box is 1.9 px wide | FAIL | F-sablonlar-16 | handle hit 8 px, box 2 mm at 25 % is ~2 px |
| P-037 | Ctrl+wheel | wheel up | 100+10 | 110 | pass |  |  |
| P-038 | Ctrl+wheel | down x60 | floor 25 | 25 | pass |  |  |
| P-039 | Ctrl+wheel | up x80 | ceiling 400 | 400 | pass |  |  |
| P-040 | Ctrl+0 | press | fit | 87 vs fit 87 | pass |  |  |
| P-041 | Ctrl++ then Ctrl+- twice | Ctrl+Plus, Ctrl+Minus x2 | net -10 from fit | 77 | pass |  |  |
| P-042 | wheel | wheel down | page scrolls | -7->77 | pass |  |  |
| P-043 | Shift+wheel | Shift+wheel | scrolls sideways | 0->0 | pass |  |  |
| P-044 | window | resize with a chosen zoom | zoom stays | 150->150 | pass |  |  |
| P-045 | window | resize while fitted | zoom follows | 87 | pass |  |  |
| P-046 | page | middle-button drag | pans | 344->444 | pass |  |  |
| P-047 | canvas | Esc with a box chosen | box cleared | None | pass |  |  |
| P-048 | Değişken ekle | Ctrl+Shift+N, name Yeni_Alan | undo restores, redo repeats, disk follows | steps 1 text='Değişken ekle' undo=True redo=True disk_after_undo=True | pass |  |  |
| P-049 | Değişken ekle | dialog answer empty / cancelled | nothing, no message | '' | pass |  | O-17: silent |
| P-050 | Değişken ekle | blank name (spaces) | nothing, silent | True | pass | O-17 | silent: no message |
| P-051 | Değişken ekle | name: braces | refused with a Turkish reason, or accepted when valid | added=0 msg='Değişken adında { veya } olamaz: {x}' | pass | F-sablonlar-25 | accepted |
| P-052 | Değişken ekle | name: duplicate | refused with a Turkish reason, or accepted when valid | added=0 msg='Bu adla bir değişken zaten var: Sicil_No' | pass |  |  |
| P-053 | Değişken ekle | name: zero-width char | refused with a Turkish reason, or accepted when valid | added=0 msg="Değişken adında görünmeyen veya özel karakter var: 'a\\u200bb'" | pass |  |  |
| P-054 | Değişken ekle | name: 400 chars | refused with a Turkish reason, or accepted when valid | added=1 msg='' | pass |  |  |
| P-055 | Değişken ekle | name: case differs | refused with a Turkish reason, or accepted when valid | added=1 msg='' | pass |  |  |
| P-056 | Değişken ekle | name: NUL | refused with a Turkish reason, or accepted when valid | added=0 msg="Değişken adında görünmeyen veya özel karakter var: 'a\\x00b'" | pass |  |  |
| P-057 | Zorunlu | click checkbox | undo restores, redo repeats, disk follows | steps 1 text='Zorunlu' undo=True redo=True disk_after_undo=True | pass |  |  |
| P-058 | Ad (inspector) | rename to Sicil_Yeni | undo restores, redo repeats, disk follows | steps 1 text='Değişken adı' undo=True redo=True disk_after_undo=True | pass |  |  |
| P-059 | Ad (inspector) | rename updates the file-name pattern | pattern follows | {Sicil_Yeni}_{Firma_Adi} | pass |  |  |
| P-060 | Ad (inspector) | rename to an existing name | refused with a reason, old name back in field | msg='' field='Firma_Adi' | FAIL | F-sablonlar-19 | the clash message does appear when the variable is chosen (checked separately: "Bu adla bir değişken zaten var: Firma_Adi"); after an undo nothing is chosen and the typed name is dropped silently |
| P-061 | Dosya adı | set pattern | undo restores, redo repeats, disk follows | steps 1 text='Dosya adı' undo=True redo=True disk_after_undo=True | pass |  |  |
| P-062 | Dosya adı | unknown variable {Yok} | message at the field, text kept | err='Kalıpta bilinmeyen değişken: Yok' visible=True text='{Yok}' | pass | F-sablonlar-33 | message is the core's |
| P-063 | Dosya adı | unmatched brace | reason | Dosya adı kalıbında eşleşmeyen süslü parantez: {Sicil_No | pass |  |  |
| P-064 | Dosya adı | 2000 characters | accepted or limited with a message | err='' saved_len=2000 | pass |  | core allows (120 chars cut at export) |
| P-065 | Kutunun sayfası | spin to 2 | undo restores, redo repeats, disk follows | steps 1 text='Kutunun sayfası' undo=True redo=True disk_after_undo=True | pass |  |  |
| P-066 | Kutunun sayfası | box moves to page 2 | canvas shows page 2, box visible | page_number=2 boxes on canvas=1 | pass |  |  |
| P-067 | Kutunun sayfası | a page the example does not have (9 of 3) | a message or refusal | page_number=2 items=0 message='' note='' list='Değişken 1: Sicil_No, 1 kutu' | FAIL | F-sablonlar-12 | box vanishes from the canvas; only the read note says 'sayfa yok' after a read |
| P-068 | Kutunun sayfası | 'son' | last page shown | page_number=3 | pass |  |  |
| P-069 | Kutunun sayfası | select all, type 0, Enter (was 2) | 1 (documented in the research file: 0 gives 1) | 2 | FAIL | F-sablonlar-13 | Qt keeps the last valid value when the typed text is Intermediate |
| P-070 | Kutu X / genişlik (inspector) | width = sheet width then X = width-5 (B-016) | box kept on the sheet | (205.19, 30.0, 415.38, 42.0) | FAIL | F-sablonlar-10 | box ends 415.4 mm, sheet 210.2; B-016 |
| P-071 | box off the sheet | is the box visible / reachable on the canvas | visible, or clamped | rect right edge 3271px vs sheet 1655px; scene rect 1675 | FAIL | F-sablonlar-10 | scene is larger than the sheet by the margin only; B-016 |
| P-072 | box off the sheet | status/list/inspector show it? | inspector X=205.19 W=210.19; list row still there | True | pass |  | the number shows 205+210; reader clips it (S-22) |
| P-073 | Kutu geometri (4 fields) | X field edit | undo restores, redo repeats, disk follows | steps 0 text='Kutuyu taşı' undo=False redo=True disk_after_undo=False | FAIL | F-sablonlar-09 | undo goes back past the typed value |
| P-074 | Kutu genişliği | type 0 | clamped to 2 | 2.0 | pass |  |  |
| P-075 | Kutu genişliği | type letters | not accepted | '2,0' | pass |  |  |
| P-076 | Kutu genişliği | type 1e3 | not accepted or clamped | 210.19 | pass |  | valid float syntax; range clamps |
| P-077 | Kutu genişliği | type 12,5 | 12.5 | 12.5 | pass |  |  |
| P-078 | Kutu genişliği | type 12.5 (dot) | 12.5 or refused | 12.5 | pass |  |  |
| P-079 | Kutuyu çoğalt | Ctrl+D | undo restores, redo repeats, disk follows | steps 1 text='Kutuyu çoğalt' undo=True redo=True disk_after_undo=True | pass |  |  |
| P-080 | Kutuyu sil | Del on a section | undo restores, redo repeats, disk follows | steps 1 text='Kutuyu sil' undo=True redo=True disk_after_undo=True | pass |  |  |
| P-081 | Değişkeni sil | Del on a variable | undo restores, redo repeats, disk follows | steps 1 text='Değişkeni sil' undo=True redo=True disk_after_undo=True | pass |  |  |
| P-082 | Sırayı değiştir (variable) | Alt+Down | undo restores, redo repeats, disk follows | steps 1 text='Sırayı değiştir' undo=True redo=True disk_after_undo=True | pass |  |  |
| P-083 | Sırayı değiştir (section) | Alt+Up on Bölüm 2 | undo restores, redo repeats, disk follows | steps 1 text='Sırayı değiştir' undo=True redo=True disk_after_undo=True | pass |  |  |
| P-084 | Ctrl+Z in the Ad field | undo with the name field focused | undoes the last template edit or the field's text | Kutuyu çoğalt | pass |  | app-level undo acts on the template stack even while typing: field text is not what is undone; re-run with a real key press (`QTest.keyClick` Ctrl+Z on the field): the field's own text is undone and the template stack s… |
| P-085 | template list | switch template then Ctrl+Z | history is cleared (O-18) | canUndo=False | pass | O-18 | known O-18 |
| P-086 | Şablonu kaydet / autosave | disk write fails | clear message with next step, status bar, toast | message="Şablon kaydedilemedi. Diskte yer olduğundan emin olup Şablonu kaydet'e basın." status='Şablon kaydedilemedi' dirty=True | pass |  |  |
| P-087 | Şablonu kaydet | press while disk still failing | error again, no 'kaydedildi' toast | message="Şablon kaydedilemedi. Diskte yer olduğundan emin olup Şablonu kaydet'e basın." | pass |  |  |
| P-088 | Şablonu kaydet | press after the disk is back | message cleared, saved | message='' dirty=False err='' | pass |  |  |
| P-089 | Şablon ekle (+) | name: normal | a template is made or a reason is given | rows 2->3 current='Yeni Ş' | pass |  |  |
| P-090 | Şablon ekle (+) | name: 3000 chars | a template is made or a reason is given | rows 3->4 current='xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' | pass | F-sablonlar-25 | accepted |
| P-091 | Şablon ekle (+) | name: NUL char | a template is made or a reason is given | rows 4->5 current='a\x00b' | pass | F-sablonlar-25 | accepted |
| P-092 | Şablon ekle (+) | name: blank | a template is made or a reason is given | rows 5->5 current='a\x00b' | pass |  |  |
| P-093 | Şablon ekle (+) | name: braces | a template is made or a reason is given | rows 5->6 current='{x}' | pass | F-sablonlar-25 | accepted |
| P-094 | Şablon ekle (+) | name: path chars | a template is made or a reason is given | rows 6->7 current='../../etc' | pass | F-sablonlar-25 | accepted |
| P-095 | Şablon ekle (+) | same name twice | second gets (2) | Yeni Ş (2) | pass |  |  |
| P-096 | tab entry / F5 | 6 damaged template files in the folder (bad JSON, bad bytes, wrong shape, future version, empty, 100000 brackets) | a message names them | rows 2->2, message='', new visible labels=[], 0.03s | FAIL | F-sablonlar-07 | B-017 |
| P-097 | tab entry / F5 | no crash, list still usable | pass | EXC=[] | pass |  |  |
| P-098 | template row | click a template whose file was damaged after the list was drawn | a message, the open template stays | EXC=['TemplateError: Şablon dosyası okunamadı: 09c153807a (Expecting property name enclosed in double quotes: line 1 column 3 (char 2)) @ store.py:59'] message='' open=Kapasite Raporu | FAIL | F-sablonlar-08 | open_template calls store.load without a guard (sablon.py:open_template) |
| P-099 | template row | click a template whose file was deleted (another PC, command line) | a message | EXC=["KeyError: '09c153807a' @ store.py:95"] message='' | FAIL | F-sablonlar-08 | KeyError from load |
| P-100 | autosave | the open template's file was damaged by another program, then the user edits | (informational) the app's copy overwrites the file | '{\n "format": "evrakc' | pass |  | last writer wins; no check of the file's change time |
| P-101 | B | press with focus on the canvas | Kutu çiz on | True | pass |  |  |
| P-102 | B | press again | off | False | pass |  |  |
| P-103 | G | press | Izgaraya oturt on | True | pass |  |  |
| P-104 | Ctrl+D | press with a box chosen | one more box | 2 | pass |  |  |
| P-105 | Del | press with a box chosen | one less | 1 | pass |  |  |
| P-106 | F9 | press | inspector hidden | False | pass |  |  |
| P-107 | B / Del inside the Ad field | typing | no command fires | drawing=False boxes=1 field='Sicil_Nob' | pass |  |  |
| P-108 | B / G in the pattern field | typing | text typed, no command | text='{Sicil_No}_{Firma_Adi}bg' snap=False | pass |  |  |
| P-109 | Del in the template list | press | nothing | 1 | pass |  |  |
| P-110 | Del in the variable list | variable with 3 boxes | asks or is clearly undoable (toast Geri al) | variables 2->1 | pass | O-03 | toast with Geri al for 10 s: O-03 |
| P-111 | Alt+Up | press on the 2nd variable | moves up | ['Firma_Adi', 'Sicil_No'] | pass |  |  |
| P-112 | Ctrl+F | press | focus in the variable list | focus on VariableTree | pass |  |  |
| P-113 | Ctrl+T then Esc | start try-all, stop with Esc | stopped | busy_at_start=True after=True status='0 okuma kontrol bekliyor' | pass |  |  |
| P-114 | Kutu çiz | double click | toggles twice (off) -- common mistake: ends on/off? | drawing=False | pass |  | two toggles, state unchanged |
| P-115 | Değişken ekle (command bar) | double click | one dialog, one variable (modal dialog swallows the second click) | dialogs=2 vars=['Sicil_No', 'Firma_Adi', 'DC1'] | n/a |  | the stub returns at once, so a real dialog would block the 2nd click: not decidable offscreen; double click with a stubbed (non-modal) dialog: not decidable offscreen; a real QInputDialog is modal and swallows the secon… |
| P-116 | Kutuyu sil | double click | one box deleted (second click on the next chosen box deletes another) | boxes 5->3, undo steps 9 | FAIL | F-sablonlar-14 |  |
| P-117 | Kutuyu çoğalt | double click | one copy (a variant) or two | boxes 3->5 | FAIL | F-sablonlar-14 | second click copies the copy: two stacked variants; two stacked copies |
| P-118 | Bütün örneklerde dene | double click | one run | EXC=[] | pass |  |  |
| P-119 | Ayrıntı panelini gizle | double click | back where it was | True | pass |  |  |
| P-120 | variable list | choose a variable far down (keyboard Alt/canvas/menu) with the column scrolled to the top | the chosen row scrolls into view | row y=2399 of viewport 648; scroll value 0 | FAIL | F-sablonlar-06 | selection from the canvas or by select_variable never scrolls the column; only a click or arrow keys in the list do |
| P-121 | page box click | click a box on the page | its row in the left column is visible | chosen Alan_12, row y=1319 of 648 | FAIL | F-sablonlar-06 |  |
| P-122 | template list + variable list | 10+3 templates, 40 variables | list stays within the column (scrolls inside), both cards reachable | templates card 520 px, variable list 2320 px, column 648 px; the Değişkenler card starts at y=639 | pass | F-sablonlar-06 | the whole template list is laid out at full height so variables begin below the fold; passes with 3 templates; with 30 the variable card starts 1,239 px down |
| P-123 | Down x8 held | arrow through 8 templates | each arrow opens a template (no 'open' step), saved edits safe | 8 loads in 0.06s, reads pending=False | pass |  | opening happens on current-item change: arrows read every template on the way, running OCR for each |
| P-124 | row | double click | opens the template (same as click), no rename editor | editing=False current=Faaliyet Belgesi | pass |  |  |
| P-125 | row | right click | no menu (documented: the template list has none) | menu requests=0 | pass | O-01 | no rename / delete / duplicate here: O-01 |
| P-126 | row | drag a row to another place | nothing moves (sorted by name) | True | pass |  |  |
| P-127 | row | double click on a variable | no editor, no action (rename is in the inspector) | state=State.NoState | pass |  |  |
| P-128 | row | right click | menu: Kutuyu çoğalt, Kutuyu sil, taşı, Değişken ekle | requests=[None] items=['Kutuyu çoğa&lt', 'Değişkeni &sil', 'Değişkeni yuka&rı taşı', 'Değişkeni &aşağı taşı', 'Değişken &ekle'] | pass |  |  |
| P-129 | bare sheet | right click | menu: Kutu çiz, Izgaraya oturt, Okumaları sayfada göster | requests=[('sablonlar.kutu_ciz', 'sablonlar.izgara', 'sablonlar.okumalari_goster')] items=['Kutu çi&z', 'Izgaraya &oturt', '&Okumaları sayfada göster'] | pass |  |  |
| P-130 | canvas with a box chosen | context-menu key (Menu / Shift+F10) event at the viewport centre | menu of the chosen box | requests=[('sablonlar.kutu_ciz', 'sablonlar.izgara', 'sablonlar.okumalari_goster')] | FAIL | F-sablonlar-17 | the page menu is chosen by what lies under the position; a keyboard event has no pointer, the box menu opens only if the box happens to lie under the centre of the view (unverified: Windows sends the focus rectangle's p… |
| P-131 | row | drag variable 1 below variable 3 (move_variable_to) | order changes, undoable | ['Alan_2', 'Alan_3', 'Değişken 1 çok uzun ad boşluklu xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'] | pass |  |  |
| P-132 | section row | move first section last | try order changes, undoable | ['İş · Belge 1 · s.1', 'İş · Belge 1 · s.2', 'İş · Belge 1 · s.0'] | pass |  |  |
| P-133 | Alt+Down on the last variable | press | nothing, silently (command is disabled) |  | pass |  |  |
| P-134 | Sayfa picker | scroll the wheel over it (a mistake while scrolling the page) | page does not change by accident | 0->1 page_number=2 | FAIL | F-sablonlar-15 | QComboBox takes the wheel without focus |
| P-135 | Örnek picker | scroll the wheel over it | example does not change by accident | 0->1 example=2 | FAIL | F-sablonlar-15 |  |
| P-136 | Örnek picker | choose Örnek 2 | page 1 of that document, boxes shown, read re-runs | example=2 page=1 boxes=46 | pass |  |  |
| P-137 | template list | open another template while try-all runs | results discarded, no stale marks on the new template | running=True, marks=['Örnek 1, sayfa 1', 'Örnek 2, sayfa 5', 'Örnek 3, sayfa 13'] | pass |  |  |
| P-138 | examples picker | finish of a run started on another template | no stale marks | ['Örnek 1, sayfa 1', 'Örnek 2, sayfa 5', 'Örnek 3, sayfa 13'] | pass |  |  |
| P-139 | window | resize during try-all | no error | EXC=[] | pass |  |  |
| P-140 | tab | switch to Değerler and back during try-all | keeps running or stops cleanly | EXC=[] task=None | pass |  |  |
| P-141 | window | close during try-all | closes without error | EXC=[] | pass |  |  |
| P-142 | file loaded with boxes beyond the sheet | open the template | boxes shown clipped or flagged | canvas items=4 variable rows=5 | pass |  | model accepts any position; no message about boxes outside the sheet |
| P-143 | far-outside box chosen in the list | reveal | scrolls to it / says it is off the sheet | selected=('Sicil_No', 1) scene rect right=1675 px; box rect right=3622 | FAIL | F-sablonlar-10 | the box is outside the scene: nothing to see, nothing says so (the only hint is the reader's note 'kutu sayfa dışında' after a read); box outside the scene: nothing shows it |
| P-144 | far-outside box, Left arrow | 0.25 mm nudge | moves 0.25 mm | (400.0, 500.0, 460.0, 520.0) -> (150.19, 276.93, 210.19, 296.93) | FAIL | F-sablonlar-11 | _moved clamps to the sheet: the box jumps to the sheet edge |
| P-145 | far-outside box, Right/Down | nudge | moves 0.25 mm or stays | (400.0, 500.0, 460.0, 520.0) -> (150.19, 276.93, 210.19, 296.93) | FAIL | F-sablonlar-11 | (after the jump the box is on the sheet edge, so Right/Down change nothing) |
| P-146 | half-outside box, Up arrow | nudge | moves 0.25 mm up | (200.0, 290.0, 260.0, 330.0) -> (150.19, 256.93, 210.19, 296.93) | FAIL | F-sablonlar-11 | x is also clamped: the box slid left onto the sheet |
| P-147 | half-outside box, Ctrl+Right | resize | grows 0.25 mm | (150.19, 256.93, 210.19, 296.93) -> (150.19, 256.93, 210.19, 296.93) | FAIL | F-sablonlar-11 | _clamp pulls the edge back onto the sheet: the box shrinks by about 50 mm |
| P-148 | Tab order (keywalk.py --tab sablonlar) | Tab walk in 3 themes x 2 sizes x 4 text sizes | no trap, nothing unnamed, work area reached | 24 of 24 combinations OK (29 stops at 150 %: title tabs, job switch, search, menu, command bar, + buttons, template list, variable list, Örnek, Sayfa, canvas, "Diğer", Ad, Zorunlu, page, 4 mm fields, pattern, Şablonu ka… | pass |  |  |
| P-149 | QAction.triggered slots (B-047 / F-degerler-01 pattern) | grep of every `triggered` and `registry.connect` on this screen, then `QAction.trigger()` on all 17 sablonlar.* and app.* actions, checked and unchecked | no slot with a default parameter that receives the checked flag by accident | 0 instances: the slots are `delete_selected`, `duplicate_box`, `ask_variable`, `read_all_examples`, `focus_canvas`, `find_variable`, lambdas with no parameter; `set_show_reads(on=True)` and the two `lambda on=None` for … | pass |  |  |
