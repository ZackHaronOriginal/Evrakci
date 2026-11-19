# Değerler audit: state matrix

Phase 4, Görev A, screen Değerler. Rows are elements or groups from `degerler-inventory.md` (E-ids). Columns are the states from the phase plan. Every cell is one of: a
screenshot reference (`S:<name>`), a path row (`P-nnn` in `degerler-paths.md`), a measured row (`M:`), a fact from the long-content runs (`L:`), or `n/a: reason`. A cell that
could not be filled says `GAP: reason` instead of a guess; the gaps are counted at the end.

How the cells were made (all offscreen, synthetic data, window 1366x768, text 100 percent unless named):
- Screenshots: `/tmp/claude-0/p4/degerler/states/<theme>-<NN>-<name>.png`, theme `light`, `dark`, `hc` (213 files: every `S:<NN>` below exists in all three themes). Written by
  a script that builds the demo window fresh in each theme and puts the element into the state with QTest (mouse move, press, Tab focus, selection, header clicks, an
  editor opened with F2, `context_menu()`, a variable added to the template for the unread state, a value emptied for Okunamadı, the toggles for Tümünü incele and Örnek kontrol).
  The scripts are in the session scratchpad (`d_states.py`, `d_long.py`, `d_read*.py`, `d_paths.py`); they are not committed.
- Long-content cases are `L:` facts and `S:L<n>-...` shots, each at 100 and 150 percent, 1366x768 and 1920x1080 and in all three themes (120 shots): `L1` = `real300`
  (300 documents x 8 variables) with the inspector on an 78-character unbroken value, a 260-character note and the 59-character variable name; `L2` = a 120-character template
  name; `L3` = 52 columns; `L4` = nothing read yet with long variable names, and a long search query. Facts: `/tmp/claude-0/p4/degerler/long-facts.tsv`; the clipping tool's
  lines for those windows: `/tmp/claude-0/p4/degerler/long-clipping.txt` (4,308 lines: 3,189 "cell text cut after 3 lines" (by design, V-21), 921 "column not visible, scroll sideways" (F-degerler-10), 135 "card cut by the scroll edge" (F-degerler-02),
  42 job-name elisions (F-yukle-23 class), 12 clear-button lines (F-degerler-11), 9 template-picker elisions (F-degerler-19)).
- The 72 matrix files are in `/tmp/claude-0/p4/degerler/matrix/` (`tools/screenshots.py matrix --allow`: 72 images, **0 KIRPILMA**: the demo data hid every overflow below).
- Measured: `/tmp/claude-0/p4/degerler/measure.tsv` from `python tools/ui_measure.py --tab degerler` (3 themes x 2 sizes x 2 text sizes, default state only): 4,833 rows, 4,694 pass,
  76 fail, 63 skip. The 76 fails are AUD-HIT-02 36 (24 the two zoom buttons, 12 the search icon), AUD-HIT-01 12 and HIG-CTL-06 12 (the search icon), DEC-CON-01 4 (the word
  "Kontrol" in the Güven column, dark only, 6.15 to 1), DEC-FOC-01 6 (`titleBand/titleTabs`, the single-tab-run artefact B-041) and AUD-A11Y-01 6 (the side panel's scroll area has no
  name). The tool measures the default state only; hover, pressed and focus colours are not measured (GAP in those cells, the screenshots are the evidence).
- Keywalk: `keywalk.py --tab degerler` in 24 of 24 combinations (3 themes x 1366x768 and 1920x1080 x text 100, 115, 130, 150): no trap, nothing unnamed, work area reached.
- Screenshot numbers: 01 default, 02 to 04 selector hover, focus, selected, 05 to 07 search focus, text, no match, 08 to 10 picker hover, focus, open, 11 table, 12 row hover,
  13 pressed, 14 selected with the cell focused, 15 selected with the table unfocused, 16 to 19 header hover, sorted up, sorted down, edge hover, 20 and 21 editor with key hint and typed,
  22 and 23 inspector for an Emin and a Kontrol value, 24x/25x/26x hover/focus/pressed of Onayla (a), Elle yaz (t), Yeni kutu çiz (v), Sayfanın tamamı (w), zoom in (z), 27 page view,
  28 context menu, 29xx/30xx command bar hover and focus (xx = ok, ek, tu, or, so, se, ge, yi), 31 Tümünü incele, 32 and 33 Örnek kontrol, 34 panel hidden (F9), 35 status bar, 36 and 37 an unread
  variable, 38 and 39 Okunamadı, 40 nothing selected, 41 no job, 42 nothing read, 43 no templated document, 44 and 45 empty Kontrol gerekenler / İncelenmemiş views.
- In hc, a disabled control is drawn in `GrayText` (by design, DESIGN.md). Selection in hc is the cyan fill with black text; focus is the ring.
- The read flow (progress, cancel, errors) was shot at `/tmp/claude-0/p4/degerler/paths/rd-*.png` (25 files) with a fake OCR engine; see `degerler-paths.md`.
- One script artefact is worth naming: after the context-menu step the page view overlay was visible again in my first runs (the script reopened nothing). It did not reproduce
  in isolation (P-046, P-094 and the motion run close it correctly), so it is not a finding; the final shots hide it explicitly, and the three themes were re-shot.

