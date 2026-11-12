# 02 - Motion design for Evrakçı

**Access note (updated 2026-11-12 after the verification pass).** The first draft was written while the network blocked most sources. A second pass reached m3.material.io (JS-rendered, so the raw token sources on GitHub were used instead), nngroup.com, w3.org, learn.microsoft.com, developer.apple.com (HIG JSON, SwiftUI docs JSON, WWDC transcripts), doc.qt.io and raw.githubusercontent.com. Values tagged **[verified]** were read from the cited primary source in that pass. **(recall)** / **(unverified)** remain only where no primary source was reachable (carbondesignsystem.com, fluent2.microsoft.design, polaris.shopify.com, primer.style and shopify.dev were blocked or JS-only). See the "Verification log" at the end for every change.

## TL;DR

- Under ~100 ms feels instantaneous; ~1 s keeps flow of thought; ~10 s is the limit of attention (Nielsen response-time limits) [1]. Motion in a productivity tool should sit mostly in the 100-250 ms band; NN/g puts most UI animation at 100-500 ms, with 100-400 ms appropriate in most cases and 500 ms feeling "like a real drag" [2] [verified].
- Every big design system converges on the same shape: short durations (50-250 ms) for small, frequent UI; longer (300-500 ms) only for large or full-screen changes; "enter = decelerate, exit = accelerate"; long-tail "emphasized" curves reserved for hero moments.
- Material 3 tokens: standard `cubic-bezier(0.2, 0, 0, 1)`, durations short1 50 ms through extra-long4 1000 ms in 50 ms steps up to 600 ms, then 100 ms steps [3] [verified from the Material Web token source].
- Carbon splits motion into **productive** (fast, quiet, task UI) and **expressive** (editorial/moments); productive is the right register for Evrakçı [4] [curves and durations verified from the Carbon repo].
- Fluent 2 gives named durations (durationUltraFast 50 ms to durationUltraSlow 500 ms) and the Windows feel Evrakçı's users already know [5] [verified from the fluentui tokens package]. Note: the first draft had the decelerate/accelerate curve names shifted; corrected in section 3.
- Apple's guidance: motion must be purposeful and optional, "generally avoid adding motion to UI interactions that occur frequently", and never make people wait for an animation to finish [6] [verified]; springs are the default animation in SwiftUI and `.smooth` has no bounce [7] [verified].
- Accessibility: honour the OS reduced-motion setting (WCAG 2.3.3 AAA; WCAG 2.2.2 Level A for anything auto-moving longer than 5 s) [8] [verified]. Qt 6.12 finally exposes this natively: `QStyleHints::accessibility()->motionPreference()` [16][18] [verified]. Vestibular triggers are large-area parallax, zoom and sliding, not short fades.
- For a keyboard-heavy tool: never make the user wait on an animation; input must be accepted mid-animation; repeated actions (arrow-key navigation) get no transition or <=80 ms.
- Qt can do all of this with `QVariantAnimation` + `QEasingCurve.BezierSpline` (and, from Qt 6.12, `QEasingCurve.fromCubicBezier`); prefer animating properties that repaint small regions, avoid `QGraphicsOpacityEffect` on large/live widgets.
- Recommendation: 6 duration tokens (0, 80, 120, 180, 240, 320 ms), 4 curves, one reduced-motion switch that collapses all durations to 0 and keeps only an instant colour/opacity change.

## 1. Apple

### 1.1 HIG Motion principles [6] [verified]
The HIG Motion page (read from developer.apple.com/tutorials/data/design/human-interface-guidelines/motion.json) says: add motion purposefully, "don't add motion for the sake of adding motion"; make motion optional (do not use it as the only way to communicate important information; supplement with haptics/audio); prefer realistic feedback motion that follows gestures and expectations; "aim for brevity and precision in feedback animations"; "In apps, generally avoid adding motion to UI interactions that occur frequently"; and "Let people cancel motion... don't make people wait for an animation to complete before they can do anything, especially if they have to experience the animation more than once." No numeric durations are published in the HIG Motion page (the earlier note about ~0.25-0.35 s system transitions stays **(unverified)**). The only frame-rate number is for games: 30 to 60 fps.

### 1.2 Spring parameters (SwiftUI; WWDC23 "Animate with springs") [7]
Verified from the WWDC23 10158 transcript and Apple's SwiftUI docs:
- Springs are configured with two parameters: **duration** and **bounce**. Bounce is a percentage in the range -1.0 to 1.0; bounce 0 is a "smooth" critically damped curve with a long tail, bounce > 0 overshoots, bounce < 0 is a flattened (overdamped) spring. Code samples in the talk use `duration: 0.5` and `bounce: 0.2` / `0.3` ("large bounce" example).
- "We now use [springs] as the default animation in SwiftUI". Presets exist: Apple's docs describe `.smooth` as a spring "with a predefined duration and no bounce", `.snappy` as "a small amount of bounce", `.bouncy` as "a higher amount of bounce". The numeric preset values (`.snappy` 0.15, `.bouncy` 0.3, default duration 0.5 s) are **(unverified)**; the talk only shows 0.2 and 0.3 as sample bounce values.
- The settling duration of a spring is not the same as the `duration` parameter and is "unpredictable", so do not wait for it for user-facing changes.
- Retargeting: when a spring is interrupted, the previous velocity is kept as the initial velocity toward the new destination ("velocity preservation"), which makes interruptions feel smooth. This is the core argument for springs over fixed-duration curves.
- The older `spring(response:dampingFraction:)` API and the `dampingFraction = 1 - bounce` mapping are **(unverified)**; the talk only says Apple provides equations to convert duration/bounce to mass/stiffness/damping.

