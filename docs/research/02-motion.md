# 02 - Motion design for Evrakçı

**Access note.** The session network blocked m3.material.io, nngroup.com, carbondesignsystem.com, learn.microsoft.com and developer.apple.com (DNS failure). Only one web search worked, and it returned third-party mirrors of the Material tokens. Most figures below therefore come from the author's recall of the published specs. They are marked **(recall)** where the exact page was not re-opened this session. Anything not known with confidence is marked **(unverified)**. Re-verify every **(recall)** value against the primary page before it goes into the final goal prompt. Source list at the end gives the canonical URLs; none were accessed live (date of attempt: 2026-11-12).

## TL;DR

- Under ~100 ms feels instantaneous; ~1 s keeps flow of thought; ~10 s is the limit of attention (Nielsen response-time limits) [1]. Motion in a productivity tool should sit mostly in the 100-250 ms band; NN/g puts useful UI animation at roughly 100-500 ms [2] (recall).
- Every big design system converges on the same shape: short durations (50-250 ms) for small, frequent UI; longer (300-500 ms) only for large or full-screen changes; "enter = decelerate, exit = accelerate"; long-tail "emphasized" curves reserved for hero moments.
- Material 3 tokens: standard `cubic-bezier(0.2, 0, 0, 1)`, durations short1 50 ms through extra-long4 1000 ms [3] (recall).
- Carbon splits motion into **productive** (fast, quiet, task UI) and **expressive** (editorial/moments); productive is the right register for Evrakçı [4] (recall).
- Fluent 2 gives named durations (ultra-fast 50 ms to ultra-slow 500 ms) and the Windows feel Evrakçı's users already know [5] (recall).
- Apple's guidance: motion must be purposeful, interruptible, and respond to gesture velocity; springs are the default in SwiftUI (`.smooth` has zero bounce) [6][7] (recall).
- Accessibility: honour the OS reduced-motion setting (WCAG 2.3.3 AAA; WCAG 2.2.2 for anything auto-moving longer than 5 s) [8]. Vestibular triggers are large-area parallax, zoom and sliding, not short fades.
- For a keyboard-heavy tool: never make the user wait on an animation; input must be accepted mid-animation; repeated actions (arrow-key navigation) get no transition or <=80 ms.
- Qt can do all of this with `QVariantAnimation` + `QEasingCurve.BezierSpline`; prefer animating properties that repaint small regions, avoid `QGraphicsOpacityEffect` on large/live widgets.
- Recommendation: 6 duration tokens (0, 80, 120, 180, 240, 320 ms), 4 curves, one reduced-motion switch that collapses all durations to 0 and keeps only an instant colour/opacity change.

## 1. Apple

### 1.1 HIG Motion principles (recall)
Apple's Human Interface Guidelines "Motion" page [6] says motion should be purposeful (communicate status, give feedback, help people visualise results), not decorative; should be optional (do not make it the only way to convey information); and should honour Reduce Motion by replacing large movement with crossfades/dissolves. Apple also says to keep feedback animations brief and precise, so they do not slow people down in frequent interactions. No numeric durations are published in the HIG itself (unverified: some platform pages cite ~0.25-0.35 s for system transitions, but this is not an official token).

### 1.2 Spring parameters (SwiftUI; WWDC23 "Animate with springs") [7] (recall)
Springs are described with two perceptual parameters instead of mass/stiffness/damping:
- **duration** (perceptual, ~ time to settle toward target; default 0.5 s) and **bounce** (-1..1; 0 = no overshoot).
- Presets: `.smooth` bounce 0 (no overshoot), `.snappy` bounce 0.15 (small overshoot), `.bouncy` bounce 0.3. `.smooth` is the SwiftUI default.
- The older API: `spring(response:dampingFraction:)`. `response` is the period of the undamped spring (about the settle time scale, default 0.55 s); `dampingFraction` 1.0 = critically damped (no overshoot), <1 overshoots. `bounce` relates to damping as roughly `dampingFraction = 1 - bounce` for positive bounce (recall; the exact mapping is approximate).
- Springs preserve velocity when retargeted (interruption) and are not defined by a fixed duration, so a gesture release or a second tap simply starts a new spring from the current position AND velocity. This is the core argument for springs over fixed-duration curves.

