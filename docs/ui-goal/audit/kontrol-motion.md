# Kontrol audit: motion

Phase 4, Görev A, screen Kontrol. Every animation on the screen, found by reading `ui/motion.py` and grepping the Kontrol files
for `motion.`, `QPropertyAnimation`, `QVariantAnimation` and timers, then measured with a script (session scratchpad `motion.py`,
offscreen, opacity sampled every 15 ms). The decision is D7: durations 0, 80, 120, 180 or 240 ms and nothing longer; reduced motion
turns every duration into 0; repeated actions (arrow keys, accept-next) must not animate (`ui/motion.py` header).

Reduced motion was measured: `set_reduced_motion_override(True)` gives `duration(NORMAL)` = 0 and `duration(SLOWER)` = 0; with it the loupe
is visible at opacity 1.0 the moment Space is pressed and hidden the moment Esc is pressed. With the override off the system setting
decides (`system_reduced_motion`); the OS value itself was not varied (no Windows).

After every run no animation object is left alive on the window (`QPropertyAnimation` children: 0), so nothing keeps running while idle.

| ID | Animation | Duration | Curve | Trigger | Reduced motion | Blocks input? | Frequent action? | Finding |
|---|---|---|---|---|---|---|---|---|
| A-01 | Loupe opens: opacity 0 to 1 | 120 ms (NORMAL) | `enter` cubic-bezier(0, 0, 0, 1) | Space, double click on a page, command bar "Sayfayı büyük göster", menu Önizle, context menu Önizle; `loupe.py:open (L475)` | 0 ms, instant (measured) | No: Right pressed during the fade moved the page (row 1 to 2). Measured opacity: 0.0 at 88 ms, 0.55 at 142 ms, 0.96 at 162 ms, 1.0 at 208 ms | Yes: Space is how pages are looked at in the primary journey (open job, check a document: arrows, N, Enter; Space is the peek) | F-kontrol-12 |
| A-02 | Loupe closes: opacity 1 to 0, then hidden | 80 ms (FAST) | `exit` cubic-bezier(0.3, 0, 1, 1) | Space, Esc, Kapat button; `loupe.py:close_loupe (L532)` | 0 ms, instant (measured) | No, but for 80 ms the loupe still counts as open (`is_open()` is `isVisible()`), so a Space pressed in that time closes again instead of opening (open, Esc, Space 10 ms later: ended hidden) | Yes, same as A-01 | F-kontrol-12 |
| A-03 | Toast appears: opacity 0 to 1 | 240 ms (SLOWER, the maximum) | `enter` | every delete, merge, "Kontrol gereken tek belge bu." and the other toasts; `feedback.py:Toaster._next (L232)` | 0 ms | No (toast does not take focus; it can cover the inspector buttons, F-kontrol-07) | Yes for delete (Del is a repeated action while cleaning up a batch) and merge | F-kontrol-13 |
| A-04 | Toast leaves (6 s timer, close X, Geri al) | none: `hide()` and `deleteLater()` at once | n/a | `Toaster.dismiss` | n/a | No | n/a | none (instant is right) |
| A-05 | Thumbnail re-render after zoom | not an animation: a 150 ms single-shot timer (`kontrol.py:THUMB_DELAY_MS`) then new thumbnails replace the scaled old ones | n/a | slider, Ctrl+wheel, Ctrl+plus/minus | n/a | No | the tiles scale at once and sharpen 150 ms later | none |
| A-06 | Scrolling to the current page | none: `scrollTo` jumps (End on 15 pages scrolled to 290 of 307 px at once); `ScrollPerPixel` | n/a | arrow keys, N, U, Ctrl+Left/Right, Ctrl+G, overview click | style hint `SH_Widget_Animation_Duration` returns 0 when reduced (`style.py:198`) | No | no animation: correct for repeated actions | none |
| A-07 | Selection ring, focus ring, deleted dimming, hover | none: painted at once | n/a | any | n/a | No | no animation | none (and no hover state at all: F-kontrol-11) |
| A-08 | Overview ring over the documents in view | none: moves at once | n/a | scrolling | n/a | No | | none |
| A-09 | Rubber band | none: follows the pointer | n/a | drag | n/a | No | | none |
| A-10 | Inspector card scroller (hairline, reveal of a focused card) | none found: `card_scroll.py` uses a timer and `scrollTo`, no animation object | n/a | Tab into a card | n/a | No | | none |
| A-11 | Menus (context, overflow, template) and tooltips | Qt's own style animation, reduced with the same style hint | style default | open menu | follows the style hint | No | | none |
| A-12 | Busy cursor for long work | `motion.busy_cursor` exists (100 ms delay); Kontrol never calls it | n/a | a large edit (every edit serialises the job twice and rebuilds the model, O-16) | n/a | n/a | an edit on a big job shows no busy feedback | not a motion finding; see O-16 and perf notes |

## Result

Two motions sit on frequent actions (A-01 and A-02 on Space, A-03 on delete and merge), which the motion decision forbids; both
are inside the allowed durations and both honour reduced motion, so they are S4. A-02 also has a small input defect (the Space
pressed during the 80 ms fade-out is lost), recorded in F-kontrol-12. No animation blocks input, none runs while idle, none
exceeds 240 ms, and none is needed for arrow-key movement, selection, approval or cut/rotate, which is correct.

Not checked: the OS "reduce motion" setting on Windows, the title band and menu animations (shared chrome), any animation
inside Qt's native dialogs (Filtre, Git).
