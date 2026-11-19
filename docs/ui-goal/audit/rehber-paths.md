# Rehber audit: click paths

Phase 4, Görev A, screen Rehber. Every click, double click, right click, drag, wheel and key on the elements of `rehber-inventory.md` that could be driven offscreen, plus the common mistakes (double click on a button, drop on the wrong place, cancel in the middle, resize, switch theme or text size while reading) and the keys of other tabs that could leak in. Driven with QTest and synthetic events against windows built by `tools/screenshots.py:build` (demo job, no real documents); the scripts are in the session scratchpad (`h.py` helpers, `p1.py` to `p9.py`), the raw rows in `/tmp/claude-0/p4/rehber/paths/`. The system print dialog, the PDF viewer and Windows' own context menu cannot run offscreen: the print dialog was replaced by a stand-in that answers at once and prints to a PDF file, `QDesktopServices.openUrl` was recorded instead of opened, and the app's data folder was pointed at the scratchpad (nothing was written to a real folder).

Result: **235 paths tried, 189 pass, 36 fail, 10 not decidable offscreen**. The failures are 27 distinct findings (01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 28, 29); rows with a finding id and result "pass" are findings found by looking at what a passing path did (the Note column says what). Tool runs are rows at the end: the screenshot matrix (72 images, 0 clipping lines), keywalk (24 of 24 combinations clean), `ui_measure.py` (63 failing rows, which are 3 findings plus the window-scroll rule).

Rules of the table: "Expected" is what the product documents (PRODUCT.md, DESIGN.md, `research/inventory-rehber.md`, the tooltip or accessible name of the element) or what the same control does elsewhere in the app. "Actual" is the measured value of the run. Pass means actual matches expected. Not decidable means the path needs a real desktop (see above). Element ids are those of `rehber-inventory.md`; E-000 is the main window itself.