### 1.3 "Designing Fluid Interfaces" (WWDC18) [9] (recall)
Key claims: (a) response must be immediate, i.e. react on touch-down, not after the gesture ends; (b) interfaces should be **interruptible and redirectable**, so the user never waits for an animation to end before acting; (c) **velocity continuity**: a gesture's release velocity feeds the following animation; (d) motion should follow a "spatial model", so things return where they came from; (e) use **critically damped** springs (no bounce) for most UI, adding bounce only when the gesture itself has momentum. The talk says "fluid" feel comes from continuous, interruptible behaviour rather than from particular durations.

### 1.4 Reduce Motion
macOS/iOS expose "Reduce motion" (`NSWorkspace.shared.accessibilityDisplayShouldReduceMotion`, `UIAccessibility.isReduceMotionEnabled`, SwiftUI `@Environment(\.accessibilityReduceMotion)`). Apple's own pattern: slides/zooms become cross-dissolves, not nothing.

## 2. Google Material 3 [3] (recall)

### 2.1 Easing tokens
| Token | cubic-bezier | Use |
|---|---|---|
| standard | (0.2, 0, 0, 1) | on-screen to on-screen, small utility |
| standard-decelerate | (0, 0, 0, 1) | entering |
| standard-accelerate | (0.3, 0, 1, 1) | exiting |
| emphasized-decelerate | (0.05, 0.7, 0.1, 1) | large entering |
| emphasized-accelerate | (0.3, 0, 0.8, 0.15) | large exiting |
| emphasized | a two-segment path curve (not a single bezier) | hero transitions |

The search mirrors listed emphasized-decelerate/accelerate as above and show that third-party tables disagree on naming for `(0.2, 0, 0, 1)`, so verify against the official page.

### 2.2 Duration tokens (ms)
short1 50, short2 100, short3 150, short4 200; medium1 250, medium2 300, medium3 350, medium4 400; long1 450, long2 500, long3 550, long4 600; extra-long1 700, extra-long2 800, extra-long3 900, extra-long4 1000. Confirmed endpoints (50 and 1000) via search mirrors; the middle steps follow the 50 ms ladder (recall).

### 2.3 Transition patterns
- **Container transform**: an element expands into its detail view (continuity of a persistent container). ~300-500 ms.
- **Shared axis** (x, y, z): sibling navigation, where the outgoing and incoming slide a short distance (30 dp) with fade; ~300 ms total.
- **Fade through**: unrelated destinations (e.g. bottom-nav tabs): outgoing fades out (~90 ms), incoming fades in with slight scale (from 92 %) over ~210 ms, so ~300 ms total.
- **Fade**: for elements appearing/disappearing in place (menus, dialogs, ~150 ms in / 75 ms out, recall).
For Evrakçı's six tabs, the best fit is **fade through** with no scale, or a plain crossfade.

## 3. Microsoft Fluent 2 / Windows [5] (recall)
Fluent 2 durations: ultra-fast 50, faster 100, fast 150, normal 200, gentle 250, slow 300, slower 400, ultra-slow 500 ms. Curves: decelerate-max `(0,0,0,1)`, decelerate-mid `(0.1,0.9,0.2,1)`, decelerate-min `(0.33,0,0.1,1)`, accelerate-max `(1,0,1,1)`, accelerate-mid `(0.9,0.1,1,0.2)`, accelerate-min `(0.8,0,0.78,1)`, easy-ease `(0.33,0,0.67,1)`, easy-ease-max `(0.8,0,0.2,1)`. Principles: motion is "purposeful", should feel natural and be quick; entering elements decelerate, exiting accelerate, and users can switch off animations. Windows (WinUI) "connected animation" is the shared-element transition (an element visually travels between two views, ~300 ms) [10]; it is intended for navigation drill-in, which Evrakçı mostly does not need. Windows system fast-fade for controls is ~83-167 ms (unverified numbers; common in WinUI 3 theme resources, e.g. `ControlFastAnimationDuration` 0.167 s, `ControlNormalAnimationDuration` 0.250 s, recall).

