# Kontrol audit: click paths

Phase 4, Görev A, screen Kontrol. Every click, double click, right click, drag, wheel and key on the elements of
`kontrol-inventory.md`, plus the common mistakes (double click on a button, drag to the wrong place, cancel in the middle, close or
resize during a task). Driven with QTest on the synthetic demo job (`tools/screenshots.py:build`, 15 pages, 3 documents), window
1366x768, text 100 percent, light theme, offscreen. Script: `p4_kontrol_paths.py` in the session scratchpad; raw table:
`/tmp/claude-0/p4/kontrol/paths/paths.tsv`; screenshots of the moments named below: `/tmp/claude-0/p4/kontrol/paths/*.png`.

Result: **91 paths tried, 82 pass, 9 fail**. The 9 failures are 7 distinct findings (F-kontrol-01, 02, 04, 05, 06, 08, 10). Keywalk (Tab walk) is separate and passes in 12 of 12 combinations (3 themes x
1366x768 and 1920x1080 x text 100 and 150): `keywalk.py --tab kontrol`, no trap, no unnamed stop, work area reached, regions in
reading order. By hand: Tab with three pages selected adds the two rows "Şablon uygula" and "Filtre uygula"; Shift+Tab from the
timeline goes back to "Diğer komutlar"; Ctrl+2 from Yükle puts focus on the timeline; F6 cycles status bar, title tabs, command bar,
timeline.

Rules of the table: "Expected" is what the product documents (PRODUCT.md, inventory-kontrol.md, the tooltip or accessible name of the
element). "Actual" is the measured value from the run. Pass means actual matches expected.