### 1.3 "Designing Fluid Interfaces" (WWDC18) [9]
Verified from the transcript: (a) response: "our tools depend on the latency"; be vigilant about every latency or timer introduced into the interface so it always feels responsive; (b) constant redirection and interruption: interfaces should respond to a change of mind mid-gesture (the iPhone X home/multitasking gestures are the worked example) without waiting for an animation to end. The claims about velocity continuity, spatial model and "critically damped springs for most UI" were not located in a targeted search and stay **(unverified)** as attributed to this talk.

### 1.4 Reduce Motion [verified]
The HIG Accessibility page says that when Reduce Motion is on, apps should reduce "automatic and repetitive animations, including zooming, scaling, and peripheral motion", and lists: tighten animation springs to reduce bounce; track animations directly with gestures; avoid animating depth changes in z-axis layers; **replace transitions in x-, y- and z-axes with fades**; avoid animating into and out of blurs. APIs: `NSWorkspace.shared.accessibilityDisplayShouldReduceMotion`, `UIAccessibility.isReduceMotionEnabled`, SwiftUI `@Environment(\.accessibilityReduceMotion)` (names from recall, **(unverified)** this pass). Apple's own pattern is therefore fades, not nothing.

## 2. Google Material 3 [3]

### 2.1 Easing tokens [verified]
Source: Material Web generated token file `tokens/versions/v0_192/_md-sys-motion.scss` (Material 3 v0.192, Web platform) [3a].
| Token (`--md-sys-motion-easing-*`) | cubic-bezier | Use |
|---|---|---|
| standard | (0.2, 0, 0, 1) | on-screen to on-screen, small utility |
| standard-decelerate | (0, 0, 0, 1) | entering |
| standard-accelerate | (0.3, 0, 1, 1) | exiting |
| emphasized-decelerate | (0.05, 0.7, 0.1, 1) | large entering |
| emphasized-accelerate | (0.3, 0, 0.8, 0.15) | large exiting |
| emphasized | web token = (0.2, 0, 0, 1) (identical to standard); the true M3 emphasized curve is a two-segment path that the token export marks "Type motion_path is not supported" | hero transitions |
| linear | (0, 0, 1, 1) | progress |
| legacy / legacy-decelerate / legacy-accelerate | (0.4, 0, 0.2, 1) / (0, 0, 0.2, 1) / (0.4, 0, 1, 1) | M2-era curves, kept for compatibility |

The earlier remark that third-party mirrors disagree on naming for (0.2, 0, 0, 1) is resolved: it is `standard` (and, in the web export only, also `emphasized`). The usage column is the author's paraphrase of the Material guidance and was not re-read on the JS-rendered m3.material.io page **(unverified wording)**.

### 2.2 Duration tokens (ms) [verified]
Same source [3a]: short1 50, short2 100, short3 150, short4 200; medium1 250, medium2 300, medium3 350, medium4 400; long1 450, long2 500, long3 550, long4 600; extra-long1 700, extra-long2 800, extra-long3 900, extra-long4 1000. All sixteen match the first draft.

### 2.3 Transition patterns
Defaults read from the Material Components Android transition classes [3b] [verified]: **MaterialFadeThrough** scales the incoming view from 0.92 (start scale 0.92f) and uses theme duration `motionDurationLong1` (450 ms on the M3 ladder) with the emphasized easing; **MaterialSharedAxis** also defaults to `motionDurationLong1` with emphasized easing; **MaterialFade** uses `motionDurationMedium4` (400 ms) incoming and `motionDurationShort3` (150 ms) outgoing, start scale 0.8. Corrections to the first draft: fade-through and shared-axis library defaults are about 450 ms, not ~300 ms, and the Fade incoming/outgoing durations are 400/150 ms, not 150/75 ms. Still **(unverified)**: the 30 dp shared-axis slide distance and the 90/210 ms fade-through opacity split quoted in the first draft (not found in the code read). The container-transform duration range is **(unverified)**.
These Material defaults are tuned for mobile and are longer than what Evrakçı should use; they are cited as a ceiling reference only.
For Evrakçı's six tabs, the best fit is **fade through** with no scale, or a plain crossfade.

## 3. Microsoft Fluent 2 / Windows [5]
**Fluent 2 tokens [verified]**, from `packages/tokens/src/global/durations.ts` and `curves.ts` in github.com/microsoft/fluentui [5a]:
| Duration token | ms |
|---|---|
| durationUltraFast | 50 |
| durationFaster | 100 |
| durationFast | 150 |
| durationNormal | 200 |
| durationGentle | 250 |
| durationSlow | 300 |
| durationSlower | 400 |
| durationUltraSlow | 500 |