## 4. IBM Carbon [4] (recall)
Curves (productive): standard `(0.2, 0, 0.38, 0.9)`, entrance `(0, 0, 0.38, 0.9)`, exit `(0.2, 0, 1, 0.9)`. Expressive: standard `(0.4, 0.14, 0.3, 1)`, entrance `(0, 0, 0.3, 1)`, exit `(0.4, 0.14, 1, 1)`.
Durations: fast-01 70 ms, fast-02 110 ms, moderate-01 150 ms, moderate-02 240 ms, slow-01 400 ms, slow-02 700 ms. Guidance: productive for "task-focused, getting-things-done" UI; expressive for "important moments, editorial". Fast durations for small elements (buttons, toggles, checkboxes), moderate for modals/dropdowns, slow for large movement.

## 5. Others
- **Atlassian** publishes motion tokens and an "applying motion" page [11]: durations around 100 / 200 / 350 ms-class "fast/medium/slow" tiers (unverified exact values) and a rule to limit motion on frequently repeated actions.
- **Shopify Polaris**: motion tokens `motion-duration-0`..`-500` in 50 ms steps and `motion-ease`, `-ease-in`, `-ease-out`, `-linear` (recall, unverified exact curves).
- **GitHub Primer**: guidance that motion is functional; timing tokens (`--base-duration-100..` etc.) exist but exact set unverified [12].
Cross-check consensus: none of these use durations over 500 ms for ordinary UI.

## 6. Research on motion and usability
- **Response-time limits (Nielsen, 1993; NN/g)** [1]: 0.1 s = feels instantaneous; 1.0 s = flow of thought is uninterrupted though the user notices the delay; 10 s = limit of keeping attention. Animation that stretches an interaction beyond ~100 ms must justify itself.
- **NN/g "Executing UX Animations: Duration and Motion Characteristics"** [2] (recall): UI animations should be 100-500 ms; under 100 ms is not perceived as animation, over 500 ms feels slow for interface elements. Smaller objects and shorter distances need less time; larger/full-screen changes need more; mobile ~ 200-300 ms, desktop should be somewhat faster (about 150 ms-class, recall) because of the mouse/keyboard speed expectations. Recommends ease-out for entrances, ease-in for exits, and avoiding linear motion.
- **Benefits of motion** (NN/g "The Role of Animation and Motion in UX") [13] (recall): spatial continuity (where did it come from/go), feedback that an input was received, state change visibility, attention direction, and perceived performance. Harms: delays repeated tasks, distracts on dense screens, causes motion sickness.
- **Productivity-tool corollary**: with 1h+ sessions, any decorative animation is repaid hundreds of times a day. Animation of 200 ms on an action done 2,000 times per session costs ~6.7 minutes of cumulative waiting if it blocks input (arithmetic, not a citation). Hence non-blocking, skippable motion.
- **Vestibular disorders / motion sensitivity**: triggers are large-field motion, parallax, zoom/scale, spinning, scroll-jacking [14] (recall: WebAIM, web.dev and A11y Project). Small opacity/colour changes are safe.
- **WCAG**: 2.3.3 Animation from Interactions (AAA): motion animation triggered by interaction can be disabled unless essential [8]; 2.2.2 Pause, Stop, Hide (A): auto-starting motion lasting >5 s needs a control; 2.3.1 Three Flashes (A). CSS `prefers-reduced-motion` is the web expression of the OS setting [15].

## 7. Recommended motion tokens for Evrakçı

Principle: calm, fast, instrumental. Motion explains where something went and confirms an action; it never gates the next input.