| Element | default | hover | pressed | focused | selected | disabled | empty | loading | error | long text / many items |
|---|---|---|---|---|---|---|---|---|---|---|
| E-010..E-020 command bar buttons | S:01 | S:29xx | GAP: not shot for the bar (the path rows press them) | S:30xx | toggles: S:31, S:32 | S:29so, S:29yi (Sonraki kontrol and Yinele); no read yet: S:42 | n/a: no content | read button off while reading: P-138, `rd-001-start` | n/a: a button has no error state | n/a: icon buttons; at 150 % the bar moves to "Diğer komutlar" (matrix `degerler-*-1366x768-150`, 0 lines) |
| E-012 Değerleri oku (labelled) | S:01 | S:29ok | GAP: as above | S:30ok | n/a: not a toggle | disabled while reading: P-138 | disabled with no templated document: S:43 | P-137 | n/a | n/a: label fixed |
| E-030..E-036 progress and message band | n/a: hidden when idle | n/a | n/a | stop button focus: P-192 (reachable, position 7 of 16) | n/a | stop button hidden when idle | n/a | S:`rd-001-start`, `rd-002-progress`, P-137, P-141 | refused S:`rd-037-refused`; failed S:`rd-033-failed-band`; per document S:`rd-030-per-doc-errors` | RD-081/082: P-197 to P-202 (150 %, 1024x600): label and hint elided (F-degerler-28) |
| E-035 Okumayı durdur | n/a: hidden | GAP: not shot | GAP: not shot | P-192 | n/a | n/a | n/a | click gives no sign: S:`rd-cancel-button-clicked`, P-149 to P-154 (F-degerler-07) | n/a | n/a |
| E-041..E-045 view switch items | S:01 | S:02 (unselected), selected has no hover fill by design | GAP: not shot | S:03 | S:04 | n/a: no disabled state | counts 0: S:41, S:42 | n/a: counts are instant | n/a | L: counts 4 digits fit ("Tümü 2400", `real300`); GAP: 5-digit counts (no job with 10,000 values) |
| E-047 search field | S:01 | GAP: not shot | n/a: no pressed state | S:05 | text: S:06 | S:42 (grey, "Sicil No ara") | no match: S:07 | n/a | n/a | long query: S:L4-search-long-query, P-074 (5,000 characters, no hang); placeholder fits (E-047 `_fit_search_hint`) |
| E-048, E-049 search icon and clear button | S:06 (x shown) | GAP: not shot | GAP: not shot | n/a: NoFocus by design | n/a | n/a | n/a | n/a | n/a | M: AUD-HIT-01/02, HIG-CTL-06 on the icon; the clear button is 38 x 38 in a 32 px field: `states/dbg-search-100.png`, F-degerler-11 |
| E-050 template picker | S:01 | S:08 | GAP: not shot | S:09 | open: S:10 | n/a | "Şablon yok": S:41 | n/a | "Şablon bulunamadı": GAP: no job with a deleted template was built | L2: 120-character name: S:L2-header-long-template-name (918 px wide, cut without "…", search to line 2), `L:` combo_w 918 / hint 1,164 at 100 %, 630 / 1,740 at 150 % (F-degerler-19) |
| E-061..E-068 table header | S:11 | S:16 | GAP: not shot | n/a: no focus stop on the header | sorted: S:17, S:18 | n/a | S:42 (titles over the empty state) | n/a | n/a | long titles: elided with a tooltip: `L:` 3 of 8 titles at 100 %, 5 of 8 at 150 %; edge hover S:19; floor 40 px P-022; nothing-read state shows full titles cut by the card edge: S:L4-empty-not-read-long-names (F-degerler-21) |
| E-069..E-071 review mark, Belge, Sayfa cells | S:11 | S:12 | S:13 | n/a: cell focus is on value cells | S:14, S:15 | n/a: rows are never disabled | n/a | n/a | n/a | 4-digit Belge numbers fit (`real300`); GAP: 5-digit numbers |
| E-072 value cell Emin | S:11 | S:12 | S:13 | S:14 (ring) | S:14 | n/a | n/a | n/a | n/a | long: S:L1-table-default |
| E-073 value cell Orta | `real300` rows with 0.82 confidence: S:L1-table-default (looks like Emin) | n/a: as E-072 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | F-degerler-10: no mark in the cell |
| E-074 value cell Kontrol (marked characters) | S:11 | S:12 | S:13 | S:14, S:20 | S:14, S:15 | n/a | n/a | n/a | n/a | an 78-character unbroken flagged code: wraps by character, 3 lines, "…": S:L1-inspector-unbroken |
| E-075 value cell Okunamadı ("boş") | S:39 | S:39 hover not shot: GAP | GAP | S:38 | S:39 | n/a | n/a | n/a | S:38 (this is the error level) | S:L1-table-default |
| E-076 value cell Okunmadı | S:36 | GAP: not shot | GAP | S:37 | S:37 | inspector buttons: S:37 | n/a | n/a | failed document: S:`rd-031-error-inspector` (F-degerler-05) | n/a |
| E-077, E-078 text kinds and wrapped text | S:L1-table-default | n/a | n/a | S:L1-inspector-longnote | n/a | n/a | n/a | n/a | n/a | L1: 260-character note shows 3 lines + "…" (clipping lines P-126 to P-128, by design V-21); numbers in a mixed column wrap ("1005.250,7 / 5", `mixed60`) |
| E-079 Güven cell | S:11 | S:12 | n/a | n/a | S:14 | n/a | n/a | n/a | n/a | clipped after a saved sort plus an added variable ("Emin %9", "Okunam"): S:36, S:39 in all three themes, `states/dbg-added-variable-after-sort.png` (F-degerler-35); out of view from 6 variables at 1366 (`cols.tsv`, F-degerler-10) |
| E-084 horizontal scroll bar | n/a: absent at 2 to 5 variables at 1366 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | L: 8 variables 338 px of range at 100 %/1366; 3 variables at 150 %/1366: 154 px; 52 columns 4,731 px (S:L3-table-48-columns) |
| E-085, E-086 cell editor and key hint | n/a: closed | n/a | n/a | S:20 (caret, 2 px ring) | typed: S:21 | n/a | n/a | n/a | n/a | 3,000 characters accepted, row 77 px high: P-099; hint chip over the next row: S:20 |
| E-110..E-116 empty states | S:41, S:42, S:43, S:07, S:44, S:45 | buttons: GAP: not shot | GAP | button focus: P-072, P-194 | n/a | n/a | this is the empty state | n/a | n/a | L4: S:L4-empty-not-read-long-names (3 long variable names in the sentence); a 5,000-character query repeated in the sentence (P-074) |
| E-100..E-105 Örnek kontrol | S:32 | GAP | GAP | S:33 | S:33 | no Emin value: GAP (the demo always has one) | n/a | n/a | error found: P-108 toast | 20 rows with 300 documents: P-107 |
| E-120..E-129 side panel, source card | S:22 | zoom buttons S:24z | S:26z | S:25z | n/a | n/a | S:40 (blank well) | crop not yet rendered: GAP (the shots wait for the render) | n/a | long variable name: title cut at the panel edge, whole card stack wider than the panel: S:L1-inspector-unbroken-100-1366 (F-degerler-02); 59-character name with spaces too |
| E-130..E-134 value card | S:22, S:23 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | S:37 (okunmadı), S:38 (Okunamadı) | 260-character suggestion: block 384 px, panel scrolls: S:L1-inspector-longnote; 78-character code: S:L1-inspector-unbroken |
| E-135..E-137 inspector buttons | S:23 | S:24a, 24t, 24v | S:26a, 26t, 26v | S:25a, 25t, 25v | n/a | S:37, S:40 | n/a | n/a | n/a | n/a: labels fixed |
| E-053 splitter handle | S:01 | GAP: not shot | n/a | n/a: no focus (F-degerler-25) | n/a | F9 hides the panel: S:34 | n/a | n/a | n/a | P-123, P-124 (side 252 to 890 px) |
| E-140..E-143 page view | n/a: closed | n/a | n/a | S:27; focus return: P-046, P-094 | n/a | n/a | n/a | page render pending: GAP | n/a | n/a |
| E-154 context menu | S:28 | GAP: not shot | n/a | key hint per entry: P-012 | n/a | disabled entries: P-011 | n/a | n/a | n/a | n/a |
| E-160..E-167 status bar | S:35 | n/a | n/a | n/a | n/a | n/a | S:41 (nothing), S:42 ("12 belgede şablon var, değer okunmadı") | n/a | S:38 ("1 okunamadı") | `real300`: items 183 + 113 + 146 px at 100 %; "219 / 2400 incelendi" fits; GAP: counts of 5 digits |
| E-170..E-172 toasts | message example: S:31 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | error kind: `rd-111-after-errors` | text cut at ~560 px: S:31 ("...Enter sırada"), F-degerler-12 |

Gaps: 29 GAP entries (the command bar and selector pressed states, hover on the clear button, the search field, picker pressed, empty-state buttons, the splitter handle, the context menu and
Örnek rows; the crop and page loading frames; 5-digit counts; a job with a deleted template; an Örnek view without an Emin value). Tablets, touch and the real Windows high-contrast theme
were not tried.

Cells that point at a finding: F-degerler-02 (inspector, long name), 10 (Güven out of view), 11 (clear button), 12 (toast cut), 19 (long template name), 21 (header over the not-read state),
35 (Güven clipped after a saved sort), 05 and 07 (read states), 13 (column floor).