| Curve token | cubic-bezier |
|---|---|
| curveAccelerateMax | (0.9, 0.1, 1, 0.2) |
| curveAccelerateMid | (1, 0, 1, 1) |
| curveAccelerateMin | (0.8, 0, 0.78, 1) |
| curveDecelerateMax | (0.1, 0.9, 0.2, 1) |
| curveDecelerateMid | (0, 0, 0, 1) |
| curveDecelerateMin | (0.33, 0, 0.1, 1) |
| curveEasyEaseMax | (0.8, 0, 0.2, 1) |
| curveEasyEase | (0.33, 0, 0.67, 1) |
| curveLinear | (0, 0, 1, 1) |

Corrections: the first draft attached (0,0,0,1) to decelerate-max and (0.1,0.9,0.2,1) to decelerate-mid (swapped), and (0.9,0.1,1,0.2) to accelerate-mid and (1,0,1,1) to accelerate-max (swapped). The durations were right. There is no "easy-ease-min" token; the Fluent set is Max/plain for easy ease. The principle text on fluent2.microsoft.design/motion is JS-rendered and was not read; "entering decelerate, exiting accelerate" is confirmed by the Windows page below, the rest of the first-draft prose is **(unverified)**.

**Windows / WinUI [verified]** [5b] (Microsoft Learn, "Timing and easing", last updated 2026-02-28): standard WinUI 3 durations `ControlNormalAnimationDuration` 250 ms, `ControlFastAnimationDuration` 167 ms, `ControlFasterAnimationDuration` 83 ms (the first draft's 0.167/0.250 were right). Fluent motion easings: "Fast Out, Slow In" `cubic-bezier(0, 0, 0, 1)` for entering UI, "Slow Out, Fast In" `cubic-bezier(1, 0, 1, 1)` for exiting UI. Connected animation [10] [verified]: the Direct configuration animates over 150 ms with the Decelerate easing; the page advises not waiting more than ~250 ms between preparing and starting the animation. The "~300 ms" figure in the first draft is not in the docs and is dropped. Connected animation suits navigation drill-in, which Evrakçı mostly does not need.

## 4. IBM Carbon [4] [verified]
Source: `packages/motion/tokens/motion.tokens.json` and `src/tokens.ts` in github.com/carbon-design-system/carbon (main) [4a]; the tokens JSON follows the 2025.10 Design Tokens format. All values in the first draft were correct.
Curves (productive): standard `(0.2, 0, 0.38, 0.9)`, entrance `(0, 0, 0.38, 0.9)`, exit `(0.2, 0, 1, 0.9)`. Expressive: standard `(0.4, 0.14, 0.3, 1)`, entrance `(0, 0, 0.3, 1)`, exit `(0.4, 0.14, 1, 1)`.
Durations and the usage text in the token file:
| Token | ms | Token description |
|---|---|---|
| fast-01 | 70 | micro-interactions such as button and toggle; instant response |
| fast-02 | 110 | micro-interactions such as fade in; subtle entrance/exit of small elements |
| moderate-01 | 150 | micro-interactions, small expansion, short distance; "default transition speed" |
| moderate-02 | 240 | expansion, system communication, toast |
| slow-01 | 400 | large expansion, important system notifications |
| slow-02 | 700 | background dimming, large hero transitions |
Carbon's overview page [4b] (carbon-website source): "Reserve expressive motion for occasional, important moments... and offer a rhythmic break to the productive experience." Older Carbon SCSS (`@carbon/styles` `_motion.scss`) also still exports legacy `$ease-in` (0.25, 0, 1, 1), `$ease-out` (0, 0, 0.25, 1), `$standard-easing` (0.5, 0, 0.1, 1), `$transition-base` 250 ms, `$transition-expansion` 300 ms.

## 5. Others
- **Atlassian** [11] [verified; atlassian.design/foundations/motion and /components/tokens/all-tokens]: motion is still "Early Access" behind a feature flag. Guidance: Interactions 50-150 ms (hover/press; example list item hover 50 ms); Transitions 150-400 ms (modals, panels; examples dropdown entrance 150 ms, modal entrance 250 ms). Tokens (introduced v11.5.0): `motion.duration.instant` 0 ms, `xxshort` 50, `xshort` 100, `short` 150, `medium` 200, `long` 250, `xlong` 400, `xxlong` 600. Easings: `out.bold` (0, 0.4, 0, 1), `inout.bold` (0.4, 0, 0, 1), `in.practical` (0.6, 0, 0.8, 0.6), `out.practical` (0.4, 1, 0.6, 1). Semantic examples: list item hovered 50 ms, pressed/selected 100 ms (colour properties only), modal enter 250 ms / exit 200 ms. Rules worth copying: "If someone will trigger this motion dozens of times a day, keep it under 150ms"; "Make exit motion faster than entrances"; "Don't make users wait without reason"; with reduced motion "motion is off and instant"; never flash, rapidly oscillate or sweep large areas. This corrects the first draft's "100/200/350 ms-class" guess.
- **Shopify Polaris** [verified from `polaris-tokens/src/themes/base/motion.ts`, package v9.4.2, main branch]: `motion-duration-0, -50, -100, ... -500` in 50 ms steps plus `-5000`. Easings: `motion-ease` (0.25, 0.1, 0.25, 1), `motion-ease-in` (0.42, 0, 1, 1), `motion-ease-out` (0.19, 0.91, 0.38, 1), `motion-ease-in-out` (0.42, 0, 0.58, 1), `motion-linear` (0, 0, 1, 1). Keyframes include `bounce`, `fade-in`, `pulse`, `spin`, `appear-above/below` (a translateY of one `space-100` unit with fade). The polaris.shopify.com docs pages were blocked.
- **GitHub Primer** [12] [verified from github.com/primer/primitives `src/tokens/base/motion` and `functional/motion`]: base durations 0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000 ms (no 150 or 250). Base easings: linear (0,0,1,1); ease (0.25, 0.1, 0.25, 1); easeIn (0.7, 0.1, 0.75, 0.9); easeOut (0.3, 0.8, 0.6, 1); easeInOut (0.6, 0, 0.2, 1). Semantic durations: `motion.duration.micro` 100 ms (hover, focus ring, colour shifts), `short` 200 ms (expand/collapse, toggles), `medium` 300 ms (modals, dropdowns entering/exiting), `long` 500 ms ("use sparingly"). Semantic easings: hover = ease, enter = easeOut (recommended default), exit = easeIn, move = easeInOut. Composite transitions: hover (micro, ease), stateChange (short, move), enter (medium, enter), exit (short, exit); the rule text says "Shorter than enter to feel snappy" and "MUST respect prefers-reduced-motion". The primer.style pages are JS-only and were not read; the repo supersedes the first draft's `--base-duration-100..` guess.
Cross-check consensus: none of these use durations over 500 ms for ordinary UI (Carbon slow-02 700 ms and Atlassian xxlong 600 ms are for hero/onboarding moments; Primer `long` 500 ms is "use sparingly").

## 6. Research on motion and usability
- **Response-time limits (Nielsen, 1993; NN/g)** [1] [verified]: 0.1 s is about the limit for the user to feel the system reacts instantaneously (no special feedback needed except to display the result); 1.0 s is about the limit for the user's flow of thought to stay uninterrupted even though the delay is noticed (the user "loses the feeling of operating directly on the data"); 10 s is the limit for keeping attention; beyond it use a percent-done indicator and a clearly signposted way to interrupt. Nielsen also advises a percent-done indicator for operations over ~10 s, and, for 2-10 s, only less conspicuous feedback because a flashing percent bar violates "display inertia". Animation that stretches an interaction beyond ~100 ms must justify itself (author's inference).
- **NN/g "Executing UX Animations: Duration and Motion Characteristics"** (Page Laubheimer, 9 Feb 2020) [2] [verified]: "the duration of most animations should be in the range of 100-500 ms, depending on complexity and on how far the element is traveling"; look for "the shortest time that an animation can take without being jarring. It is far more common for animations to be too long than too short." Simple feedback (checkbox, toggle) roughly 100 ms, which "feels immediate"; substantial screen changes such as a modal moving into view 200-300 ms; "At 500ms, animations start to feel like a real drag"; "In most cases, a range of 100-400 ms is appropriate, with 400ms being a very slow animation, to be used only for big movements across large screens"; entering needs a subtly longer duration than exiting (popup 300 ms in, 200 or 250 ms out). Easing: linear motion looks unnatural; use ease-out for entrances and ease-in for exits (ease-out feels responsive; ease-in/in-out for leaving can feel unresponsive if the start is slow); an arc path looks more natural than a diagonal. The article also warns that opacity changes can be computationally expensive on many platforms when many elements change at once. **Removed from the first draft:** the "mobile 200-300 ms / desktop about 150 ms" split; the article does not give a desktop/mobile split.
- **Benefits of motion** (NN/g "The Role of Animation and Motion in UX", Page Laubheimer, 12 Jan 2020) [13] [verified]: motion is best as subtle feedback for microinteractions, not to entertain; uses are feedback that an action was recognised (counters change blindness), communicating state/mode changes, spatial metaphors for navigation, and signifiers of how elements behave. Costs: motion attracts attention via peripheral vision and easily distracts; time-filling "down-time" animations frustrate participants; several simultaneous animations overwhelm. The first draft's "perceived performance" item is not a heading of that article and is dropped.
- **Productivity-tool corollary**: with 1h+ sessions, any decorative animation is repaid hundreds of times a day. Animation of 200 ms on an action done 2,000 times per session costs ~6.7 minutes of cumulative waiting if it blocks input (arithmetic, not a citation). Hence non-blocking, skippable motion.
- **Vestibular disorders / motion sensitivity**: WCAG's own Understanding text names scrolling-triggered element movement and parallax as vestibular triggers (dizziness, nausea, headaches) [8] [verified]; Apple lists zooming, scaling, peripheral motion, z-depth changes and animated blurs [6b] [verified]; NN/g mentions epilepsy and vestibular sensitivity for long-travel motion [2] [verified]. "Small opacity/colour changes are safe" is the author's inference, consistent with Apple's advice to replace movement with fades. Web.dev/WebAIM [14] not re-read **(recall)**.
- **WCAG** [8] [verified, WCAG 2.2 Understanding pages]: **2.3.3 Animation from Interactions (Level AAA)**: "Motion animation triggered by interaction can be disabled, unless the animation is essential to the functionality or the information being conveyed." Sufficient techniques listed: avoid unnecessary animation, provide a control to turn off non-essential animation, or use the user-agent/OS reduce-motion feature. **2.2.2 Pause, Stop, Hide (Level A)**: for moving, blinking or scrolling information that (1) starts automatically, (2) lasts more than five seconds and (3) is presented in parallel with other content, there must be a mechanism to pause, stop or hide it unless essential; auto-updating information needs a pause/hide/frequency control. **2.3.1 Three Flashes or Below Threshold (Level A)**: nothing flashes more than three times in any one second, or the flash is below the general and red flash thresholds (the luminance-change wording in our rule 11 is a simplification). CSS `prefers-reduced-motion` is the web expression of the OS setting [15] (recall).

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
Exits are 70-75 % of the matching enter (e.g. 180 in, 130 out). Cross-check: NN/g 300 in / 200-250 out (67-83 %), Atlassian modal 250 in / 200 out (80 %), Primer enter 300 / exit 200 (67 %), Material Fade 400 / 150; the 70-75 % figure is the author's choice inside that range. Hard ceiling 400 ms; nothing in the tool exceeds it except indeterminate progress which is looped and not motion-heavy.

