# Rehber audit: motion

Phase 4, Görev A, screen Rehber. Every animation on the screen: duration, curve, trigger, reduced motion, whether it blocks input. Measured by sampling the toast's opacity every 10 ms offscreen and by counting `QAbstractAnimation` children of the window before and after each action (`m1.py` and `m2.py` in the session scratchpad). `rehber.py`, `rehber_parts.py`, `rehber_reader.py`, `rehber_content.py` and `rehber_print.py` contain no animation and no `motion.` call (`grep -n "motion\.\|QPropertyAnimation\|QVariantAnimation" src/evrakci/ui/rehber*.py` finds nothing); the only motion a person sees on this tab is shared chrome.

| ID | Element | Trigger | Duration and curve | Reduced motion | Blocks input? | Frequent action? | Finding |
|---|---|---|---|---|---|---|---|
| M-01 | Toast (E-064 to E-066), fade in | after printing, a print failure, a PDF failure | 240 ms (SLOWER), enter curve (0, 0, 0, 1); opacity 0.00 at 0 ms, 0.69 at 72 ms, 0.88 at 127 ms, 0.96 at 176 ms, 1.00 at 225 ms | opacity 1.00 at 3 ms (override on) | no | no: one toast per print or failure | none (same widget as F-kontrol-13, which is about toasts after every delete; printing is rare) |
| M-02 | Toast, dismiss | 6 s timer, x button, the next toast | none: hidden at once | same | no | no | none |
| M-03 | Stepping through hits (F3, Shift+F3, Enter, chevrons) and the reveal of the hit | every step | none: the current mark is repainted and the bar set at once; 0 new animation objects after 5 steps | same | no | yes (held key repeat) | none (no motion on a frequent action) |
| M-04 | Scrolling the guide (wheel, PgUp/PgDn, Home/End, arrows, contents click, section jump) | every scroll | none: no smooth scroll; PgDn moves one page (622 px) in the same frame; `go_to_section` 0 ms | same | no | yes | none |
| M-05 | Zoom (Ctrl+wheel, Ctrl+plus/minus, slider, buttons) | every zoom step | none: the guide is laid out again, 17 ms at 100 % and 16 ms at 300 % on the demo guide (`m2.py`); no animation object | same | no (the window repaints after the layout, 17 ms) | yes (wheel steps) | none |
| M-06 | Guide to "no result" card and back | a search without hits, Esc | none: a `QStackedLayout` switch, 4 ms | same | no | yes (typing) | none |
| M-07 | Typing in the search field | every key | the hits are painted as extra selections: 8 ms for a 6-character term; the result line is announced to screen readers 500 ms after the last change (a timer, not an animation) | same | no | yes | none |
| M-08 | Side panel hide and show (F9) | F9 | none: 3 ms | same | no | no | none |
| M-09 | Hover and pressed fills (buttons, contents rows, search field) | pointer | none of our code; the style paints the state at once (the primary button: fill 63,90,76 -> 52,73,62 in the next frame) | same | no | yes | none |
| M-10 | Focus ring (D11) | keyboard focus | no animation of this screen's code; shared chrome; one `QAbstractAnimation` child can exist in the window after a toast (`animations 1` after the first toast, 0 at rest) | same | no | yes | none |
| M-11 | Scroll bar widening on hover (DESIGN.md: 9 px, wider on hover) | pointer | style-drawn, not measured: GAP | n/a | no | yes | GAP: not measured offscreen |
| M-12 | Caret blink in the search field | focus in the field | system flash time 1,000 ms (`QApplication.cursorFlashTime()`); follows the system, not the app's reduced-motion override | system setting | no | n/a | none |
| M-13 | Printing 200 sheets (400 pages) to a PDF printer | Yazdır | no animation and no busy cursor; the GUI thread is busy for 0.7 s (P-162); on a real printer the spooler time was not measured | n/a | yes: the window does not repaint during the print call | no | none (a real printer was not available; if the spool takes seconds the window freezes without a word: not decidable offscreen) |
| M-14 | Taskbar and busy cursor | none on this tab | none | n/a | no | no | none |

After every run no animation object of this screen is left alive. For the reader with weak eyesight: the guide, the contents list and the hit marks change in the next frame, so there is no motion to lose or to turn off; the only fade is the 240 ms toast, which turns to 3 ms with reduced motion. Rows: 14, findings: 0.