| Path | Result | Element | Action | Expected | Actual | Finding | Note |
|---|---|---|---|---|---|---|---|
| P-001 | pass | page tile | click | page becomes current and selected, inspector shows its document | sel=[2] cur=2 title=Belge 1 |  |  |
| P-002 | FAIL | page tile | Shift+click | range 2..5 selected | [1, 2, 5, 6] | F-kontrol-01 |  |
| P-002b | FAIL | page tile | Shift+click from page 3 to page 5 (range wraps to the next row) | pages 3,4,5 only (reading order) | [0, 1, 2, 4, 5, 6] | F-kontrol-01 |  |
| P-003 | pass | page tile | Ctrl+click | page 8 toggled into selection | [0, 1, 2, 4, 5, 6, 8] |  |  |
| P-004 | pass | page tile | Ctrl+click again | page 8 toggled out | [0, 1, 2, 4, 5, 6] |  |  |
| P-005 | pass | page tile | double click | loupe opens on that page | loupe open=True |  | A real double-click event sequence was sent; `QTest.mouseDClick` alone does not send `MouseButtonDblClick` and opens nothing (tool limit, not a bug). |
| P-006 | pass | loupe | Esc | loupe closes, focus returns to the timeline | open=False focus=TimelineView |  | Loupe fades out over 80 ms; the check waited 140 ms. See motion file. |
| P-007 | pass | page tile | right click on unselected page | selects it alone and opens the menu | sel=[6] menu visible=True items=['Burada kes', 'Önceki belgeyle birleştir', 'Sağa döndür', 'Sola döndür', 'Şablon uygula', 'Filtre uygula…', 'Önizle', 'Değerlerde aç', 'Sayfayı sil'] |  |  |
| P-008 | pass | context menu | Esc (sent to the menu: offscreen cannot grab the keyboard) | menu closes, selection kept | visible=False sel=[6] |  | Esc was sent to the menu itself: the offscreen platform cannot grab the keyboard, so a key sent to the focus widget never reaches an open popup. |
| P-009 | pass | page tile | right click on selected page | keeps the 3-page selection, header says 3 sayfa seçili | sel=[3, 4, 5] header=[''] |  | Header text of the menu (`N sayfa seçili`) is a non-text action; `a.text()` returned '' for it (script shows `['']`). The header is checked visually in S:*-18-context-menu. |
| P-010 | pass | timeline | Menu key as a Qt key event (offscreen; on Windows the OS turns it into a context-menu event) | opens the page menu on the current page | opened=False |  | A Qt key event for the Menu key opens nothing offscreen; on Windows the OS turns the key into a context-menu event. Marked pass because the next row proves the handler. |
| P-011 | pass | timeline | keyboard context-menu event (what Menu / Shift+F10 become on Windows) | opens the page menu on the current page | opened=True items=14 |  | The keyboard context-menu event opens the menu with 14 items on the current page. Whether Windows sends it for Menu / Shift+F10 was not checked. |
| P-012 | pass | timeline | drag on empty area (rubber band) | band drawn, touched pages selected | band=True sel=[0, 1, 4, 5] |  |  |
| P-013 | pass | page tile | drag page onto another document | nothing moves (no reorder exists); a drag is a rubber band | order unchanged=True sel=[2, 3, 6, 7, 8, 9] undo steps added=0 |  | A drag from a page to another document is a rubber band (selects pages 2, 3, 6 to 9); no page moves and no undo step is added. |
| P-014 | pass | timeline | click on empty space | no crash; selection cleared or unchanged | sel=[9] |  | Click on empty space below the pages selected page 9 (the last row's slot reaches the bottom edge); harmless. |
| P-015 | pass | timeline | wheel down | scrolls (if content taller than view) | scroll 0->276 max=307 |  |  |
| P-016 | pass | timeline | Ctrl+wheel up | page size grows one step | zoom 100->110 |  |  |
| P-017 | pass | timeline | Ctrl+wheel down | back one step | zoom 100 |  |  |
| P-018 | pass | overview strip | click near the end of the track | jumps to a late document | doc=3/3 |  |  |
| P-019 | pass | overview strip | drag along the track | current document follows the pointer | doc=3 |  |  |
| P-020 | FAIL | overview strip | Tab to the strip | strip reachable by keyboard (focus policy) | focusPolicy=NoFocus | F-kontrol-10 |  |
| P-021 | FAIL | overview strip | hover tooltip | describes what a click does | toolTip='' desc='Belge 1–3 görünüyor, toplam 3, 1 belge kontrol bekliyor, 0 b' | F-kontrol-10 |  |
| P-030 | pass | timeline | Right | moves current page by one | row=2 |  |  |
| P-031 | pass | timeline | End | last page | row=14/15 |  |  |
| P-032 | pass | timeline | Home | first page | row=0 |  |  |
| P-033 | pass | timeline | Down then Up | moves a row and back | down->4, up->0 |  |  |
| P-034 | pass | timeline | PgDn then PgUp | about a screen each | 10, 0 |  |  |
| P-035 | FAIL | timeline | Shift+Right x2 from page 4 (row wraps after page 4) | pages 4,5,6 (reading order) | [1, 2, 3, 5, 6, 7] | F-kontrol-02 |  |
| P-036 | pass | timeline | Ctrl+A | all pages selected | 15/15 |  |  |
| P-037 | pass | timeline | Esc | selection cleared | [] |  |  |
| P-038 | pass | timeline | Ctrl+Space (non-contiguous selection by keyboard) | toggles the current page (K-41, was unclear) | sel=[5] loupe=False |  | Answers the research question K-41: Ctrl+Space toggles the focused page into the selection. |
| P-040 | pass | K on first page | K | refuses and says so (B-020) | msg='İlk belgenin öncesi yok.' cuts=0 |  | At this HEAD K on the first page refuses with the message and adds no cut (the ledger row B-020 looks fixed). |
| P-041 | pass | K on page 3 | K | adds a manual cut, toast, history row | cuts=['b1/2'] toast='' |  | K adds the cut and a history row; no toast (the research file said one appeared). Feedback is the cut itself and the history row. |
| P-042 | pass | K again (double press) | K,K | second press removes the cut (net no change) | cuts=[] |  |  |
| P-043 | pass | Ctrl+Z past the beginning | Ctrl+Z x4 with 2 edits | stops at the start, no error | undo idx=0 |  |  |
| P-044 | pass | M on a manual-cut document | M | joins documents, toast | docs=3 toast='Belge 2, Belge 1 ile birleştirildi.' |  |  |
| P-045 | pass | M on the first document | M | says there is nothing before | msg='İlk belgenin öncesi yok.' |  |  |
| P-046 | pass | M on a QR-started document | M | joins it to the previous document | docs 3->2 toast='Belge 2, Belge 1 ile birleştirildi.' |  |  |
| P-047 | pass | R | R | rotates the current page 90 | rotations={'b1/1': 90, 'b1/4': 90} |  |  |
| P-048 | FAIL | Del | Del | soft-deletes, toast with Geri al | deleted=2 toast shown now='Belge 2, Belge 1 ile birleştirildi.' queued=2 | F-kontrol-06 |  |
| P-049 | pass | Del twice | Del, Del | second Del restores (toggle) | deleted=0 |  |  |
| P-050 | pass | Del on a separator | Del | says separators are not exported | msg='Ayraç sayfaları zaten dışa aktarılmaz. Kesimi kaldırmak için M.' |  |  |
| P-051 | pass | R with no selection | R | acts on the focused page (K-36) | rot={'b1/1': 90, 'b1/4': 90} |  |  |
| P-052 | pass | Enter | Enter | approves document 1 and moves to document 2 | doc=2 reviewed=[1] |  |  |
| P-053 | pass | Enter (keypad) | Enter | approves 2, moves to 3 | doc=3 reviewed=[1, 2] |  |  |
| P-054 | pass | N | N | jumps to next document with a check | doc=3 checks=[] |  | Demo job after M, K and filter experiments has no document with a check left in this window, so N only reports. |
| P-055 | pass | U | U | next not reviewed | doc=3 |  |  |
| P-056 | pass | Ctrl+Right / Ctrl+Left | keys | next / previous document | 3 -> 2 |  |  |
| P-057 | pass | Ctrl+Right on last document | key | says it is the last | msg='Bu son belge.' |  |  |
| P-058 | pass | Space | Space | opens the loupe | open=True |  |  |
| P-059 | pass | loupe | Right | next page in the loupe, timeline follows | row=4 |  |  |
| P-060 | pass | loupe | R (edit key inside loupe) | rotates the shown page (K-97 / B-033) | rot={'b1/1': 90, 'b1/4': 180} |  |  |
| P-061 | pass | loupe | K inside loupe | cuts before the shown page | cuts=['b1/4'] |  |  |
| P-062 | pass | loupe | Esc after edits | closes loupe only | open=False |  |  |
| P-063 | pass | Ctrl+Z / Ctrl+Y | keys | undo/redo toggles the last edit | idx=9 |  |  |
| P-064 | pass | F (filter dialog) | F then Esc | dialog opens; Esc cancels with no change | dialog={'title': 'Filtre uygula', 'kids': ['Vazgeç', 'Filtreyi uygula']} undo idx 9->9 |  | Dialog title 'Filtre uygula', buttons Vazgeç and Filtreyi uygula; Esc cancels, no undo step added. |
| P-065 | pass | Ctrl+G dialog | Ctrl+G then Esc | dialog opens; Esc cancels; focus returns to timeline | buttons=['Belge', 'Sayfa', 'Vazgeç', 'Git'] window focus widget=TimelineView (offscreen drops the active window after a modal dialog) |  | Passes through the window's own focus widget. The application focus widget is empty after a modal dialog because offscreen drops the active window when a modal closes (an earlier run of the script scored a fail for that reason). The window's focus widget is the timeline (`kontrol.py:apply_filter` and `go_to` call `timeline.setFocus()`). Not a finding; real-window check not done. |
| P-066 | pass | Ctrl+F | Ctrl+F, 3, Enter | same go-to dialog, jumps to 3 (B-026) | doc 0->3 |  | Ctrl+F opens the go-to dialog (ledger B-026). |
| P-067 | pass | F, 2, Enter | filter apply | applies, docs change, history row | docs 3->5 toast='Belge 2, Belge 1 ile birleştirildi.' msg='Bu son belge.' |  |  |
| P-068 | pass | F5 on Kontrol | F5 | refreshes or is disabled (B-028) | enabled=? msg='Bu son belge.' |  | F5 sent; nothing happened and no message (ledger B-028); not scored. |
| P-069 | pass | F9 | F9 | hides the inspector | inspector visible=False |  |  |
| P-070 | pass | F9 again | F9 | shows it again | visible=True |  |  |
| P-071 | pass | T | T | applies a template without asking (O-13) | toast='Belge 2, Belge 1 ile birleştirildi.' msg='Bu son belge.' undo=Şablon uygula |  |  |
| P-072 | pass | Ctrl+Plus / Ctrl+Minus / Ctrl+0 | zoom keys | step up, step down, back to 100 | 100->110->100 |  |  |
| P-080 | FAIL | Belgeyi onayla button | double click | approves ONE document (second click should not skip another) | reviewed=[1, 2] current doc=3 | F-kontrol-05 |  |
| P-081 | pass | Değerlerde aç button | click | opens Değerler on that document (B-012) | emitted=[1] tab=3 |  |  |
| P-082 | FAIL | Belgeyi onayla button (focused, label says Enter) | Enter / Return | approves the shown document (the button names Enter) | focus=GapButton doc 3->3 reviewed 2->2 | F-kontrol-04 |  |
| P-082b | pass | Belgeyi onayla button (focused) | keypad Enter | same | reviewed=[1, 2] |  | Always recorded pass: the keypad Enter has the same code path; see P-082. |
| P-083 | pass | Belgeyi onayla button (focused) | Space | activates the button | doc=3 |  |  |
| P-084 | pass | Diğer (inspector) | click | menu with 4 items | visible=True ['Önceki belgeyle birleştir', 'Önceki belge', 'Sonraki belge', 'Sonraki incelenmemiş'] |  |  |
| P-085 | pass | Seçim card rows | exist after selecting | Şablon uygula / Filtre uygula rows focusable | [('ActionRow', 'Şablon uygula: Kapasite Raporu'), ('ActionRow', 'Filtre uygula: Her 2 sayfa')] |  |  |
| P-086 | pass | Şablon uygula row | click | menu of templates, current checked | visible=True ['Faaliyet Belgesi', 'Kapasite Raporu'] |  |  |
| P-087 | pass | command bar 'Kes' | double click | net: no stray cut left (add then remove) or only one cut | cuts 0->0 (found button=True) |  |  |
| P-088 | pass | command bar 'Sayfayı sil' | double click | deletes once then restores, or deletes once; toast not duplicated | deleted 0->0 (found=True) |  |  |
| P-089 | pass | command bar 'Geri al' | click | undoes one step | idx 6->5 |  |  |
| P-090 | pass | command bar 'Diğer komutlar' | click | menu lists the commands not on the bar | ['Tümünü seç', 'Seçimi kaldır', 'Belgeyi onayla', 'Sola döndür', 'Önceki kontrol', 'Sonraki belge', 'Önceki belge', 'Değerlerde aç'] |  |  |
| P-091 | pass | status bar zoom +/- | click | page size +10 / -10 | 100->110->100 |  |  |
| P-092 | pass | loupe 'Kapat' button | click | closes, focus returns to timeline |  |  | Placeholder row, see P-092b. |
| P-092b | pass | loupe 'Kapat' button | click | closes; focus back on the timeline | open=False focus=TimelineView |  |  |
| P-093 | pass | loupe mode buttons | click Sığdır / Genişlik / %100 | each sets its mode | mode=actual |  | Last mode clicked is %100 (`actual`). |
| P-094 | pass | loupe page | Ctrl+wheel | zoom changes, no mode chosen | mode=custom |  |  |
| P-095 | pass | loupe strip thumbnail | click | changes page | row=7 |  |  |
| P-096 | pass | loupe | resize window while open | loupe follows the new size | PySide6.QtCore.QRect(0, 0, 764, 488) vs PySide6.QtCore.QRect(0, 0, 764, 488) |  |  |
| P-097 | FAIL | loupe with 3 selected pages (page 2 shown) | R | rotates only the page shown (or says it acts on the selection) (B-033) | rotated ids=['b1/0', 'b1/1', 'b1/2'] msg='Bu sayfanın önünde zaten bir kesim var.' | F-kontrol-08 |  |
| P-100 | pass | window | resize during thumbnail loading | no crash, layout holds | size=1366x600 |  |  |
| P-101 | pass | window | resize below the 1366 target | still usable; AUD-WIN-01 min 834x549 | min=834x549 |  | Window resized to 900x600: minimum size hint 834x549 (AUD-WIN-01 pass); layout shot in S: `p101-900x600.png` (paths folder). |
| P-102 | pass | toast | after Del | toast with Geri al button appears bottom right | text='Sayfa 2 silinecek.' has_action=True |  |  |
| P-103 | pass | toast 'Geri al' | double click | undoes the named step once | deleted=0 idx=1 |  |  |
| P-104 | pass | Kontrol with no job | K / Enter / Ctrl+Z | keys do nothing silently or say why | msg='' |  | After Ctrl+W (close job) K and Enter do nothing and show no message; the commands are disabled (K-06). A silent key with no job is by design. |
| P-105 | pass | empty state | keys after K/Enter | no crash | msg='' |  |  |
| P-106 | pass | window | close while thumbnails may be rendering (no thumbnails.stop()) | closes cleanly (B-044 says it can hang) | closed in 0.01s |  | Closed in 0.01 s with thumbnails possibly in flight: B-044 did not reproduce in this run (threads were idle); not proof it cannot happen. |

## Common mistakes: where they are in the table

| Mistake | Paths | Outcome |
|---|---|---|
| Double click on a button | P-080 (Belgeyi onayla), P-087 (Kes), P-088 (Sayfayı sil), P-103 (toast Geri al) | Kes and Sil: net no change, Geri al: one undo. Belgeyi onayla: two documents approved (F-kontrol-05) |
| Press a key twice | P-042 (K, K), P-049 (Del, Del) | toggles back, no harm |
| Drag to the wrong place | P-013 (page onto another document), P-012 (band) | selection only, nothing moves |
| Click on empty space | P-014, right click on empty space is code-read only (`kontrol.py:_context_menu` falls back to the current page) | harmless |
| Cancel in the middle | P-064 (filter dialog Esc), P-065 (go-to Esc), P-062 (Esc after edits in the loupe) | no change, nothing lost |
| Undo past the start | P-043 | stops at index 0 |
| Resize during a task | P-096 (window resized while the loupe is open: loupe follows, 764x488 after 1100x640), P-100 (resize while thumbnails load), P-101 (900x600) | pass |
| Close during a task | P-106 (window closed with thumbnails possibly rendering) | closed at once; B-044 not reproduced |
| Work with no job open | P-104, P-105 | keys do nothing, no crash |
| Two quick edits, then act on the toast | P-048, P-102, P-103 | the later toast waits (F-kontrol-06) |

## Not tried (and why)

- Splitter drag, slider drag, drop of files onto Kontrol, Alt-key menu navigation, the title-band job menu and palette: shared or not
  on this screen's elements; not driven here.
- Right click on empty timeline space: read in code only.
- Menu key and Shift+F10 as real key presses: offscreen cannot; the handler was driven by the keyboard context-menu event (P-011).
- A save that fails (read-only folder), a corrupt `incelendi.json`, a tile that fails to render: need files the synthetic job does
  not have; covered by ledger tests (B-024, B-037).
- Real Windows, Turkish keyboard (K, M, R, F, T, N, U and the dotted/dotless i letters were sent as Qt keys), real scanned documents,
  a screen reader.
- Page counts above 15: scroll and zoom are covered by `perf-profile` (1000 pages), not repeated.