### 7.1 Durations
| Token | ms | Use |
|---|---|---|
| `motion.none` | 0 | arrow-key selection move, hover on dense rows, any repeated-key action, reduced-motion |
| `motion.instant` | 80 | press/active feedback, checkbox/toggle, focus ring appear |
| `motion.fast` | 120 | hover colour, button state, tooltip fade-in, row highlight flash on accept |
| `motion.base` | 180 | menus/popovers/dropdowns, toast appear, inline editor open, banner reveal |
| `motion.moderate` | 240 | panel/drawer slide (<= 24 px travel), tab content crossfade, dialog enter |
| `motion.slow` | 320 | rare, large changes: first-run, wizard step, progress completion |
Exits are 70-75 % of the matching enter (e.g. 180 in, 130 out). Hard ceiling 400 ms; nothing in the tool exceeds it except indeterminate progress which is looped and not motion-heavy.

### 7.2 Curves (cubic-bezier x1,y1,x2,y2)
| Token | Value | Use |
|---|---|---|
| `ease.standard` | (0.2, 0, 0, 1) | default state changes, moves (M3 standard) |
| `ease.enter` | (0, 0, 0, 1) | things appearing (M3/Fluent decelerate-max) |
| `ease.exit` | (0.3, 0, 1, 1) | things leaving (M3 standard-accelerate) |
| `ease.linear` | (0, 0, 1, 1) | only for progress bars/spinners/opacity-only micro fades |
No emphasized or bouncy curve; overshoot is excluded (document-checking context, users must trust that things are stable).

### 7.3 Interaction map
| Interaction | Token / curve |
|---|---|
| Tab switch (Yükle...Rehber) | crossfade, `moderate` 240 (or 180) ms, `standard`; no slide; tab indicator underline moves 180 ms `standard` |
| Thumbnail timeline selection (arrow keys) | none; selection ring appears at once; scroll-into-view 120 ms `enter` only if target was off-screen |
| Thumbnail timeline scrolling | native/inertial, no custom animation |
| Add/remove a cut line | 120 ms fade + 2 px nudge; undo/redo replays same in reverse, but coalesced if repeated rapidly |
| Row accept (Değerler) | 120 ms background flash to success tone then settle; row stays in place |
| Hover on buttons/rows | `fast` 120 ms colour only |
| Press | `instant` 80 ms |
| Focus ring | `instant` 80 ms, or immediate; must remain visible (never animate away) |
| Dialog/popover | 180 ms enter (`enter`), 130 ms exit (`exit`), opacity + <= 8 px translate |
| Toast / banner | 180 ms enter; auto-dismiss exit 130 ms |
| Progress (OCR, export) | determinate bar width eases 120 ms `standard` between updates; indeterminate uses 1.2 s linear loop of small element; under reduced motion becomes static text + percent |
| Error / validation | colour change 120 ms plus icon + text; no shake |
| Drag of boxes (template editor) | no easing while dragging (1:1 with pointer); on release snap 120 ms `enter` |
| Large destructive action completion | 240 ms fade only |

