# Yükle audit: motion

Phase 4, Görev A, screen Yükle. Every animation on the screen, found by reading `ui/motion.py` and grepping the Yükle files, `feedback.py`, `style.py` and the
window for `motion.`, `QPropertyAnimation`, `QVariantAnimation`, timers and cursors, then measured with a script (session scratchpad `motion.py`, offscreen,
opacity and pixels sampled every 15 to 60 ms; output `/tmp/claude-0/p4/yukle/motion.txt`). The decision is D7: durations 0, 80, 120, 180 or 240 ms and
nothing longer; reduced motion turns every duration into 0; repeated actions (arrow keys, accept-next) must not animate. Both modes were measured:
`motion.set_reduced_motion_override(False)` and `(True)`. The system value itself was not varied (no Windows).

After every run no animation object is left alive on the window (`QPropertyAnimation` children: 0), and hovering and clicking batch rows created none.

| ID | Element | Trigger | Duration and curve | Reduced motion | Blocks input? | Frequent action? | Finding |
|---|---|---|---|---|---|---|---|
| M-01 | Toast fade-in (E-113) | every `_tell`: add, remove, queue, cancel, refusal | 240 ms (SLOWER), enter curve (0,0,0,1); opacity 0.46 at 60 ms, 1.0 at 232 ms | 0 ms: opacity 1.0 at once (measured) | no (the toast never takes focus) | yes: Del and every add | F-yukle-28 |
| M-02 | Toast dismissal (E-113) | timeout (6 s, 10 s with Geri al), X, next toast | none: `hide()` at once | same | no | n/a | none |
| M-03 | Indeterminate progress bar (E-054, "Dosyalar inceleniyor: N") | start of every read, until the pages are counted | Qt style loop, about 8 distinct frames in 480 ms, no token | **keeps moving** (8 distinct frames with the override on) | no | no (once per read) | F-yukle-29 |
| M-04 | Determinate progress bar (E-054) | every progress report | none: `setValue`; redraw at most every 0.1 s (`REPORT_EVERY`) | same | no | n/a | none |
| M-05 | Busy cursor over the screen (E-122) | read starts to read ends | immediate set and unset, no 100 ms delay (`motion.BUSY_DELAY_MS`) | same | no (the window stays usable) | no | F-yukle-30 |
| M-06 | Spinner icons (loader-circle in Okunuyor cells, status bar, inspector) | while reading | static pixmap, no rotation | same | no | n/a | none (the state is also a word) |
| M-07 | Drop overlay (E-106) | files dragged over the window | appears and disappears at once (no effect, no animation); dashed edge static | same | no (mouse-transparent) | no | none |
| M-08 | Error bar (E-059) | a failed read, the next read, the X | none: the widget is inserted; the table below jumps down 70 px (144 to 214) | same | no | no | F-yukle-24 (layout shift, not motion) |
| M-09 | Row selection, hover, pressed, focus ring (E-027) | pointer and keys | none (0 animation objects after hover and click) | same | no | yes (arrows) | none: correct |
| M-10 | Header and splitter resize (E-028, E-049) | drag | follows the pointer, no easing | same | no | n/a | none |
| M-11 | Table scroll | wheel, scroll bar | `ScrollPerPixel`, no smooth-scroll animation | same | no | yes | none |
| M-12 | Qt menus and tooltips (E-063, E-085 to E-091) | open | Qt style; `style.py (L198)` returns 0 for `SH_Widget_Animation_Duration` under reduced motion | follows the override | no | no | not measured offscreen (GAP) |
| M-13 | Taskbar flash at the end of a read (E-121) | read ends while the window is not active | OS | OS | no | no | Windows only (GAP) |

Summary: 13 rows, 3 findings (M-01, M-03, M-05) and one layout shift (M-08). Nothing on Yükle moves while idle. The toast is the only token-driven animation and it
answers every frequent key; the indeterminate bar is the only motion that ignores the reduced-motion setting.
