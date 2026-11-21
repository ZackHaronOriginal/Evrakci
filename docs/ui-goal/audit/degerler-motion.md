# Değerler audit: motion

Phase 4, Görev A, screen Değerler. Every animation on the screen, found by reading `ui/motion.py` and grepping `degerler*.py`, `loupe.py` and `feedback.py` for `motion.`,
`QPropertyAnimation`, `QVariantAnimation`, timers and cursors, then measured with a script (session scratchpad `d_motion.py` and `d_shift.py`, offscreen, opacity sampled every 12 ms; output
`/tmp/claude-0/p4/degerler/motion.log`). The decision is D7: durations 0, 80, 120, 180 or 240 ms and nothing longer; reduced motion turns every duration into 0; repeated actions
(arrow keys, accept-next) must not animate. Both modes were measured: `motion.set_reduced_motion_override(False)` and `(True)`. The system value itself was not varied (no Windows).
Every animation that starts was counted by wrapping `QAbstractAnimation.start`; its target object was recorded.

After every run no animation object is left alive on the window (`QPropertyAnimation` children: 0), including during a read.

| ID | Element | Trigger | Duration and curve | Reduced motion | Blocks input? | Frequent action? | Finding |
|---|---|---|---|---|---|---|---|
| M-01 | Toast (E-170 to E-172), fade in | every toast: read finished (E-171), Seçilenleri onayla (E-172), error found in the sample, some navigation messages | 240 ms (SLOWER), enter curve (0, 0, 0, 1); opacity 0.42 at 60 ms, 0.79 at 98 ms, 1.0 at 251 ms (second run: 0.36 at 55 ms, 1.0 at 248 ms) | opacity 1.0 at 0 ms | no | yes: a toast followed 1 of 25 repeated navigation keys (Down x10, Tab x10, N x5) and 1 of 3 view switches in the run | F-degerler-27 |
| M-02 | Toast, dismiss | 6 s timer (10 s with Geri al), x button, a newer toast | none: `hide` and `deleteLater` at once | same | no | no | none |
| M-03 | Page view (loupe, E-140), fade in | Space, E-126, context menu, palette | 120 ms (NORMAL), enter curve; 0.55 at 76 ms, 0.91 at 90 ms, 1.0 at 138 to 143 ms | 1.0 at 0 ms | the overlay takes the keys once visible; the first 120 ms are already clickable | no: one press per page | none |
| M-04 | Page view, fade out | Esc, Kapat, Space again | 80 ms (FAST), exit curve (0.3, 0, 1, 1); 0.85 at 49 ms, 0.0 at 112 ms (the hide follows the animation) | hidden at 0 ms | no | no | none |
| M-05 | Page view: close then reopen within 30 ms | Esc then Space very fast | the fade-out's `finished -> hide` is still connected when the next `fade_in` starts: the loupe ends hidden after 400 ms (normal motion); with reduced motion it stays open (True) | n/a | yes: Space seems to do nothing | rare | F-degerler-26 |
| M-06 | Progress bar (E-033) | a read | determinate; no indeterminate stripe: 1 distinct frame in 360 ms while the value does not change (range 0..3); no animation object | same | no | no | none |
| M-07 | Busy cursor | a read | none: `QApplication.overrideCursor()` is None while a read runs and the table cursor is the arrow (the window stays usable, the band is the signal) | same | no | no | none |
| M-08 | View switch pill (E-046) | click or Left/Right on E-042 to E-045 | none: the pill and fill change at once (image right after the click equals the image 300 ms later) | same | no | yes | none |
| M-09 | Row selection, current cell, focus ring, hover fill (E-080 to E-082) | arrows, Tab, N, mouse | none: painted by the delegate in the same frame; 0 animations from 10 Down, 10 Tab and 5 N presses (the one animation counted is M-01) | same | no | yes | none |
| M-10 | Accept (Enter, Onayla) | Enter x4 | none: 0 animations for 4 accepts; the next value is selected at once | same | no | yes | none |
| M-11 | Cell editor and key hint (E-085, E-086) | F2, double click | none: the editor and the chip appear in the same frame (0 animations) | same | no | yes | none |
| M-12 | Table scrolling (wheel, scroll bars, `scrollTo`) | wheel, N, Tab | per-pixel scroll mode, no smooth-scroll animation; `scrollTo` jumps | same | no | yes | none |
| M-13 | Progress and message band (E-030) appears | a read starts or a refusal or failure message | none (no animation) but a **layout shift**: the card moves down 62 px (50 px band + 12 px gap) when the band shows and back up when it ends or is closed (`card before (90, 636)`, `while reading (152, 574)`, `after (90, 636)`) | same | no | once per read | F-degerler-36 |
| M-14 | Menus, context menu, template picker popup | right click, Alt+menu, click on E-050 | no animation of its own is set by the app; Qt's menu fade hint was not read from the application style | GAP: not read | no | yes (context menu) | none known |
| M-15 | Empty states, status bar items, side panel content swap | any state change | none: `show()/hide()` only | same | no | yes | none |
| M-16 | Splitter drag, panel hide (F9) | drag, F9 | none: the splitter moves with the pointer; F9 shows or hides the panel at once and the table recomputes its widths in the same pass | same | no | yes | none |
| M-17 | Taskbar progress (E-173), window alert (E-174) | a read | OS surfaces: `taskbar.set(done, total)` is called 15 times for 12 documents and `clear()` once at the end (stub); `QApplication.alert` at the end when the window is in the background. Not visible offscreen | not applicable (OS) | no | no | none |

Summary: 2 durations in use (240 ms toast, 120 and 80 ms loupe), all inside D7; with reduced motion every duration is 0 and no animation starts. One finding on a frequent action (the toast fade, M-01),
one race that leaves the page view hidden (M-05), one layout shift (M-13).