## 8. Rules we should adopt for Evrakçı
1. No animation may delay input handling: every animation is non-blocking and the next keypress/click is processed immediately and retargets the running animation (interruptible, as Apple's fluid interface principle [9]).
2. Maximum duration for any UI transition is 320 ms; default interaction transitions are 80-240 ms. Test: grep for any animation duration constant > 320 ms outside indeterminate progress.
3. Repeated keyboard actions (arrow navigation, accept-next, undo/redo bursts) use `motion.none` or at most 80 ms; a held key must never queue animations.
4. Use only the four curves in 7.2; entering elements use `ease.enter`, leaving use `ease.exit`, moves use `ease.standard`. No overshoot/bounce anywhere.
5. Animate only opacity, colour and short translations (<= 24 px). No scale or zoom for panels, no parallax, no full-window slides, no auto-rotating or looping decorative motion.
6. Exit duration = ~70-75 % of enter duration.
7. A single app-level `reduced_motion` flag, initialised from the OS and overridable in settings; when on, all durations resolve to 0 (state changes still happen, as instant colour/opacity swaps) and progress indicators become static.
8. State must never be conveyed by motion alone: every animated change (accept, error, cut added) also leaves a persistent visible state (icon, text, colour with contrast per the colour research file).
9. Looping animation (spinner, indeterminate bar) must be small (< ~32 px area), and stop when the window is inactive; anything auto-playing for >5 s needs a pause path or must be non-essential (WCAG 2.2.2 [8]).
10. Motion tokens live in one module (`motion.py`) and widgets never hardcode a duration; every animated widget goes through a helper that applies the reduced-motion flag.
11. Never flash: no change of luminance more than 3 times in any second (WCAG 2.3.1 [8]).
12. Success/accept highlights fade out in <= 400 ms total and must not repeat; the screen should be visually still while the user reads.

## 9. Qt / PySide6 feasibility notes

**Animation classes.** `QPropertyAnimation` animates any `Q_PROPERTY` (in PySide6 use `@Property(type, fget, fset)`) and is the simplest route for `pos`, `geometry`, `windowOpacity`, `maximumHeight`. `QVariantAnimation` gives a raw `valueChanged` signal and works for custom-painted widgets: store the animated value in a member (hover progress 0..1) and call `update()` (or `update(rect)`) in the slot. `QParallelAnimationGroup` / `QSequentialAnimationGroup` compose them. Set `setDuration(ms)` and `setEasingCurve(...)`; retargeting a running animation is done by `stop()`, `setStartValue(current)`, `setEndValue(new)`, `start()`, which gives interruptibility (no velocity carry-over; Qt has no built-in spring; a spring would need a custom timer-based integrator, e.g. QTimer at 16 ms).

**Custom cubic-bezier.** `QEasingCurve(QEasingCurve.BezierSpline)` then `curve.addCubicBezierSegment(QPointF(x1, y1), QPointF(x2, y2), QPointF(1, 1))`. This maps exactly to CSS `cubic-bezier(x1,y1,x2,y2)` because the spline starts at (0,0). Example for `ease.standard`: `c.addCubicBezierSegment(QPointF(0.2,0), QPointF(0,1), QPointF(1,1))`. Qt also has built-in `OutCubic` and `OutQuint` which are close to decelerate-max (approximation only). Verify with a unit test comparing sampled `valueForProgress` to an independent bezier solver (Qt's docs describe BezierSpline [16]).

**QGraphicsOpacityEffect costs.** It renders the widget (and children) into an offscreen pixmap each frame, which defeats native acceleration, can blur text on non-integer device pixels, and interacts badly with other effects and with child widgets that also repaint (e.g. a thumbnail grid). It also forbids using the effect on a widget which has an effect on an ancestor (undefined). Use it only for small, short-lived widgets (toast, popover, ~180 ms). For large views (the thumbnail timeline, tables) avoid it: crossfade by painting two cached `QPixmap` snapshots with `painter.setOpacity()` in a dedicated overlay widget, or just swap instantly. For top-level windows/popups `setWindowOpacity` is cheaper (needs compositing; works on Windows/macOS, depends on compositor on Linux/X11).

**Custom-painted widgets.** Drive a float "progress" with a `QVariantAnimation`; in `paintEvent` interpolate colours with `QColor` lerp (in linear light if possible, otherwise just sRGB). Call `update(rect)` on the dirty region only, and never run more than one frame timer (Qt default animation timer ~16 ms, i.e. ~60 fps; fine on office PCs). For `QStyleSheet`-styled widgets, stylesheet properties cannot be animated by Qt natively (no transitions); animate a custom property and repaint, or switch to a `QPalette`/custom paint approach for hover colours. Avoid animating `geometry` of items inside layouts (it forces relayout every frame); animate `maximumHeight` sparingly or use an overlay. For `QGraphicsView`/`QGraphicsItem` thumbnails, use `QGraphicsObject` properties and `ItemCoordinateCache` where items are static.

**Honouring reduced motion.**
- **Windows**: `SystemParametersInfoW(SPI_GETCLIENTAREAANIMATION = 0x1042, 0, &BOOL, 0)` returns FALSE when "Show animations in Windows" is off (Settings > Accessibility > Visual effects > Animation effects) [17]. In PySide6 call via `ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(b), 0)` with `b = ctypes.c_int()`. Re-read on `WM_SETTINGCHANGE` (override `nativeEvent` or an `QAbstractNativeEventFilter`) so the app follows live changes. `UISettings.AnimationsEnabled` (WinRT) is an alternative (unverified in PySide).
- **macOS**: `NSWorkspace.sharedWorkspace().accessibilityDisplayShouldReduceMotion()` via PyObjC; observe `NSWorkspaceAccessibilityDisplayOptionsDidChangeNotification` for live updates (recall).
- **Linux**: GNOME `org.gnome.desktop.interface enable-animations` (gsettings) / GTK `gtk-enable-animations`; KDE has "Animation speed" in `kdeglobals` (`AnimationDurationFactor`, 0 = off) (recall). Fall back to the in-app setting.
- Qt itself: no cross-platform reduced-motion property in `QStyleHints` is known to the author (unverified for Qt 6.8+; check `QStyleHints` docs). Do not rely on it; implement a small `platform_prefs.reduced_motion()` plus an app setting "Animations: System / On / Off" and a global factor in the helper that makes `duration = 0 if reduced else token`.
- When reduced, still emit the final state immediately (call `setEndValue` then `setCurrentTime(duration)` or skip animation and set the value).

**Testing.** Add a headless test that every `QAbstractAnimation` created through the helper has `duration() == 0` when the flag is on; and a manual test at 1366x768 on a low-end PC to confirm there are no dropped frames at the 240 ms transitions.

## Sources (accessed 2026-11-12 unless noted; most primary pages could not be reached, see top)
1. Nielsen, Response Times: The 3 Important Limits - https://www.nngroup.com/articles/response-times-3-important-limits/ (not re-fetched; widely known)
2. NN/g, Executing UX Animations: Duration and Motion Characteristics - https://www.nngroup.com/articles/animation-duration/ (not fetched; recall)
3. Material 3, Easing and duration tokens - https://m3.material.io/styles/motion/easing-and-duration/tokens-specs (not fetched; endpoints partially cross-checked via search mirrors, e.g. https://camoa.github.io/dev-guides/css/css-craft/motion-design-tokens and https://docs.rs/crate/bevy_material_ui/latest/source/src/motion.rs)
4. IBM Carbon, Motion - https://carbondesignsystem.com/elements/motion/overview/ (not fetched; recall)
5. Fluent 2, Motion - https://fluent2.microsoft.design/motion (not fetched; recall)
6. Apple HIG, Motion - https://developer.apple.com/design/human-interface-guidelines/motion (not fetched; recall)
7. WWDC23, Animate with springs - https://developer.apple.com/videos/play/wwdc2023/10158/ (recall)
8. W3C WCAG 2.2: 2.3.3 https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html ; 2.2.2 https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html ; 2.3.1 https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html (not fetched; recall)
9. WWDC18, Designing Fluid Interfaces - https://developer.apple.com/videos/play/wwdc2018/803/ (recall)
10. Microsoft, Connected animation - https://learn.microsoft.com/windows/apps/design/motion/connected-animation (recall)
11. Atlassian Design, Applying motion - https://atlassian.design/foundations/motion/applying-motion (appeared in search results; page not opened)
12. GitHub Primer, Motion / tokens - https://primer.style/foundations/motion (unverified)
13. NN/g, The Role of Animation and Motion in UX - https://www.nngroup.com/articles/animation-purpose-ux/ (recall)
14. WebAIM / web.dev on vestibular disorders and reduced motion - https://web.dev/articles/prefers-reduced-motion (recall)
15. MDN, prefers-reduced-motion - https://developer.mozilla.org/docs/Web/CSS/@media/prefers-reduced-motion (recall)
16. Qt, QEasingCurve - https://doc.qt.io/qt-6/qeasingcurve.html (recall)
17. Microsoft, SystemParametersInfo SPI_GETCLIENTAREAANIMATION - https://learn.microsoft.com/windows/win32/api/winuser/nf-winuser-systemparametersinfow (recall)