Already in the ledger and seen again: B-006 (blank pages), B-007 (sheet and page wording), B-027 (Ctrl+G, silent on Rehber), B-028 (F5, enabled and silent), B-041 (focus probe artefact), B-055 (the job's undo stack reaches every tab). B-027 and B-028 were not driven again.

| ID | Element | Path (action) | Expected | Actual | Result | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-001 | E-001 title tab Rehber | Ctrl+6 from Kontrol | Rehber shown, focus in the reading card | tab=rehber focus=Reader:Tarama rehberi | pass |  |  |
| P-002 | E-014 Yardım konuları | F1 from Kontrol | Rehber shown | tab=rehber focus=Reader:Tarama rehberi | pass |  |  |
| P-003 | E-001 title tab Rehber | click the tab | Rehber shown | tab=rehber | pass |  |  |
| P-004 | E-003 Yükle link | Yükle with a job open: the guide link exists | a link | found | pass |  |  |
| P-005 | E-003 Yükle link | click 'Rehber'de tarama ayarları' | Rehber opens at its scanner settings section (Tarayıcı ayarları = section 4) | tab=rehber section=1 scroll=0 | FAIL | F-rehber-10 | opens at the top of the guide (inventory observation 6) |
| P-006 | E-069 menus | menu_structure for Rehber: entries that name the tab's commands | Dosya has both separator commands; Git has Rehber; Düzen has Bul | [('&Dosya', ['rehber.yazdir', 'rehber.pdf_ac']), ('Düz&en', ['app.bul', 'app.sonraki_sonuc', 'app.onceki_sonuc']), ('&Görünüm', []), ('Gi&t', []), ('&Araçlar', []), ('&Yardım', [])] | pass |  |  |
| P-007 | E-019 reader | PgDn | scrolls one page | value=622 | pass |  |  |
| P-008 | E-019 reader | PgUp | back to the top | value=0 | pass |  |  |
| P-009 | E-019 reader | End | bottom | value=1071 max=1071 | pass |  |  |
| P-010 | E-019 reader | Home | top | value=0 | pass |  |  |
| P-011 | E-019 reader | Down arrow | scrolls a line | value=20 | pass |  |  |
| P-012 | E-019 reader | Space (page down in a reader, 'Önizle' on Kontrol) | scrolls one page or nothing harmful | value 20->642 | pass |  |  |
| P-013 | E-019 reader | wheel down one notch | scrolls | value=60 | pass |  |  |
| P-014 | E-019 reader | wheel up one notch | back | value=0 | pass |  |  |
| P-015 | E-019 reader | click in the text | focus to the reader, no edit | focus=Reader:Tarama rehberi readOnly=True | pass |  |  |
| P-016 | E-035 text selection | Ctrl+A in the reader | selects the guide text | 2289 chars | pass |  |  |
| P-017 | E-035 text selection | Ctrl+C after Ctrl+A | copies text to the clipboard | 2289 chars; starts 'Tarama rehberi\nZımbalı evrak d' | pass |  |  |
| P-018 | E-035 text selection | double click on a word in the title | selects the word | 'rehberde' | pass |  |  |
| P-019 | E-019 reader | Tab from the reader | moves to the search field | focus=SearchField:Rehberde ara | pass |  |  |
| P-020 | E-019 reader | Shift+Tab from the search field | back to the reader | focus=Reader:Tarama rehberi | pass |  |  |
| P-021 | E-036 tip link 'Bir daha gösterme' | reach the link with the keyboard (25 Tab presses from the reader, then Enter) | a keyboard way to dismiss the tip | no stop shows the link; a Tab walk from the reader visits ['ActionButton', 'JobSwitch', 'PartsButton', 'QSlider', 'QSpinBox', 'QToolButton', 'Reader', 'SearchBox', 'SearchField', 'TitleTabs', 'TocList']; the card's focusNextPrevChild skips links; no key or menu command dismisses it | FAIL | F-rehber-08 | inventory R-09: 'Tab leaves the text (it does not walk the links)' |
| P-022 | E-036 tip link | anchor present at the right of the tip | anchorAt finds rehber:gizle | rehber:gizle | pass |  |  |
| P-023 | E-036 tip link | click 'Bir daha gösterme' | tip leaves, remembered | show_note=False flag=True | pass |  |  |
| P-024 | E-023 tip banner | get the tip back after dismissing it | a way back (Ayarlar, menu) | no control restores it (code: only prefs.set_flag, never cleared) | FAIL | F-rehber-08 | S4 |
| P-025 | E-003 Yükle empty page | empty Yükle (no job): a way to the guide | a guide link or hint on the empty Yükle page | none: [] | FAIL | F-rehber-10 | observation 6 |
| P-026 | E-001 Rehber without a job | open Rehber with no job | works (no job needed) | guide sections=7 prints enabled=True | pass |  |  |
| P-027 | E-019 reader / E-059..062 zoom | Ctrl++ in the reader | zoom 110 | zoom=110 | pass |  |  |
| P-028 | E-019 reader | Ctrl+- twice | zoom 90 | zoom=90 | pass |  |  |
| P-029 | E-019 reader | Ctrl+0 | back to 100 | zoom=100 | pass |  |  |
| P-030 | E-019 reader | Ctrl+= | zoom 110 | zoom=110 | pass |  |  |
| P-031 | E-019 reader | Ctrl+wheel up one notch | zoom +10 | zoom=120 | pass |  |  |
| P-032 | E-019 reader | Ctrl+wheel down two notches | zoom 100 | zoom=100 | pass |  |  |
| P-033 | E-019 reader | Ctrl++ 30 times | stops at 300 | zoom=300 | pass |  |  |
| P-034 | E-019 reader | zoom 300: text wider than the card? | no cut text (horizontal bar is off) | idealWidth=911 viewport=911 hbar visible=False | pass |  | doc height 8002 |
| P-035 | E-019 reader | Ctrl+- 40 times | stops at 50 | zoom=50 body px=8 | pass | F-rehber-21 | body text 8 px at zoom 50 (the 13 px floor of DEC-TYP-01 is about the type ramp at 100 %) |
| P-036 | E-019 reader | scroll to y=700, then Ctrl++ twice | the same text stays at the top of the card | heading 'Tarayıcı ayarları' was 37 px below the top edge, is -30 px after; top text before 'Tarayıcı ayarları' (section 3, bar 700); after 'Ayar' (section 4, bar 902/1385) | FAIL | F-rehber-20 | the position is kept as a fraction of the document, not as the text at the top |
| P-037 | E-060 zoom slider | drag to the maximum | zoom 300 | zoom=300 slider=300 | pass |  |  |
| P-038 | E-060 zoom slider | drag to the minimum | zoom 50 | zoom=50 | pass |  |  |
| P-039 | E-061 zoom in | click + | zoom 110 | zoom=110 button=24x24 | pass | F-rehber-15 | 24x24 (AUD-HIT-02) |
| P-040 | E-059 zoom out | click - twice | zoom 90 | zoom=90 | pass |  |  |
| P-041 | E-045 contents card | Ctrl+wheel over the contents list | zoom only through the guide, or none | zoom=100 | pass |  | records behaviour |
| P-042 | E-032 hit marks | search 'ayıraç', Ctrl++ | hits kept, current hit kept | hits 10->10, current 0->0 | pass |  |  |
| P-043 | E-046 contents row | click row 4 'Tarayıcı ayarları' | guide scrolls to it, row marked, status 'Bölüm 4 / 7' | section=4 bar=721 top of section=737 | pass |  |  |
| P-044 | E-046 contents row | click the last row 'Kısayollar' | scrolls (as far as the end allows), row 7 marked | section=7 bar=1071/1071 | pass |  |  |
| P-045 | E-046 contents row | scroll to top by hand | row 1 follows | section=1 | pass |  |  |
| P-046 | E-046 contents row | scroll to 700 by hand | the row of the section at the top follows (3) | section=3 | pass |  |  |
| P-047 | E-046 contents row | Down in the list | next section, guide scrolls | section=2 bar=312 | pass |  |  |
| P-048 | E-046 contents row | End | last section | section=7 | pass |  |  |
| P-049 | E-046 contents row | Home | first section, guide to its top | section=1 bar=163 | pass |  |  |
| P-050 | E-046 contents row | type 'Y' (type-ahead) | jumps to Yükleme | section=5 current=Yükleme | pass |  |  |
| P-051 | E-046 contents row | Enter on the marked row after a manual scroll | scrolls to the row's section again | bar 0->0 (row was 1) | FAIL | F-rehber-23 |  |
| P-052 | E-046 contents row | click the row that is already marked, after a manual scroll | scrolls to it | bar=163 (row 1) | pass |  |  |
| P-053 | E-046 contents row | double click row 2 | same as a click, nothing else | section=2 | pass |  |  |
| P-054 | E-046 contents row | right click row 3 | no menu, row chosen or nothing | section=3 popup=None | pass |  |  |
| P-055 | E-045 contents card | wheel over the contents list | the side panel scrolls or nothing (the list has no bar) | side scroll=0/0 guide bar unchanged=626 | pass |  | records behaviour |
| P-056 | E-047 hit counts | search 'ayıraç': counts per row | counts only on rows with hits | [None, 9, None, None, None, None, 1] | pass |  |  |
| P-057 | E-047 hit counts | sum of counts equals hits | equal | sum=10 hits=10 | pass |  |  |
| P-058 | E-046 contents row | search with no hits | no row marked | current row=-1 | pass |  |  |
| P-059 | E-015 side panel button / F9 | F9 | side panel hidden, guide wider | side hidden=True reader w=1318 | pass |  |  |
| P-060 | E-015 side panel button | F9 again | back | hidden=False | pass |  |  |
| P-061 | E-015 side panel button | tooltip changes after hide | says 'göster' after hiding | before: Yan paneli gizle (F9) | pass |  |  |
| P-062 | E-015 side panel button | tooltip while hidden | 'Yan paneli göster (F9)' | ['Yan paneli göster (F9)', 'Yan paneli göster (F9)', 'Yan paneli göster (F9)', 'Yan paneli göster (F9)', 'Yan paneli göster (F9)', 'Yan paneli göster (F9)'] | pass |  |  |
| P-063 | E-056 splitter handle | drag far to the left | side panel can grow only to a limit, guide keeps a minimum | sizes=[396, 914] reader min=396 | pass |  |  |
| P-064 | E-056 splitter handle | drag far to the right | side panel keeps its minimum width (320) and no clipping | sizes=[990, 320] side min=320 | pass |  |  |
| P-065 | E-056 splitter handle | resize with the keyboard | some key moves the splitter | handle focusPolicy=0 (no key moves it); F9 hides the panel | FAIL | F-rehber-28 | S4 |
| P-066 | E-040 search field | Ctrl+F from the reader | focus in the field, text selected | focus=SearchField:Rehberde ara | pass |  |  |
| P-067 | E-040 search field | Ctrl+F on Kontrol (app-wide key) | Rehber's field does not take it | tab=kontrol focus=TimelineView:Sayfalar | pass |  | Kontrol opens its own Ctrl+F (B-026 go-to dialog) |
| P-068 | E-009 Sonraki sonuç | F3 with an empty field | nothing happens; the user is told why or the key is silent | enabled={'app.sonraki_sonuc': None, 'app.onceki_sonuc': None} bar 0->0 result line='7 bölüm, 2 dakikalık okuma' | pass | F-rehber-17 | silent: F3 and Shift+F3 are disabled with no hits, nothing is shown |
| P-069 | E-009 Sonraki sonuç | buttons with an empty field | grey | prev enabled=False next enabled=False | pass |  |  |
| P-070 | E-009 Sonraki sonuç (command bar) | command bar button with an empty field | visible but disabled | [('ActionButton', False), ('QToolButton', False)] | pass |  |  |
| P-071 | E-037 no-result state | type 'zzzq' | empty state in place of the guide, 'Sonuç yok' line | stack=empty result="<b style='color:#16201a'>0</b> sonuç" title='“zzzq” için sonuç yok' | pass |  |  |
| P-072 | E-009 Sonraki sonuç | F3 with no hits | silent or says 'Sonuç yok' on screen | enabled={'app.sonraki_sonuc': None, 'app.onceki_sonuc': None}; the 'Sonuç yok' text of step() is only an accessible name (announce), never drawn; nothing changes on screen; focus=SearchField:Rehberde ara | FAIL | F-rehber-17 |  |
| P-073 | E-040 search field | Enter in the field with no hits | a visible 'Sonuç yok' or no-op | result accessible name='Sonuç yok', drawn text="<b style='color:#16201a'>0</b> sonuç" | pass |  | the empty state is the visible answer |
| P-074 | E-040 search field | Shift+Enter with no hits | no-op | stack=empty | pass |  |  |
| P-075 | E-037 'Kısayolları göster' | click | back to the guide, Kısayollar section | query='' section=7 stack=text focus=SearchField:Rehberde ara | pass |  |  |
| P-076 | E-037 'Aramayı temizle' | click | field empty, guide back, focus in the field | query='' focus=SearchField:Rehberde ara | pass |  |  |
| P-077 | E-040 search field | Esc in the field with text | clears, guide back | query='' | pass |  |  |
| P-078 | E-037 'Aramayı temizle' | Enter on the focused button | clears | query='zzzq' | FAIL | F-rehber-07 | Space works (next row); same cause as F-rehber-07 |
| P-079 | E-037 'Kısayolları göster' | Space on the focused button | goes to Kısayollar | query='' section=7 | pass |  |  |
| P-080 | E-037 no-result state | Esc with the focus in the field (the message sent to the window reaches the focus widget) | clears the search | query='' focus=SearchField:Rehberde ara | pass |  |  |
| P-081 | E-037 no-result state | Esc with the focus on 'Kısayolları göster' | clears the search | query='zzzq' | FAIL | F-rehber-18 | Esc clears from the field, reader and contents list only (rehber.py:eventFilter 542) |
| P-082 | E-037 no-result state | Tab walk of the whole window from the search field while 'no result' is shown (45 presses) | yes | 'Aramayı temizle' is stop 18 and 'Kısayolları göster' stop 19, after the command bar and before the search field (main pane before side panel) | pass |  |  |
| P-083 | E-037 no-result state | Tab, 10 presses only | reaches 'Aramayı temizle' and 'Kısayolları göster' | 10 presses cover the side panel and status bar; the two buttons are further round (see the 45-press row) | pass |  | first attempt was too short; kept for the record |
| P-084 | E-032 hit marks | type 'ayıraç' | hits marked, first current | hits=10 current=0 result="<b style='color:#16201a'>10</b> sonuç, 1 / 10" status="10<span style='color:#16201a; font-weight:600'> sonuç: ayıraç</span>" | pass |  |  |
| P-085 | E-009 Sonraki sonuç | F3 | next hit | current=1 | pass |  |  |
| P-086 | E-008 Önceki sonuç | Shift+F3 | previous hit | current=0 | pass |  |  |
| P-087 | E-008 Önceki sonuç | Shift+F3 on the first hit | wraps to the last | current=9 of 10 | pass |  |  |
| P-088 | E-009 Sonraki sonuç | F3 on the last hit | wraps to the first | current=0 | pass |  |  |
| P-089 | E-009 Sonraki sonuç | F3 with the focus in the reader | steps | current=1 | pass |  |  |
| P-090 | E-009 Sonraki sonuç | F3 with the focus in the contents list | steps | current=2 | pass |  |  |
| P-091 | E-043 next chevron | click | next hit | current=3 | pass |  |  |
| P-092 | E-042 previous chevron | click | previous hit | current=2 | pass |  |  |
| P-093 | E-040 search field | Enter | next hit | current=3 | pass |  |  |
| P-094 | E-040 search field | Shift+Enter | previous hit | current=2 | pass |  |  |
| P-095 | E-009 Sonraki sonuç | F3 on another tab with a search active in Rehber | does not step Rehber | current 2->2 | pass |  |  |
| P-096 | E-040 search field | leave the tab and return | query kept | query='ayıraç' hits=10 focus=SearchField:Rehberde ara | pass |  |  |
| P-097 | E-019 reader | Esc in the reader with a search active | clears the search | query='' focus=SearchField:Rehberde ara | pass |  |  |
| P-098 | E-046 contents row | Esc in the contents list | clears | query='' | pass |  |  |
| P-099 | E-051 count field | Esc in the count box with a search active | clears the search, or is ignored | query='ayıraç' focus=QSpinBox:Kaç adet ayıraç sayfası | pass |  | records behaviour |
| P-100 | E-055 Yazdır | Esc on the Yazdır button with a search active | clears (as in the other places) or nothing | query='ayıraç' | pass |  | records behaviour |
| P-101 | E-019 reader | Esc with no search | nothing | tab=rehber focus=Reader:Tarama rehberi | pass |  |  |
| P-102 | E-040 search field (x) | x is visible only with text | visible | visible=True | pass |  |  |
| P-103 | E-040 search field (x) | click the x | clears, focus to the field | buttons=2 size=[(22, 18), (22, 18)] | pass | F-rehber-14 | the x is 22 x 18 px at 100 % and 26 x 22 at 150 % (AUD-HIT-01 and AUD-HIT-02, 24 rows) |
| P-104 | E-040 search field (x) | click x | field empty | query='' focus=SearchField:Rehberde ara | pass | F-rehber-14 | the x is 22 x 18 px at 100 % and 26 x 22 at 150 % (AUD-HIT-01 and AUD-HIT-02, 24 rows) |
| P-105 | E-040 search field | only spaces | treated as empty | query='' stack=text x visible=True | pass |  |  |
| P-106 | E-040 search field | query 'AYIRAC' (upper case without Turkish letters) | hits | hits=10 first-section=2 result="<b style='color:#16201a'>10</b> sonuç, 1 / 10" | pass |  |  |
| P-107 | E-040 search field | query 'ayirac' (ASCII for ayıraç) | hits | hits=10 first-section=2 result="<b style='color:#16201a'>10</b> sonuç, 1 / 10" | pass |  |  |
| P-108 | E-040 search field | query 'İKİ' (dotted capital) | hits | hits=4 first-section=1 result="<b style='color:#16201a'>4</b> sonuç, 1 / 4" | pass |  |  |
| P-109 | E-040 search field | query 'iki' (iki matches İki / iki) | hits | hits=4 first-section=1 result="<b style='color:#16201a'>4</b> sonuç, 1 / 4" | pass |  |  |
| P-110 | E-040 search field | query 'ı' (dotless i) | hits | hits=232 first-section=1 result="<b style='color:#16201a'>232</b> sonuç, 17 / 232" | pass |  |  |
| P-111 | E-040 search field | query 'Ctrl+P' (a key typed as in the guide text) | hits | hits=1 first-section=2 result="<b style='color:#16201a'>1</b> sonuç, 1 / 1" | pass |  |  |
| P-112 | E-040 search field | query 'Kontrol+P' (a key as the panel button shows it) | hits? | hits=1 first-section=7 result="<b style='color:#16201a'>1</b> sonuç, 1 / 1" | pass |  | records behaviour |
| P-113 | E-040 search field | query 'ctrl' ('ctrl') | hits | hits=4 first-section=1 result="<b style='color:#16201a'>4</b> sonuç, 4 / 4" | pass |  |  |
| P-114 | E-040 search field | query 'kontrol' (the word Kontrol) | hits | hits=7 first-section=5 result="<b style='color:#16201a'>7</b> sonuç, 1 / 7" | pass |  |  |
| P-115 | E-040 search field | query 'a' (one letter) | many | hits=258 first-section=1 result="<b style='color:#16201a'>258</b> sonuç, 171 / 258" | pass |  | records behaviour |
| P-116 | E-040 search field | query '.*' (regex characters) | none | hits=0 first-section=- result="<b style='color:#16201a'>0</b> sonuç" | pass |  |  |
| P-117 | E-040 search field | query '(' (an open bracket) | none | hits=3 first-section=2 result="<b style='color:#16201a'>3</b> sonuç, 2 / 3" | pass |  | the guide text contains '(' (e.g. '(Ctrl+P)'); plain substring search |
| P-118 | E-040 search field | query '<b>' (html) | none | hits=0 first-section=- result="<b style='color:#16201a'>0</b> sonuç" | pass |  |  |
| P-119 | E-040 search field | query '&amp;' (html entity) | none | hits=0 first-section=- result="<b style='color:#16201a'>0</b> sonuç" | pass |  |  |
| P-120 | E-040 search field | query 'zımba sökücü' (a phrase in one block) | hits | hits=1 first-section=1 result="<b style='color:#16201a'>1</b> sonuç, 1 / 1" | pass |  |  |
| P-121 | E-040 search field | query 'masaya koyun' (words from the same paragraph in a different order) | none? | hits=0 first-section=- result="<b style='color:#16201a'>0</b> sonuç" | pass |  | records behaviour |
| P-122 | E-040 search field | query '1. Her' (list number text) | none | hits=0 first-section=- result="<b style='color:#16201a'>0</b> sonuç" | pass |  |  |
| P-123 | E-040 search field | query '300 dpi' (table cell) | hits | hits=1 first-section=4 result="<b style='color:#16201a'>1</b> sonuç, 1 / 1" | pass |  |  |
| P-124 | E-040 search field | query 'Önerilen' (table header) | hits | hits=1 first-section=4 result="<b style='color:#16201a'>1</b> sonuç, 1 / 1" | pass |  |  |
| P-125 | E-040 search field | query 'Bölüm' (the word the status bar uses) | ? | hits=0 first-section=- result="<b style='color:#16201a'>0</b> sonuç" | pass |  | records behaviour |
| P-126 | E-040 search field | query 'bir daha' (text inside the tip banner) | hits | hits=1 first-section=1 result="<b style='color:#16201a'>1</b> sonuç, 1 / 1" | pass |  |  |
| P-127 | E-040 search field | query 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' (600 characters) | none | hits=0 first-section=- result="<b style='color:#16201a'>0</b> sonuç" | pass |  |  |
| P-128 | E-031 'Kısayollar' table | 'Ctrl' and 'Kontrol' find different places | the same keys under one name | 'Ctrl': 4 hits in sections [1, 2, 7]; 'Kontrol': 7 hits in sections [5, 7] | FAIL | F-rehber-06 | the generated table and the buttons write 'Kontrol+', the typed guide text and the tip write 'Ctrl+' |
| P-129 | E-040 search field | 'a' (every block has hits): time to mark | under 100 ms | 258 hits in 16 ms | pass |  |  |
| P-130 | E-040 search field | typing while hits are repainted | no lag | 40 ms for 14 key presses | pass |  |  |
| P-131 | E-040 search field | Ctrl+F while F9 hid the side panel | shows it and focuses the field | hidden=False focus=SearchField:Rehberde ara | pass |  |  |
| P-132 | E-009 Sonraki sonuç | F3 while the side panel (and the result line) is hidden | steps; the counter is not visible | current=1 status="10<span style='color:#16201a; font-weight:600'> sonuç: ayıraç</span>" | pass |  | records behaviour (status bar still shows 'N sonuç: term' but not 'i / N') |
| P-133 | E-023 tip banner | search 'gösterme' (a hit in the tip's link), then dismiss the tip | hits recomputed, empty state shown | hits 1->0 stack=text | FAIL | F-rehber-19 |  |
| P-134 | E-023 tip banner | search 'ctrl+f': the tip text is searchable | hits in the tip | hits=1 first at block 'Ctrl+F ile rehberde arayın, Ctrl+tekerle' | pass |  | the tip is part of the searchable text |
| P-135 | E-047 hit counts | hits inside the tip banner are counted per section | the tip is not a section | first hit section=1 | pass |  | the tip is counted under the first section (Hazırlık); harmless |
| P-136 | E-051 count field | default value | 20 (the CLI default is 10) | 20 | pass | F-rehber-03 | window 20, CLI 10 (B-007 note) |
| P-137 | E-051 count field | Up | 21 | 21 | pass |  |  |
| P-138 | E-051 count field | PgUp | +10 (Qt step) | 31 | pass |  |  |
| P-139 | E-051 count field | Down twice | 29 | 29 | pass |  |  |
| P-140 | E-051 count field | Down at 1 | stays 1 | 1 | pass |  |  |
| P-141 | E-051 count field | Up at 200 | stays 200 | 200 | pass |  |  |
| P-142 | E-051 count field | type 0 | not accepted (range 1-200) | text='0' value=20 | pass |  |  |
| P-143 | E-051 count field | type 500 | not accepted or clamped | text='50' value=50 | pass |  | Qt keeps the last valid text while typing |
| P-144 | E-051 count field | empty the field, then press Ctrl+P | uses the last valid number, says so | text='' value=50 | pass |  | records behaviour |
| P-145 | E-051 count field | print with the box emptied | a valid count is printed (what number?) | pages in file=100 box text='' | pass |  | records behaviour |
| P-146 | E-051 count field | type letters | ignored | text='20' | pass |  |  |
| P-147 | E-051 count field | type 2.5 | integer only | text='25' | pass |  |  |
| P-148 | E-051 count field | paste 999 | clamped or refused | text='20' value=20 | pass |  |  |
| P-149 | E-051 count field | wheel over the box while it has no focus (scrolling the side panel) | value unchanged | 20->21 focusPolicy=15 | FAIL | F-rehber-24 | direct wheel event on the box; through the card scroller the wheel scrolls the panel instead |
| P-150 | E-051 count field | remembered between runs | kept in prefs | prefs has no key for it: restart gives 20 | FAIL | F-rehber-24 | S4 (inventory R-19) |
| P-151 | E-011 Ayıraç sayfasını yazdır | Ctrl+P on Rehber, count 3 | dialog, 6 pages, success toast | dialogs=1 pages=6 toast='3 ayıraç sayfası (6 sayfa) yazıcıya gönderildi.' | pass |  |  |
| P-152 | E-064 toast (success) | where it stands after printing | not over the Yazdır button or the count | toast (1058, 660, 312, 84) (card part) vs Yazdır button (993, 623, 334, 40) overlap=True (3 px of shadow room only; the card clears the button at 100 %, S:toast-print-ok-light-1366x768-100) | pass |  | at 150 % it does cover the button: see the next row |
| P-153 | E-063 print dialog | Ctrl+P then cancel (Esc / İptal) | nothing printed; says nothing or says 'iptal' | file exists=False toast='' | pass |  | silent cancel (inventory R-21) |
| P-154 | E-055 Yazdır | click | dialog, prints | dialogs=1 pages=6 | pass |  |  |
| P-155 | E-055 Yazdır | focus + Space | prints | dialogs=1 | pass |  |  |
| P-156 | E-055 Yazdır | focus + Enter | prints (its tooltip names Ctrl+P only; Enter on a primary button is expected) | dialogs=0 | FAIL | F-rehber-07 | same cause as F-kontrol-04 (actions.py _BUTTON_KEYS) |
| P-157 | E-055 Yazdır | double click | one print job (the real dialog is modal; here a stand-in answers at once) | 0 dialog(s) opened, 0 print job(s) sent; with the real modal system dialog the second click cannot arrive until the first closes | pass |  | not decidable offscreen: the system QPrintDialog cannot run |
| P-158 | E-011 Ayıraç sayfasını yazdır | Ctrl+P twice | each press asks again | dialogs=2 | pass |  | records behaviour |
| P-159 | E-011 Ayıraç sayfasını yazdır | Ctrl+P on Kontrol | not Rehber's printer dialog | dialogs from Rehber=0; tab=kontrol | pass |  |  |
| P-160 | E-011 Ayıraç sayfasını yazdır (command bar) | click the printer icon | dialog | dialogs=1 tip='Ayıraç sayfasını yazdır (Kontrol+P)' | pass |  |  |
| P-161 | E-055 Yazdır | count 1 to a PDF printer | 2N pages, quick, UI not frozen for long | 2 pages, 0.6 s on the GUI thread, file 1124 KiB; toast '3 ayıraç sayfası (6 sayfa) yazıcıya gönderildi.' | pass |  | printing runs on the GUI thread (no progress, Esc, or cancel) |
| P-162 | E-055 Yazdır | count 200 to a PDF printer | 2N pages, quick, UI not frozen for long | 400 pages, 0.7 s on the GUI thread, file 1413 KiB; toast '3 ayıraç sayfası (6 sayfa) yazıcıya gönderildi.' | pass |  | printing runs on the GUI thread (no progress, Esc, or cancel) |
| P-163 | E-065 toast (print failed) | printer refuses | toast with the reason and 'PDF olarak aç' | 'Ayıraç sayfaları yazdırılamadı: printer did not start. PDF olarak açıp oradan yazdırabilirsiniz.' | FAIL | F-rehber-12 | a next step is given (PDF), but the reason is English library text |
| P-164 | E-065 toast (print failed) | OSError from the printer | toast says what happened in Turkish | 'Ayıraç sayfaları yazdırılamadı: [Errno 13] Permission denied. PDF olarak açıp oradan yazdırabilirsiniz.' | FAIL | F-rehber-12 | reason text comes from the system / library, in English |
| P-165 | E-012 PDF olarak aç | click / call | file written in the data folder, opened | ['file:///tmp/claude-0/p4/rehber/prints/ayirac-sayfalari.pdf'] pages=4 | pass |  |  |
| P-166 | E-012 PDF olarak aç | where the file is | the person is told the folder, or the PDF viewer shows the path | folder /tmp/claude-0/p4/rehber/prints (the real one is the user data folder, e.g. %LOCALAPPDATA%\Evrakci); no toast, no status text names it; toast='' | FAIL | F-rehber-25 | inventory observation 7 |
| P-167 | E-012 PDF olarak aç | click twice quickly | one viewer window | openUrl called 2 times (the second write overwrites the first; with a viewer holding the file open on Windows the second goes to ayirac-sayfalari-2.pdf) | FAIL | F-rehber-25 | no feedback while writing; both clicks open the viewer |
| P-168 | E-012 PDF olarak aç | the usual file is held open by a viewer | falls to -2 and opens that | tried ['ayirac-sayfalari.pdf', 'ayirac-sayfalari-2.pdf']; opened ['file:///tmp/claude-0/p4/rehber/prints/ayirac-sayfalari-2.pdf']  | pass |  |  |
| P-169 | E-066 toast (PDF failed) | nothing can be written | toast with the reason and 'Yeniden dene' | 'Ayıraç sayfaları PDF olarak yazılamadı: Permission denied. Açık bir PDF görüntüleyiciyi kapatıp yeniden deneyin.' | FAIL | F-rehber-12 | reason is the OS text (English on most systems) |
| P-170 | E-012 PDF olarak aç | files left behind | old copies are cleaned up | names tried up to ayirac-sayfalari-20.pdf; nothing deletes them; count in folder now: 2 | FAIL | F-rehber-25 |  |
| P-171 | E-001..E-062 focus order | F6 five times from the reader | title band, command bar, work area, status bar, back | ['QToolButton', 'TitleTabs', 'ActionButton', 'Reader', 'QToolButton'] | pass |  |  |
| P-172 | E-001..E-062 focus order | Shift+F6 | previous region | Reader:Tarama rehberi | pass |  |  |
| P-173 | E-001..E-062 focus order | 30 Tab presses from the reader | one full round, every stop named, nothing skipped | ['SearchField:Rehberde ara', 'TocList:İçindekiler', 'QSpinBox:Kaç adet ayıraç sayfası', 'PartsButton:Ayıraç sayfasını yazdır (Kon', 'QToolButton:Rehber yazısı uzaklaştır', 'QSlider:Rehber yazısı yakınlaştırma ', 'QToolButton:Rehber yazısı yakınlaştır', 'TitleTabs:Sekmeler', 'JobSwitch:Açık iş: Kasım 2026 kapasite', 'SearchBox:Ara (Ctrl+K)', 'QToolButton:Menü (Alt)', 'ActionButton:Bul (Kontrol+F)', 'ActionButton:Ayıraç sayfasını yazdır (Kon', 'ActionButton:PDF olarak aç', 'ActionButton:Klavye kısayolları (Üst Kara', 'ActionButton:Yardım konuları (F1)', 'ActionButton:Yan paneli gizle (F9)', 'QToolButton:Diğer komutlar', 'Reader:Tarama rehberi', 'SearchField:Rehberde ara', 'TocList:İçindekiler', 'QSpinBox:Kaç adet ayıraç sayfası', 'PartsButton:Ayıraç sayfasını yazdır (Kon', 'QToolButton:Rehber yazısı uzaklaştır', 'QSlider:Rehber yazısı yakınlaştırma ', 'QToolButton:Rehber yazısı yakınlaştır', 'TitleTabs:Sekmeler', 'JobSwitch:Açık iş: Kasım 2026 kapasite', 'SearchBox:Ara (Ctrl+K)', 'QToolButton:Menü (Alt)'] | pass |  |  |
| P-174 | E-070 shortcut sheet | Shift+F1 on Rehber | the sheet opens with Rehber's keys | modal=None top=['ShortcutSheet', 'MainWindow'] | pass |  | records behaviour |
| P-175 | E-034 default context menu | right click on the guide text: entries | a Turkish menu opens from the mouse and the keyboard | not decidable offscreen: QTest sends no OS context-menu event, and popup.exec blocks. createStandardContextMenu() lists: Ko&pyala (Kontrol+C), &Bağlantı Konumunu Kopyala, Tümünü Seç (Kontrol+A); the keys are written with Qt's Turkish translation | not decidable |  | a real Windows run is needed (Menu key, Shift+F10, right click) |
| P-176 | E-034 default context menu | right click on the text opens a menu | a Turkish menu opens from the mouse and the keyboard | not decidable offscreen: QTest sends no OS context-menu event, and popup.exec blocks. createStandardContextMenu() lists: Ko&pyala (Kontrol+C), &Bağlantı Konumunu Kopyala, Tümünü Seç (Kontrol+A); the keys are written with Qt's Turkish translation | not decidable |  | a real Windows run is needed (Menu key, Shift+F10, right click) |
| P-177 | E-034 default context menu | Menu key in the reader | a Turkish menu opens from the mouse and the keyboard | not decidable offscreen: QTest sends no OS context-menu event, and popup.exec blocks. createStandardContextMenu() lists: Ko&pyala (Kontrol+C), &Bağlantı Konumunu Kopyala, Tümünü Seç (Kontrol+A); the keys are written with Qt's Turkish translation | not decidable |  | a real Windows run is needed (Menu key, Shift+F10, right click) |
| P-178 | E-034 default context menu | Shift+F10 in the reader | a Turkish menu opens from the mouse and the keyboard | not decidable offscreen: QTest sends no OS context-menu event, and popup.exec blocks. createStandardContextMenu() lists: Ko&pyala (Kontrol+C), &Bağlantı Konumunu Kopyala, Tümünü Seç (Kontrol+A); the keys are written with Qt's Turkish translation | not decidable |  | a real Windows run is needed (Menu key, Shift+F10, right click) |
| P-179 | E-040 search field | right click | system edit menu on a text field, none on a button/list | not decidable offscreen (no popup is created by QTest.mouseClick right button) | not decidable |  | records behaviour |
| P-180 | E-051 count field | right click | system edit menu on a text field, none on a button/list | not decidable offscreen (no popup is created by QTest.mouseClick right button) | not decidable |  | records behaviour |
| P-181 | E-055 Yazdır | right click | system edit menu on a text field, none on a button/list | not decidable offscreen (no popup is created by QTest.mouseClick right button) | not decidable |  | records behaviour |
| P-182 | E-046 contents list | right click | system edit menu on a text field, none on a button/list | not decidable offscreen (no popup is created by QTest.mouseClick right button) | not decidable |  | records behaviour |
| P-183 | E-019 reader | drop a PDF file on the guide | the app takes it as a scan (as on Yükle) or ignores it; the guide stays | drag accepted by the reader=True; guide text unchanged=True; source=''; tab=yukle | pass |  |  |
| P-184 | E-000 window | drag a PDF over the window while Rehber is shown | the app takes the drop (the drop overlay of Yükle) or refuses plainly | window accepts=True tab=yukle | pass |  | records behaviour |
| P-185 | E-035 text selection | drag selected text out of the reader | copy only (read-only) | readOnly=True; dropping text INTO the reader is ignored | pass |  |  |
| P-186 | E-019 reader | drop text on the guide | guide unchanged | unchanged=True | pass |  |  |
| P-187 | E-040 search field | drop text 'zzz' on the field | accepted as typing (standard) | query='' | pass |  | records behaviour |
| P-188 | E-046 contents row | drag a row up or down | not reorderable | dragEnabled=False dragDropMode=DragDropMode.NoDragDrop | pass |  |  |
| P-189 | E-000 window | resize 1366x768 -> 1100x640 with a search active | hits, current hit and position kept | hits=10 cur=1 (was 1) bar 0.47->0.39 splitter=[676, 368] | pass |  |  |
| P-190 | E-000 window | shrink to the minimum size | still usable, nothing cut | min=911x549 splitter=[600, 368] reader=596x464 side=368 | pass |  |  |
| P-191 | E-000 window | clipping check at the minimum size | 0 lines | 0 lines [] | pass |  |  |
| P-192 | E-000 window | clipping check at 1024x600 (below the target) | 0 lines | 0 lines []; window may be at its minimum: 1024x600 | pass |  |  |
| P-193 | E-019 reader | switch theme to dark while reading a search hit | position, hits, current hit kept | bar 0.47->0.00 section 2->1 hits 10->10 cur 1->1 (position back to the top; hits and current hit kept) | FAIL | F-rehber-09 |  |
| P-194 | E-019 reader | switch text size to 150 % at run time | position kept | bar max=1699 value=0 section 1; hits 10 cur 1 (position back to the top) | FAIL | F-rehber-09 |  |
| P-195 | E-034 default context menu | context-menu event (Menu key / Shift+F10 / right click on Windows) | a Turkish menu opens from the mouse and the keyboard | not decidable offscreen: QTest sends no OS context-menu event, and popup.exec blocks. createStandardContextMenu() lists: Ko&pyala (Kontrol+C), &Bağlantı Konumunu Kopyala, Tümünü Seç (Kontrol+A); the keys are written with Qt's Turkish translation | not decidable |  | a real Windows run is needed (Menu key, Shift+F10, right click) |
| P-196 | E-040 search field | context-menu event on the field | a Turkish menu opens from the mouse and the keyboard | not decidable offscreen (no popup is created by QTest.mouseClick right button) | not decidable |  | a real Windows run is needed (Menu key, Shift+F10, right click) |
| P-197 | E-019 reader | drop a PDF on the guide (no drag-enter first) | the window's own drop rule applies | tab after=rehber; pages in the open job 15->15; dialogs seen=[]; without the preceding drag-enter the window ignores it | pass |  | with a drag-enter first, the window takes the PDF as a scan: job gets 1 more file (15 -> 16 pages) and the tab jumps to Yükle, no question asked; same as the drop anywhere rule of Yükle (not a finding of this screen) |
| P-198 | E-038 guide file missing | start with docs/tarama-rehberi.md missing | the page says it and how to fix it; the rest works | sections=['Kısayollar'] toc rows=1 result='1 bölüm, 1 dakikalık okuma'; page text='Tarama rehberi\nRehber dosyası bulunamadı.\n￼\nCtrl+F ile rehberde arayın, Ctrl+tekerlek ile ' | pass |  |  |
| P-199 | E-038 guide file missing | search in the empty guide | works on what is there | hits=5 | pass |  | records behaviour |
| P-200 | E-038 guide file missing | the page tells the person what to do | 'Rehber dosyası bulunamadı.' plus a next step (reinstall, where the file should be) | text is 'Rehber dosyası bulunamadı.' only; no path, no next step; the tab still lists 'Kısayollar' as 'Bölüm 1 / 1' | FAIL | F-rehber-13 |  |
| P-201 | E-024 sections / E-046 contents | 30 sections (one with a 40-character unbroken run) at 150 % text | the contents list is visible | 31 rows, toc height=1496, side scroll max=1651, side height=612; the contents card does not show at all, the panel is blank under the search line (S:long-30-sections-light-1366x768-150) | FAIL | F-rehber-11 |  |
| P-202 | E-046 contents row | a section title longer than the list (150 % text) | wraps or elides with a tooltip | 24 of 31 titles are wider than the row (421 px); first: ('Çok uzun bir bölüm başlığı örneği numara 1', 468); row tooltip=''; accessible name keeps the full title | FAIL | F-rehber-22 | the row text is cut by the style with no tooltip |
| P-203 | E-000 window | clipping check with the long guide at 150 % | 0 lines | 0 lines [] | pass |  |  |
| P-204 | E-019 reader | a 160-character unbroken word in a list at 150 % text | wraps or scrolls sideways; nothing cut | idealWidth=839 viewport=839; horizontal bar always off; the word is cut at the card edge: False | pass | LONG-WORD |  |
| P-205 | E-047 hit counts | search 'a' on 30 sections: counts column | numbers fit the row (caption numerals) without hiding the title | hits=5434; max count digits=3 | pass |  | records behaviour |
| P-206 | E-040 search field | 300-character query | field scrolls inside, empty state wraps the term | empty title width=5270 vs card 990 wrap=True | pass |  |  |
| P-207 | E-058 status 'N sonuç: term' | a long term in the status bar | elides or leaves room for the zoom slider | status hits width=778 text="150<span style='color:#16201a; font-weight:600'> sonuç: uzun" | pass |  | records behaviour |
| P-208 | E-019 reader (job keys leaking into the guide) | Ctrl+Z with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (0, 0, 0, False, 1, 'rehber', 0); dialogs=[] | FAIL | F-rehber-01 |  |
| P-209 | E-019 reader (job keys leaking into the guide) | Ctrl+Y with the guide focused | nothing in the job changes while reading the guide | before (0, 0, 0, False, 1, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | FAIL | F-rehber-01 |  |
| P-210 | E-019 reader (job keys leaking into the guide) | Ctrl+Shift+Z with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-211 | E-019 reader (job keys leaking into the guide) | Del with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-212 | E-019 reader (job keys leaking into the guide) | Enter with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-213 | E-019 reader (job keys leaking into the guide) | N with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-214 | E-019 reader (job keys leaking into the guide) | U with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-215 | E-019 reader (job keys leaking into the guide) | K with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-216 | E-019 reader (job keys leaking into the guide) | M with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-217 | E-019 reader (job keys leaking into the guide) | R with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-218 | E-019 reader (job keys leaking into the guide) | Ctrl+G with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-219 | E-019 reader (job keys leaking into the guide) | F5 with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-220 | E-019 reader (job keys leaking into the guide) | Ctrl+E with the guide focused | nothing in the job changes while reading the guide | goes to Dışa Aktar (the app-wide key); nothing is exported | pass |  | app-wide key, not a leak |
| P-221 | E-019 reader (job keys leaking into the guide) | Ctrl+D with the guide focused | nothing in the job changes while reading the guide | before (1, 0, 0, False, 2, 'rehber', 0) after (1, 0, 0, False, 2, 'rehber', 0); dialogs=[] | pass |  |  |
| P-222 | E-039 side panel | 1366x768 at 150 % text: is the print card visible without scrolling? | visible, or reachable by wheel, Tab and Ctrl+P | below the fold: side scroll max 547 px; reached by wheel (one card per notch), Tab (focus reveal) and Ctrl+P (S:side-scrolled-print-light-1366x768-150) | pass |  | DESIGN.md Layout: at 150 % panes scroll in their own area |
| P-223 | E-039 side panel / E-046 | 13-section guide at 150 %: Tab to the contents list, wheel over the panel | contents list and print card both reachable | Tab shows the list (rows 12 and 13 cut at the bottom); the wheel goes search -> print card and skips the list (S:toc-taller-12sections-light-1366x768-150, -tab-toc, -scrolled); threshold measured: 10 sections at 150 %, 12 at 100 % | FAIL | F-rehber-11 | the shipped guide has 7 sections |
| P-224 | E-064 toast (success) | 150 % text, print card scrolled into view, then print | the toast does not hide the Yazdır button | toast (939,640,431,96) over the button (921,643,397,48) for 6 s | FAIL | F-rehber-26 |  |
| P-225 | E-072 separator sheet | render the sheet and read its labels | 'AYIRAÇ' and 'Bu sayfa çıktıya girmez' | 'AYIRA□' and 'Bu sayfa □□kt□ya girmez': Ç, ç and ı have no glyph in Pillow's built-in Aileron font (S:separator-sheet-150dpi); the same 8 Turkish letters tested (Ç ç ı İ ş ğ ü ö) all draw as the missing-glyph box | FAIL | F-rehber-02 |  |
| P-226 | E-072 separator sheet | decode the QR at 100, 150, 300 and 600 dpi, and at half size, blurred and rotated 3 degrees (zxingcpp) | EVRAKCI-AYIRAC-1 | decoded in all five cases | pass |  |  |
| P-227 | E-072 separator sheet | quiet zone against the unprintable edge (margins are set to 0) | QR far from the paper edge | ink starts 68 mm from the sides and 80 mm from the top (bbox 404..838 x 474..1251 px at 150 dpi), so a printer's 4 to 6 mm unprintable edge cannot touch it (inventory observation 8 answered) | pass |  |  |
| P-228 | E-063 print dialog | does the print job ask for two-sided output? | N sheets for N separators, or a plain note that two-sided must be chosen | QPrinter duplex is never set (default DuplexNone); the job is 2N pages, so on a one-sided printer N separators take 2N sheets; 'A4, iki yüze aynı QR' and the guide's 'iki yüzüne de basılır' read as if two-sided were automatic | FAIL | F-rehber-03 | B-007 related |
| P-229 | E-051 count / E-064 | read the three numbers for one job: box, toast, tooltip, guide, CLI | one unit | box: 'sayfa' next to the count; tooltip 'ayıraç sayfası sayısı'; toast '20 ayıraç sayfası (40 sayfa)'; guide 'yaprağın iki yüzüne'; CLI 'yaprak'; default 20 in the window, 10 on the command line | FAIL | F-rehber-03 | B-007 (open, strict xfail test exists) |
| P-230 | E-031 'Kısayollar' table | read the generated table: the zoom row and the Esc row | 'Ctrl++ ve Ctrl+-' and 'Esc' | 'Kontrol+Sayı++ ve Kontrol+-' (the keypad plus, because the 'Num' filter runs on the translated name 'Sayı') and 'Vazgeç' for Esc; 'F3 ve Üst Karakter+F3' (S:scrolled-end-light-1366x768-100) | FAIL | F-rehber-05 |  |
| P-231 | E-019 reader | follow the guide: 'Çift taraflı taramadaki boş arka yüzleri iş ayarından atabilirsiniz' - find the setting in the window | a control, menu entry or palette command | none in 6 tabs (no widget text, tooltip or action contains 'boş'); the demo job keeps its blank page in document 2 (3 / 7 / 3 pages); ctl.set_drop_empty(True) gives 3 / 6 / 3; only `evrakci is bos-sayfalar ac` sets it | FAIL | F-rehber-04 | B-006 (open, strict xfail test exists) |
| P-232 | E-019 reader | 'Boş sayfalar hiçbir zaman belge ayırmaz' | a blank page inside a document does not cut | document 2 of the demo job holds the blank page and stays one document | pass |  |  |
| P-233 | E-000 window | tools/screenshots.py matrix --allow (6 tabs x 3 themes x 2 sizes x 2 text sizes) | 0 KIRPILMA on Rehber | 72 images, 0 KIRPILMA lines in the whole matrix; the 12 Rehber images are in /tmp/claude-0/p4/rehber/matrix/ | pass |  |  |
| P-234 | E-001..E-062 focus order | keywalk.py --tab rehber, 3 themes x 4 text sizes x 2 window sizes | no trap, nothing unnamed, work area reached | 24 of 24 combinations OK; 18 stops: job switch, search box, menu, Bul, Yazdır, PDF olarak aç, Kısayollar, Yardım, panel, Diğer, reader, search field, contents, count, Yazdır, 3 zoom controls | pass |  |  |
| P-235 | E-000 window | tools/ui_measure.py --tab rehber (3 themes x 2 sizes x 2 text sizes) | 0 failing rules | 3,375 rows: 3,210 pass, 63 fail, 102 skip; fails: AUD-HIT-02 36 (search x 12, zoom buttons 24), AUD-HIT-01 12 (search x), AUD-WIN-02 9, DEC-FOC-01 6 (tab strip probe) | FAIL | F-rehber-14, F-rehber-15, F-rehber-16, F-rehber-29 |  |