### 7.2 Curves (cubic-bezier x1,y1,x2,y2)
| Token | Value | Use |
|---|---|---|
| `ease.standard` | (0.2, 0, 0, 1) | default state changes, moves (M3 standard) |
| `ease.enter` | (0, 0, 0, 1) | things appearing (M3 standard-decelerate = Fluent curveDecelerateMid = Fluent "Fast Out, Slow In") |
| `ease.exit` | (0.3, 0, 1, 1) | things leaving (M3 standard-accelerate; Fluent's exit is (1, 0, 1, 1)) |
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
1. No animation may delay input handling: every animation is non-blocking and the next keypress/click is processed immediately and retargets the running animation (interruptible, as Apple's fluid interface principle [9] and HIG "let people cancel motion" [6]).
2. Maximum duration for any UI transition is 320 ms; default interaction transitions are 80-240 ms. Test: grep for any animation duration constant > 320 ms outside indeterminate progress. (Supported by: NN/g 100-400 ms "in most cases", Atlassian frequent actions under 150 ms.)
3. Repeated keyboard actions (arrow navigation, accept-next, undo/redo bursts) use `motion.none` or at most 80 ms; a held key must never queue animations.
4. Use only the four curves in 7.2; entering elements use `ease.enter`, leaving use `ease.exit`, moves use `ease.standard`. No overshoot/bounce anywhere.
5. Animate only opacity, colour and short translations (<= 24 px). No scale or zoom for panels, no parallax, no full-window slides, no auto-rotating or looping decorative motion.
6. Exit duration = ~70-75 % of enter duration.
7. A single app-level `reduced_motion` flag, initialised from the OS and overridable in settings; when on, all durations resolve to 0 (state changes still happen, as instant colour/opacity swaps) and progress indicators become static.
8. State must never be conveyed by motion alone: every animated change (accept, error, cut added) also leaves a persistent visible state (icon, text, colour with contrast per the colour research file).
9. Looping animation (spinner, indeterminate bar) must be small (< ~32 px area), and stop when the window is inactive; anything auto-playing for >5 s needs a pause path or must be non-essential (WCAG 2.2.2 [8]).
10. Motion tokens live in one module (`motion.py`) and widgets never hardcode a duration; every animated widget goes through a helper that applies the reduced-motion flag.
11. Never flash: nothing may flash more than 3 times in any one second (WCAG 2.3.1 [8]); in practice the success highlight fires once.
12. Success/accept highlights fade out in <= 400 ms total and must not repeat; the screen should be visually still while the user reads.

## 9. Qt / PySide6 feasibility notes

**Animation classes.** `QPropertyAnimation` animates any `Q_PROPERTY` (in PySide6 use `@Property(type, fget, fset)`) and is the simplest route for `pos`, `geometry`, `windowOpacity`, `maximumHeight`. `QVariantAnimation` gives a raw `valueChanged` signal and works for custom-painted widgets: store the animated value in a member (hover progress 0..1) and call `update()` (or `update(rect)`) in the slot. `QParallelAnimationGroup` / `QSequentialAnimationGroup` compose them. Set `setDuration(ms)` and `setEasingCurve(...)`; retargeting a running animation is done by `stop()`, `setStartValue(current)`, `setEndValue(new)`, `start()`, which gives interruptibility (no velocity carry-over; Qt has no built-in spring; a spring would need a custom timer-based integrator, e.g. QTimer at 16 ms).

**Custom cubic-bezier [16] [verified, Qt 6.12 docs].** `QEasingCurve(QEasingCurve.BezierSpline)` then `curve.addCubicBezierSegment(QPointF(x1, y1), QPointF(x2, y2), QPointF(1, 1))`. Qt docs: the type enum is `QEasingCurve::BezierSpline` (value 45, "custom easing curve using a cubic bezier spline"); `addCubicBezierSegment(c1, c2, endPoint)` is "only applicable if type() is BezierSpline... the spline implicitly starts at (0.0, 0.0) and has to end at (1.0, 1.0) to be a valid easing curve". This maps exactly to CSS `cubic-bezier(x1,y1,x2,y2)`. **New in Qt 6.12:** the static `QEasingCurve::fromCubicBezier(c1, c2)` convenience, equivalent to creating a BezierSpline curve and calling `addCubicBezierSegment(c1, c2, QPointF(1, 1))`; `toCubicSpline()` returns the points. Use the 3-argument call if the app must run on Qt < 6.12. Example for `ease.standard`: `c.addCubicBezierSegment(QPointF(0.2,0), QPointF(0,1), QPointF(1,1))`. Qt also has built-in `OutCubic` and `OutQuint` which are close to decelerate-max (approximation only). Verify with a unit test comparing sampled `valueForProgress` to an independent bezier solver (Qt's docs describe BezierSpline [16]).

**QGraphicsOpacityEffect costs.** It renders the widget (and children) into an offscreen pixmap each frame, which defeats native acceleration, can blur text on non-integer device pixels, and interacts badly with other effects and with child widgets that also repaint (e.g. a thumbnail grid). It also forbids using the effect on a widget which has an effect on an ancestor (undefined). Use it only for small, short-lived widgets (toast, popover, ~180 ms). For large views (the thumbnail timeline, tables) avoid it: crossfade by painting two cached `QPixmap` snapshots with `painter.setOpacity()` in a dedicated overlay widget, or just swap instantly. For top-level windows/popups `setWindowOpacity` is cheaper (needs compositing; works on Windows/macOS, depends on compositor on Linux/X11).

**Custom-painted widgets.** Drive a float "progress" with a `QVariantAnimation`; in `paintEvent` interpolate colours with `QColor` lerp (in linear light if possible, otherwise just sRGB). Call `update(rect)` on the dirty region only, and never run more than one frame timer (Qt default animation timer ~16 ms, i.e. ~60 fps; fine on office PCs). For `QStyleSheet`-styled widgets, stylesheet properties cannot be animated by Qt natively (no transitions); animate a custom property and repaint, or switch to a `QPalette`/custom paint approach for hover colours. Avoid animating `geometry` of items inside layouts (it forces relayout every frame); animate `maximumHeight` sparingly or use an overlay. For `QGraphicsView`/`QGraphicsItem` thumbnails, use `QGraphicsObject` properties and `ItemCoordinateCache` where items are static.

**Honouring reduced motion.**
- **Windows** [17b] [verified: `SPI_GETCLIENTAREAANIMATION` 0x1042, pvParam points to a BOOL that receives TRUE if animations are enabled, FALSE otherwise]: `SystemParametersInfoW(SPI_GETCLIENTAREAANIMATION = 0x1042, 0, &BOOL, 0)` returns FALSE when "Show animations in Windows" is off (Settings > Accessibility > Visual effects > Animation effects) [17]. In PySide6 call via `ctypes.windll.user32.SystemParametersInfoW(0x1042, 0, ctypes.byref(b), 0)` with `b = ctypes.c_int()`. Re-read on `WM_SETTINGCHANGE` (override `nativeEvent` or an `QAbstractNativeEventFilter`) so the app follows live changes. `UISettings.AnimationsEnabled` (WinRT) is an alternative (unverified in PySide).
- **macOS**: `NSWorkspace.sharedWorkspace().accessibilityDisplayShouldReduceMotion()` via PyObjC; observe `NSWorkspaceAccessibilityDisplayOptionsDidChangeNotification` for live updates (recall).
- **Linux**: GNOME `org.gnome.desktop.interface enable-animations` (gsettings) / GTK `gtk-enable-animations`; KDE has "Animation speed" in `kdeglobals` (`AnimationDurationFactor`, 0 = off) (recall). Fall back to the in-app setting.
- **Qt itself [verified, Qt 6.12 docs] [17][18]:** `QStyleHints::accessibility()` returns a `QAccessibilityHints` object (class since Qt 6.10, "platform specific accessibility hints"). It has `contrastPreference` (since 6.10) and, **since Qt 6.12**, a read-only property `motionPreference : Qt::MotionPreference` with notifier signal `motionPreferenceChanged(Qt::MotionPreference)`. The enum `Qt::MotionPreference` (since 6.12) has `NoPreference = 0` and `ReducedMotion = 1` ("The user prefers fewer animations in their UI"); the docs say respecting it "may make the application more accessible to those that suffer from vestibular motion disorders". In PySide6 this would be `QGuiApplication.styleHints().accessibility().motionPreference()` (binding names inferred, **(unverified)**; confirm the installed PySide6 version actually ships Qt 6.12). `QStyleHints` itself has no reduce-motion property (checked the 6.12 member list). The first draft's "no cross-platform property is known" is therefore out of date for Qt >= 6.12 but still true for 6.10/6.11 and earlier. Plan: implement `platform_prefs.reduced_motion()` as: Qt >= 6.12 -> `motionPreference`; else the per-OS probes above; plus an app setting "Animations: System / On / Off" and a global factor in the helper that makes `duration = 0 if reduced else token`.
- When reduced, still emit the final state immediately (call `setEndValue` then `setCurrentTime(duration)` or skip animation and set the value).

**Testing.** Add a headless test that every `QAbstractAnimation` created through the helper has `duration() == 0` when the flag is on; and a manual test at 1366x768 on a low-end PC to confirm there are no dropped frames at the 240 ms transitions.

## Sources (accessed 2026-11-12; [verified] marks pages/files actually read in the verification pass)
1. Nielsen, Response Times: The 3 Important Limits (1993, updated 2014) - https://www.nngroup.com/articles/response-times-3-important-limits/ [verified]
2. NN/g, Executing UX Animations: Duration and Motion Characteristics (9 Feb 2020) - https://www.nngroup.com/articles/animation-duration/ [verified]
3. Material 3, Easing and duration tokens - https://m3.material.io/styles/motion/easing-and-duration/tokens-specs (JS-rendered, text not extractable). Values verified from:
   - 3a. https://raw.githubusercontent.com/material-components/material-web/main/tokens/versions/v0_192/_md-sys-motion.scss [verified]
   - 3b. https://raw.githubusercontent.com/material-components/material-components-android/master/lib/java/com/google/android/material/transition/MaterialFadeThrough.java (also MaterialSharedAxis.java, MaterialFade.java) [verified]
4. IBM Carbon, Motion - https://carbondesignsystem.com/elements/motion/overview/ (host blocked this pass). Verified from:
   - 4a. https://raw.githubusercontent.com/carbon-design-system/carbon/main/packages/motion/tokens/motion.tokens.json and .../packages/motion/src/tokens.ts [verified]
   - 4b. https://raw.githubusercontent.com/carbon-design-system/carbon-website/main/src/pages/elements/motion/overview.mdx [verified]
5. Fluent 2, Motion - https://fluent2.microsoft.design/motion (JS-rendered, not extractable). Verified from:
   - 5a. https://raw.githubusercontent.com/microsoft/fluentui/master/packages/tokens/src/global/durations.ts and curves.ts [verified]
   - 5b. Microsoft Learn, Timing and easing - https://learn.microsoft.com/en-us/windows/apps/design/motion/timing-and-easing [verified]
6. Apple HIG, Motion - https://developer.apple.com/design/human-interface-guidelines/motion (read via https://developer.apple.com/tutorials/data/design/human-interface-guidelines/motion.json) [verified]; 6b. HIG Accessibility (same JSON route, accessibility.json), Reduce Motion section [verified]
7. WWDC23, Animate with springs - https://developer.apple.com/videos/play/wwdc2023/10158/ [verified, transcript]; SwiftUI `Animation.smooth/.snappy/.bouncy` docs via https://developer.apple.com/tutorials/data/documentation/swiftui/animation/<name>.json [verified]
8. W3C WCAG 2.2: 2.3.3 https://www.w3.org/WAI/WCAG22/Understanding/animation-from-interactions.html ; 2.2.2 https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html ; 2.3.1 https://www.w3.org/WAI/WCAG22/Understanding/three-flashes-or-below-threshold.html [verified]
9. WWDC18, Designing Fluid Interfaces - https://developer.apple.com/videos/play/wwdc2018/803/ [verified, transcript: response, interruption/redirection]
10. Microsoft, Connected animation - https://learn.microsoft.com/en-us/windows/apps/design/motion/connected-animation [verified]
11. Atlassian Design, Motion - https://atlassian.design/foundations/motion and token list https://atlassian.design/components/tokens/all-tokens [verified]
12. GitHub Primer primitives - https://raw.githubusercontent.com/primer/primitives/main/src/tokens/base/motion/easing.json5, .../timing.json5, .../functional/motion/motion.json5 [verified]; docs page https://primer.style/foundations/primitives/motion (JS-only, not read)
12b. Shopify Polaris tokens - https://raw.githubusercontent.com/Shopify/polaris/main/polaris-tokens/src/themes/base/motion.ts [verified]
13. NN/g, The Role of Animation and Motion in UX (12 Jan 2020) - https://www.nngroup.com/articles/animation-purpose-ux/ [verified]
14. WebAIM / web.dev on vestibular disorders and reduced motion - https://web.dev/articles/prefers-reduced-motion (recall, not fetched)
15. MDN, prefers-reduced-motion - https://developer.mozilla.org/docs/Web/CSS/@media/prefers-reduced-motion (recall, not fetched)
16. Qt, QEasingCurve (Qt 6.12) - https://doc.qt.io/qt-6/qeasingcurve.html [verified]
17. Qt, QStyleHints - https://doc.qt.io/qt-6/qstylehints.html [verified: `accessibility` property, no motion property]; 17b. Microsoft, SystemParametersInfoW - https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-systemparametersinfow [verified]
18. Qt, QAccessibilityHints (since 6.10; `motionPreference` since 6.12) - https://doc.qt.io/qt-6/qaccessibilityhints.html ; Qt::MotionPreference - https://doc.qt.io/qt-6/qt.html [verified]

## Verification log (2026-11-12)

**Corrected (first draft was wrong)**
- Fluent 2 curves: decelerate-max/mid and accelerate-max/mid were swapped. Correct: curveDecelerateMax (0.1,0.9,0.2,1), curveDecelerateMid (0,0,0,1), curveAccelerateMax (0.9,0.1,1,0.2), curveAccelerateMid (1,0,1,1). Token names are camelCase (`durationUltraFast`, `curveEasyEase`...); there is no easy-ease-min; curveLinear added. Recommended `ease.enter` comment re-attributed to Fluent curveDecelerateMid.
- Material 3 fade-through / shared-axis defaults are ~450 ms (long1), not ~300 ms; Fade is 400 ms in / 150 ms out, not 150/75 ms. Fade-through start scale 0.92 confirmed.
- NN/g: removed the invented "mobile 200-300 ms, desktop ~150 ms" split; replaced with the article's real numbers (checkbox/toggle ~100 ms, modal 200-300 ms, 500 ms is a drag, 100-400 ms typical, enter 300 vs exit 200-250 ms). Dropped "perceived performance" from the benefits list (not in the article).
- Apple HIG Motion: the "replace large movement with crossfades" sentence belongs to the HIG Accessibility Reduce Motion section, not Motion; the Motion page's real key rules (avoid motion on frequent interactions, let people cancel, don't make people wait) were added.
- Atlassian: first-draft "100/200/350 ms-class" guess replaced by the real tokens (0/50/100/150/200/250/400/600 ms) and curves.
- Primer: replaced the guessed `--base-duration-100..` with the real base (0-1000 in non-uniform steps) and semantic (micro 100, short 200, medium 300, long 500) tokens and easings.
- Qt: the claim that no `QStyleHints`/Qt API exists for reduced motion is outdated: Qt 6.12 adds `QAccessibilityHints::motionPreference` and `Qt::MotionPreference` (QAccessibilityHints itself since 6.10).
- Windows connected animation "~300 ms" removed (docs say Direct = 150 ms, ~250 ms prepare-to-start window).

**Confirmed unchanged (now verified)**
- All 16 Material 3 duration tokens (50...1000 ms) and easing curves standard / standard-decelerate / standard-accelerate / emphasized-decelerate / emphasized-accelerate; added emphasized (web export = 0.2,0,0,1), linear and legacy curves.
- Fluent 2 durations (50/100/150/200/250/300/400/500 ms); WinUI 250/167/83 ms.
- Carbon productive and expressive curves and the six duration tokens (70/110/150/240/400/700 ms); usage descriptions added.
- Polaris duration scale in 50 ms steps and the `motion-ease*` names; exact curves added.
- NN/g 100-500 ms range and Nielsen's 0.1 / 1 / 10 s limits; WCAG 2.3.3 (AAA), 2.2.2 (A, 5 s), 2.3.1 (A, 3 flashes) wording; SPI_GETCLIENTAREAANIMATION = 0x1042; `QEasingCurve.BezierSpline` + `addCubicBezierSegment` with implicit start at (0,0).
- SwiftUI: springs are the default animation; `.smooth` has no bounce; velocity is preserved on interruption; bounce range -1 to 1.

**Still unverified (tags kept)**
- Apple: numeric `.snappy` (0.15) / `.bouncy` (0.3) preset values, default spring duration 0.5 s, `response/dampingFraction` mapping, "~0.25-0.35 s system transitions", exact AppKit/UIKit Reduce Motion API names this pass, and the WWDC18 claims about velocity continuity / critically damped springs.
- Material: 30 dp shared-axis distance, 90/210 ms fade-through split, container-transform duration range, and the exact "use" wording on m3.material.io (JS-rendered).
- Fluent 2 principles prose (fluent2.microsoft.design JS-rendered), Carbon "when to use" prose beyond the token descriptions (carbondesignsystem.com blocked), Primer and Polaris docs prose (primer.style JS-only, polaris.shopify.com / shopify.dev blocked).
- macOS NSWorkspace notification name, GNOME `enable-animations`, KDE `AnimationDurationFactor`, `UISettings.AnimationsEnabled` from PySide, web.dev/MDN pages, and whether the PySide6 release in use bundles Qt 6.12.
- All Evrakçı-specific numbers in sections 7 and 8 are design recommendations by the author, not citations; they were cross-checked against the verified ranges above and stay within them (max 320 ms; frequent actions <= 120 ms; Atlassian: frequent < 150 ms).
