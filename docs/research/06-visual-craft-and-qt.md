# 06 — Visual design craft, and what is achievable in Qt/PySide6

**Research caveat.** The research sandbox could only reach github.com. Primary design-system sites (radix-ui.com, doc.qt.io, material.io, apcacontrast, W3C) did not resolve. Items checked live on GitHub are cited as [n] with an access date. Everything else is established background knowledge, marked **(bg)** = "from background knowledge, not re-verified this session". Treat **(bg)** numbers as to be re-checked against the primary source before they go into the final prompt. Nothing below is invented; where unsure it says "(unverified)".

## TL;DR

- Build colour in a perceptual space (OKLCH or CIELAB/HCT), not HSL. Generate a 12-step neutral and a 12-step accent ramp per hue, then freeze them as primitives. Ship hex values to Qt.
- Use the Radix 12-step role model: steps 1–2 backgrounds, 3–5 component fills (rest/hover/active), 6–8 borders, 9–10 solid fills, 11–12 text **(bg)**. It makes light and dark themes mechanically derivable.
- Tint neutrals slightly toward the brand hue (chroma about 0.005–0.02 in OKLCH). Avoid pure #000 and #FFF in both themes.
- Contrast: WCAG 2 ratios (4.5:1 body, 3:1 large text and UI components) are the legal/audit floor **(bg)**. Use APCA Lc values as a second check, because WCAG 2 misjudges dark mode and thin type **(bg)**. For our older users, aim above the floor: at least 7:1 for primary text.
- Never signal status by colour alone. Pair every status colour with an icon and a text label. Colour-blind safety is a hard requirement for "nothing silently wrong".
- Type: one UI family, bundled (OFL). Inter or IBM Plex Sans are the strongest candidates because both have tabular figures and Latin Extended (Turkish ı İ ğ ş). Base size 13–14 px, a modular scale of about 1.125–1.2, line height about 1.4–1.5.
- Spacing on a 4 px base with 8 px rhythm. Radius scale of three or four steps (4/6/8/12). Hairline 1 px borders define surfaces; shadows only for floating layers.
- Dark mode: surfaces at about L 0.18–0.28 in OKLCH, rising with elevation. Desaturate accents. No pure black.
- "Premium" is mostly restraint: hairlines, layered surfaces, one accent, crisp small type, strong focus rings, zero decorative gradients.
- Qt reality: QSS cannot do shadows, transitions or variables. Plan for a token-driven QSS template generator plus a small custom-painted widget layer (QPainter) for the hero components. Avoid PyQt-Fluent-Widgets as a dependency (GPL-3 / commercial; see licence analysis).

## 1. Colour systems

### 1.1 Perceptual spaces
- **HSL** lightness is not perceptual: yellow at L 50% looks far brighter than blue at L 50%. Ramps built in HSL have uneven contrast between steps.
- **CIELAB (L\*a\*b\*)** is roughly perceptual in lightness; hue shifts in blue are known artefacts **(bg)**.
- **OKLab/OKLCH** (Björn Ottosson, 2020) fixes most hue drift and is now in CSS Color 4/5. L is 0–1, C is chroma (about 0–0.4), H is hue in degrees **(bg)**. Practical benefit: equal L steps give roughly equal perceived steps, so one lightness curve can be reused across hues.
- **Material 3 HCT** = CIE hue and chroma plus CIELAB L\* as "Tone". Material builds a tonal palette per key colour with tones 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99, 100 **(bg)**. Because Tone is L\*, a contrast difference of about 40 tone units between two colours reliably gives at least 3:1, and about 50 gives at least 4.5:1 **(bg)**. This makes accessible pairs by construction, which is a useful rule for us: pick text and background tones at least 50 apart.
- Qt has no OKLCH support. Generate palettes offline (a small Python script using `colour-science` or hand-coded OKLab maths) and commit the resulting hex tokens. Do not compute at runtime.

### 1.2 Radix Colors 12-step scale (role of each step) **(bg)**
Radix's scale is designed so each step has one job, in both light and dark:

| Step | Role |
|---|---|
| 1 | App background |
| 2 | Subtle background (sidebars, striped rows, cards) |
| 3 | UI element background (rest) |
| 4 | UI element background (hover) |
| 5 | UI element background (active/selected) |
| 6 | Subtle borders and separators |
| 7 | UI element border, focus rings |
| 8 | Hovered UI element border |
| 9 | Solid background (highest chroma, the "pure" colour) |
| 10 | Hovered solid background |
| 11 | Low-contrast text |
| 12 | High-contrast text |

Radix states steps 11 and 12 meet roughly APCA Lc 60 and Lc 90 against steps 1–2 **(bg, unverified in detail)**. Licence: MIT **(bg)**. The takeaway for us: define roles, not colours. A table row hovering in Değerler uses step 3 → 4, a selected row step 5 with a step 7 border, and so on. Radix also ships "alpha" variants of each step so overlays work on any background; in Qt we can use `rgba()` in QSS for these.

### 1.3 Neutral tinting
Neutrals with a hint of the brand hue (Radix's Slate, Mauve, Sage pairings; Tailwind's slate/zinc/stone) feel more cohesive than pure grey **(bg)**. Rule of thumb: chroma 0.005–0.02 in OKLCH, same hue as the accent (or a complementary muted hue). Pure grey next to a coloured accent looks dead, but too much tint reads as a colour cast on scanned-document previews, which matters for us because staff judge page content on the page background. Keep the page-preview surface neutral grey or dark.

### 1.4 Semantic tokens and status colours
- Layers: **primitive** (blue-9) → **semantic** (`accent.solid`, `text.primary`, `status.error.fg`) → **component** (`button.primary.bg`). Code uses only semantic/component names.
- Status set for Evrakçı: success (OK/accepted), warning (needs check), error (failed/cut missing), info (neutral hint), plus "unreviewed/pending". Each needs fg, bg-subtle, border, and solid variants.
- Status must be encoded redundantly: colour + icon shape + word (for example a check circle, a triangle and an octagon, with "Onaylandı", "Kontrol et", "Hata"). About 8% of men have red-green colour deficiency **(bg)**; red/green alone is forbidden.
- Prefer a blue-orange pair over red-green for good/bad where a binary is needed.

### 1.5 Contrast: WCAG 2 vs APCA
- WCAG 2.x (and 2.2): text 4.5:1 (AA), 7:1 (AAA); large text (≥24 px, or ≥18.66 px bold) 3:1; UI components and graphical objects 3:1 against adjacent colours (SC 1.4.11) **(bg)**. WCAG 2.2 adds minimum target size 24×24 CSS px (SC 2.5.8, AA) and focus appearance in AAA **(bg)**.
- WCAG 2 weaknesses: ignores font weight and size beyond a binary, over-rates mid-dark text on dark backgrounds, and under-rates thin light-on-dark text **(bg)**.
- APCA (WCAG 3 draft candidate) outputs Lc (about 0–106). Commonly cited guidance: Lc 90 preferred for body text, Lc 75 minimum for body/column text, Lc 60 minimum for content text at larger sizes, Lc 45 for large/headline text, Lc 30 for non-text minimums, below Lc 15 effectively invisible **(bg)**. APCA is still draft and not a legal standard.
- Rule for us: verify every text/background pair with both. Legal/audit floor is WCAG AA; design target is WCAG ≥ 7:1 for body text and Lc ≥ 75 (Lc 90 for 12–13 px text). Disabled text may be lower but must stay readable (≥ 3:1); never use disabled styling to hide information.
- Automate: a pytest that loads the token file and asserts every declared pair meets its threshold in both themes.

## 2. Typography

### 2.1 Scales
- Modular scale: size_n = base × ratio^n. Common ratios: 1.125 (major second), 1.2 (minor third), 1.25 (major third). Dense desktop UIs need a small ratio (≤ 1.2), because there is little space for large jumps.
- Suggested scale at base 14 px, ratio about 1.15–1.2, rounded to whole pixels: 11 (caption/meta), 12 (secondary), 14 (body), 16 (emphasis/section), 20 (page title), 24 (rare display). Whole-pixel sizes are crisp at 100% scaling on Windows.
- Windows/Fluent reference: Windows type ramp is Caption 12, Body 14, Body Strong 14 semibold, Subtitle 20, Title 28, Display 68 (effective pixels, Segoe UI Variable) **(bg)**. Material 3 body-medium is 14 sp, body-large 16 sp **(bg)**. Our users are older: **minimum 12 px for anything readable, 14 px default body, and a user-selectable scale (100/115/130%)**.
- Line height: 1.4–1.5 for body; 1.2–1.3 for headings; table rows are driven by row height (see spacing), not leading. Measure (line length) 45–75 characters for prose such as the Rehber tab; cap Rehber text width at about 70 characters.
- Weights: use only 400, 500 or 600, and 700 sparingly. Variable fonts allow 450–550 fine-tuning, but Qt handles named weights more reliably (see §9).
- **Tabular figures** (`tnum`) are mandatory for page numbers, counts, amounts and dates in tables so columns align. Qt 6 can request OpenType features via `QFont.setFeature` / `QFont::setFeature` in Qt 6.7+ **(bg, verify version)**. Safer fallback: choose a font that makes digits tabular by default (IBM Plex Sans digits are tabular by default **(bg, unverified)**).
- Letter-spacing: Inter's optical-size design (Inter Display for ≥ ~20 px) is meant to be tighter at large sizes; at UI sizes use default tracking. Do not apply negative tracking to 12–14 px text.

### 2.2 Font candidates (bundling, licence, Turkish)
Turkish needs ı, İ, ğ/Ğ, ş/Ş, ç, ö, ü, with correct dotted/dotless capitals. All Latin Extended-A fonts below cover these; confirm with a glyph test string ("İıĞğŞşÇçÖöÜü ISIK ığdır").

| Font | Licence | Notes |
|---|---|---|
| Inter | SIL OFL 1.1; reserved font name "Inter" [1] | Variable and static weights 100–900, tabular numbers, slashed zero, tall x-height [1]. Turkish coverage: not stated on the repo page [1]; widely reported to include Latin Extended **(bg)**, so test. Best all-round UI choice. |
| Atkinson Hyperlegible Next | SIL OFL 1.1 [2] | Designed by the Braille Institute for low vision; 6 weights with italics [2]. Repo is archived read-only [2]. Language coverage not stated on the repo page [2] (Next reportedly supports 150+ languages **(unverified)**). Excellent legibility for older users; numerals less compact and no stated tabular figures **(unverified)**. |
| IBM Plex Sans | SIL OFL 1.1 **(bg)** | Includes Turkish, tabular digits **(bg)**; a slightly more "technical" tone; many weights (static). |
| Noto Sans | SIL OFL 1.1 **(bg)** | Maximal coverage, neutral, a little wide; safe fallback and for any CJK/Cyrillic. |
| Source Sans 3 | SIL OFL 1.1 **(bg)** | Compact, good at small sizes; variable version exists. |
| Segoe UI / Segoe UI Variable | Proprietary Microsoft; ships with Windows, **not redistributable** **(bg)** | Use as the *system* fallback on Windows only (`font-family` list), never bundle. |
| SF Pro | Apple licence, restricted to Apple platforms **(bg)** | Do not bundle. |

OFL practicalities **(bg)**: bundling and redistribution inside an app are allowed; the font may not be sold by itself; modified versions must not use the Reserved Font Name; ship the OFL text and copyright notice alongside. OFL is compatible with an AGPL app as a separate asset (fonts are data, not linked code).

**Recommendation to test**: Inter (default UI), with Atkinson Hyperlegible Next as an optional "high legibility" user setting. Both OFL. Run an A/B at 13/14 px on a 1366×768 panel before deciding.

## 3. Spacing and density
- 4 px base unit, 8 px rhythm: 4, 8, 12, 16, 24, 32, 48. Material uses an 8 dp grid with 4 dp for small components/icons **(bg)**; Fluent uses 4 px multiples **(bg)**.
- Density scales: Material defines density -1…-3 in 4 dp steps (compact rows 48→40→36→32 dp) **(bg)**. Windows Fluent standard control height is 32 px; compact is 24 px **(bg)**.
- Proposed for Evrakçı (office staff, long sessions, 1366×768 screens): three user-selectable densities. Comfortable (row 40, control 36), Default (row 32, control 32), Compact (row 28, control 28). Never go below 24 px hit height (WCAG 2.2 SC 2.5.8 minimum) **(bg)**; prefer ≥ 32 for primary actions.
- Padding inside controls: horizontal = 2× vertical. Group spacing 16, section spacing 24–32. Use the same few values everywhere; arbitrary values (5, 7, 10 px) are the main cause of "amateur" feel.
- Align text baselines of labels and inputs; align numeric columns right (tabular figures).

## 4. Iconography

| Set | Licence | Grid/stroke |
|---|---|---|
| Lucide | ISC [3] | Stroke icons, 24×24 grid, 2 px default stroke (adjustable) **(bg; repo page did not state grid/stroke [3])**; ~1,600+ icons [3] (the page contradicts itself: 1600+ vs 2000+ [3]) |
| Phosphor | MIT **(bg)** | 6 weights (thin…bold, duotone), 256 grid in source, rendered 24 px **(bg)** |
| Tabler Icons | MIT **(bg)** | 24×24, 2 px stroke, ~5,000 icons **(bg)** |
| Fluent System Icons | MIT **(bg)** | Regular and Filled, multiple sizes 12–48 with hand-tuned optical versions **(bg)**; matches Windows 11 |
| SF Symbols | Apple licence: only for Apple platform apps **(bg)** | **Cannot be used.** |

Rules **(bg)**: icons sit on a pixel grid with a safe area (24 px icon → 20 px live area, 2 px padding); one stroke weight throughout; round caps/joins to match a rounded UI; optical sizing, i.e. 16 px icons are drawn separately from 24 px (Fluent) or use 1.5 px stroke at 16 px (Lucide `stroke-width` can be set). Filled variant = selected/active state, outline = default. Icons beside text align to the cap-height centre; pair with text labels in all primary navigation for non-technical users (icon-only is acceptable only for universally known actions with tooltips).

Qt: SVG icons render through `QSvgRenderer`/`QIcon`. Use `currentColor` replacement (read SVG, substitute stroke colour, render to QPixmap at devicePixelRatio) so icons follow theme tokens. Cache pixmaps per (name, size, colour, dpr). Render at integer logical sizes (16/20/24) to keep strokes crisp.

## 5. Elevation, borders, radius
- Flat/hairline design (Linear, Vercel Geist, Radix): surfaces are separated by **1 px low-contrast borders** (step 6) and small lightness changes, with shadows reserved for layers that float (menus, popovers, dialogs). This is cheaper to render and simpler in Qt.
- Elevation scale: 0 (page), 1 (card: border only), 2 (raised: border + subtle shadow), 3 (popover/menu: shadow 0 8 24 rgba(0,0,0,.12) plus border), 4 (modal dialog + scrim). Light-mode shadows should be layered (two shadows: tight and wide) and low opacity; Material's umbra/penumbra/ambient model is the reference **(bg)**.
- Radius scale: 2 (tags/checkbox), 4 (inputs, buttons), 6–8 (cards, panels), 12 (dialogs); use `full` pill only for badges. Windows 11 uses 4 px (controls) and 8 px (overlays/windows) **(bg)**. Nested radii: inner = outer − padding.
- 1 px borders must be physically 1 px: on a 125%/150% display, draw at device pixels (see §9) or the hairlines blur.
- Neomorphism (soft extruded shadows) fails contrast and affordance rules; do not use.

## 6. Dark mode done right
- Not pure black: Material recommends surfaces around #121212 **(bg)**; most polished apps use L ≈ 0.15–0.25 in OKLCH (Linear and Vercel are near-black but tinted) **(bg)**. Pure black with white text causes halation and harsh contrast for people with astigmatism **(bg)**; for long sessions, soften.
- Elevation by lightness: higher layers are *lighter* (Material overlays white at 5–16% by elevation) **(bg)**. Shadows are barely visible in dark mode, so use lightness plus border.
- Text: primary text about 87–92% white-equivalent rather than 100% **(bg)**; secondary about 60–70%. Check with APCA, since WCAG 2 over-states contrast of mid-grey text on dark.
- Accents: reduce chroma and raise lightness (Radix dark step 9 is brighter/less saturated than the light one); never reuse the light-theme hex.
- Status colours need separate dark values. Scanned page thumbnails are white paper on dark UI; put them on a mid-dark neutral matte with a hairline so they do not glare. Offer "dim page previews" as an option (unverified benefit).
- Provide light, dark, and follow-system. Qt 6.5+ exposes `QStyleHints.colorScheme()` and a `colorSchemeChanged` signal; Qt 6.8 adds `setColorScheme` **(bg, verify)**.

## 7. Data-viz of status (job progress, page states)
- A page-state strip in Kontrol (thousands of thumbnails) needs ≤ 5–6 states, each with distinct colour **and** shape/icon/pattern: OK, split-here, uncertain, manually cut, error, skipped.
- Use colour-blind-safe ramps (Okabe-Ito palette is the standard **(bg)**). Use sequential single-hue ramps for ordered quantities such as OCR confidence; diverging only for signed values.
- Progress: determinate bars with a numeric label ("312/640 sayfa"); never an unlabeled spinner longer than ~1 s. Mini-map/overview of the 800 pages should show state ticks at ≥ 3:1 against its track.
- Categories ≤ 6 colours; beyond that, use labels or position.

## 8. Design tokens architecture
- Three tiers: primitive (raw values: `blue.9 = #3E63DD`), semantic (`color.accent.solid -> blue.9`), component (`button.primary.bg -> color.accent.solid`). Themes swap only the primitive→semantic mapping.
- Source of truth: one JSON file in the **W3C Design Tokens Community Group format** (DTCG; `$value`, `$type`, `$description`, aliases like `{color.blue.9}`; draft, stable format version in 2025 **(bg)**). Tools: Style Dictionary can transform it **(bg)**.
- For Python: a small generator reads the JSON and emits (a) a `Tokens` dataclass for QPainter code, (b) a rendered QSS string from a template (`{{color.surface.1}}` placeholders, Jinja2 or `string.Template`). That substitutes for CSS variables, which QSS lacks.
- Also emit spacing, radius, type scale, durations (fast 100 ms, normal 150–200 ms) and easing tokens, even if used only in code animations.
- Contrast test in CI over token pairs (see §1.5).

## 9. What makes UI feel "premium" (concrete techniques)
Reference products: Linear, Raycast, Things 3, Arc, Notion, Vercel Geist. Common, observable techniques **(bg: derived from using/inspecting these products and public design write-ups; no primary source fetched)**:
1. **Restrained accent**: one accent colour used only for primary action, selection and focus; everything else is neutral.
2. **Layered surfaces** with tiny lightness steps (page → panel → card) instead of heavy borders or shadows.
3. **Consistent 1 px hairlines** at low contrast; dividers are removed wherever spacing can do the job.
4. **Crisp micro-typography**: 12–13 px medium-weight labels, 11 px uppercase-free meta text, tabular figures, no more than 3 sizes per screen.
5. **Visible, consistent focus states**: 2 px ring in accent with 2 px offset (Geist and Radix do this); keyboard users are first-class. WCAG 2.2 AAA asks for a focus indicator with ≥ 3:1 contrast and ≥ 2 px thickness **(bg)**.
6. **Fast, short motion**: 100–200 ms ease-out for hover and state changes; no bounce; honour reduced-motion.
7. **Keyboard-first**: command palette, shortcut hints shown inline in menus and tooltips (Raycast, Linear).
8. **Empty states and microcopy** with clear next actions; consistent iconography; no ornamental gradients.
9. **Density with air**: tight rows but generous group spacing, aligned to the grid.
10. **State completeness**: every control has rest, hover, pressed, focus, disabled, selected, error designs.

## 10. Qt/PySide6 feasibility

### 10.1 What QSS can and cannot do (from Qt Style Sheets behaviour, bg; the doc.qt.io page was unreachable)
- **Can**: colours, `border`, `border-radius`, `padding/margin`, fonts, `qlineargradient/qradialgradient/qconicalgradient` backgrounds, `rgba()` colours, pseudo-states (`:hover`, `:pressed`, `:checked`, `:focus`, `:disabled`), sub-controls (`::item`, `::indicator`, `::handle`, `::section`), dynamic properties for selectors (`[state="error"]`), image/`url()` assets.
- **Cannot**: `box-shadow`/`text-shadow`, transitions/animations, CSS variables or `calc()`, `filter`/`backdrop-filter`, per-corner complex shapes, `:focus-visible`-style keyboard-only focus, fine control of some native elements (menus' shadows, scrollbar animation), `letter-spacing` and OpenType features.
- Dynamic property changes need re-polish: `widget.style().unpolish(w); widget.style().polish(w)`.
- Performance: a global stylesheet routes all widgets through `QStyleSheetStyle`, which is slower on huge widget counts; large tables should use `QStyledItemDelegate` painting rather than styled cell widgets.
- Workarounds: shadows via `QGraphicsDropShadowEffect` (CPU-rasterised, blur is expensive; effect forces off-screen rendering of the widget and children, and cannot be nested well; fine on a handful of static cards/dialogs, bad on scrolling lists) or by painting a pre-rendered 9-patch shadow pixmap in `paintEvent` (cheap, recommended). Animation via `QPropertyAnimation` on a custom `Property` (e.g., hover progress) with the widget repainting.

### 10.2 Approaches compared
| Approach | Pros | Cons |
|---|---|---|
| Pure QSS (token-templated) | Fast to write, hot-reloadable, themeable by regenerating string | No shadows/animation; subtle quirks; slower with many widgets |
| QSS + custom-painted widgets (QPainter) for key components (buttons, cards, chips, status badges, nav rail, toggles) | Full control: antialiased hairlines, hover tweens, shadows, focus rings | More code; must handle a11y (`accessibleName`), DPI, keyboard focus manually |
| `QProxyStyle` | Tweak metrics (`pixelMetric`), icons, focus rect, standard-pixmap while keeping native behaviours; cheap | Cannot restyle shapes broadly without reimplementing drawing |
| Full `QStyle` subclass | Deepest control, fastest at runtime | Large effort (every control element); Qt-version fragile |
| Fusion + `QPalette` | Consistent cross-platform base, palette-driven, supports dark | Dated look without QSS/painting help |

Recommendation: **Fusion base style + token-generated QPalette + a thin QSS layer for layout/spacing/borders + custom-painted widgets for a short list of signature components + QProxyStyle for metrics/focus-ring**. Qt 6.7+ also ships a `windows11` style **(bg, verify)** that could be the base on Windows, but Fusion is predictable on all three platforms.

### 10.3 High-DPI, fonts, runtime theming
- Qt 6 enables high-DPI scaling by default; the default rounding policy is `PassThrough`, so fractional scales (125%, 150%) are honoured **(bg)**. Hairlines: draw rects at `x + 0.5` in logical coordinates or compute in device pixels using `devicePixelRatioF()` to keep 1 px borders crisp; test at 100/125/150/200%. Provide `@2x`-independent assets (SVG) only.
- Bundle fonts: `QFontDatabase.addApplicationFont(path)` (works from files or via `QResource`/`importlib.resources`); call before creating widgets; read family name from `QFontDatabase.applicationFontFamilies(id)`. Windows font weight mapping of variable fonts through Qt can be unreliable; **static per-weight TTFs (Regular, Medium, SemiBold) are the safe choice** **(bg)**. Set app default with `QApplication.setFont()`, and set hinting preference (`QFont.PreferFullHinting` vs `PreferNoHinting`) per screenshot tests, since Windows ClearType rendering affects crispness.
- Runtime theming: keep a `ThemeManager` that holds the active token set; on switch, regenerate QPalette + QSS (`app.setStyleSheet(...)`) and emit a `themeChanged` signal for custom-painted widgets to repaint and for icon caches to flush. Follow OS via `styleHints().colorScheme()` signal (6.5+) **(bg)**. Avoid per-widget `setStyleSheet` calls; they are slow and fragment the rules.
- Accessibility: Qt exposes UI Automation on Windows, so set `accessibleName/Description` on every custom widget; ensure focus order and visible focus; support Windows High Contrast by respecting `QPalette` when the system reports forced colours (partial; unverified).

## 11. Reference Qt apps and libraries
- **Krita** (KDE, GPL): highly customisable dark/light themes, dense pro UI; good reference for docker/panel density **(bg)**.
- **OBS Studio 30+**: Qt 6 with a refreshed "Yami"/"Rachni" theme set (QSS with a variables-like preprocessing step — OBS themes use a `.obt` theme format with variables, resolved before QSS is applied) **(bg, unverified detail)**. Closest precedent for token-templated QSS in a large Qt app.
- **Telegram Desktop**: fully custom-painted widgets (its own UI toolkit on Qt), smooth animations, crisp at all DPIs; shows the ceiling of the custom-paint route **(bg)**.
- **KDE apps / Breeze**: a real `QStyle` plugin with a coherent token-like palette scheme **(bg)**.
- **qt-material** (MIT **(bg)**): Material-style QSS generator for PySide/PyQt via XML theme files and Jinja templates; good proof of the template approach, but a Material look is heavy for our density **(bg)**.
- **PyQt-Fluent-Widgets** (zhiyiYo): Fluent-style widgets; **licence GPLv3 for non-commercial projects, commercial licence required otherwise** [4]; its `LICENSE` file is GPLv3 [5]; a PySide6 variant exists but no separate licence is stated on the page [4].

### Licence check: PyQt-Fluent-Widgets vs our AGPL
- GPLv3 §13 expressly permits linking/combining GPLv3 code with AGPLv3 code; the combined work is then governed by AGPLv3 for the network-use clause **(bg: standard FSF position)**. So a GPLv3 dependency is *technically compatible* with an AGPL app.
- Issues: (1) the README frames GPLv3 as the "non-commercial" option and sells a commercial licence [4]; ambiguity for chambers of commerce deployments (public bodies) → legal risk, unverified. (2) It bundles Fluent icons/assets whose provenance/licensing would also need auditing **(unverified)**. (3) Its look is opinionated Windows 11 Fluent; theming deeper than its API allows is hard. (4) PyQt variant depends on PyQt (GPL); the PySide6 branch is needed to keep PySide's LGPL stack.
- **Recommendation: do not depend on it.** Use it only as a visual reference; implement our own small widget kit.

## Rules we should adopt for Evrakçı

1. All colours come from a single DTCG-format JSON token file (primitive → semantic → component); no hex literals in widget code or QSS templates. Enforce with a grep test.
2. Palettes are generated in OKLCH offline, as 12-step ramps for neutral + accent + 4 status hues, with the Radix role mapping (1–2 bg, 3–5 component, 6–8 borders, 9–10 solid, 11–12 text).
3. Neutrals are tinted toward the accent hue at OKLCH chroma 0.005–0.02; no #000000 or #FFFFFF backgrounds in either theme. Page-preview matte is a neutral, untinted grey.
4. Every text/background token pair is unit-tested: body text ≥ 7:1 WCAG and APCA |Lc| ≥ 75 (≥ 90 for ≤ 13 px); secondary text ≥ 4.5:1; UI component boundaries and focus rings ≥ 3:1; in both themes.
5. Status is never colour-only: each state has a unique icon, a Turkish text label, and a colour; verify with a colour-blind simulation (protanopia, deuteranopia, tritanopia) in screenshot review.
6. Bundle one OFL UI font (test Inter vs IBM Plex Sans vs Atkinson Hyperlegible Next on İıĞğŞş and on 1366×768); ship static Regular/Medium/SemiBold TTFs and the OFL text; use Segoe UI only as a non-bundled system fallback.
7. Type scale in whole pixels: 12 / 14 (default) / 16 / 20 / 24; no text below 12 px; line height 1.4–1.5 body; prose measure ≤ 70 characters; tabular figures on all numeric columns.
8. Provide a user-facing UI scale (100/115/130%) and three densities (row heights 40/32/28); no interactive target under 24 px, primary targets ≥ 32 px.
9. Spacing only from {4, 8, 12, 16, 24, 32, 48}; radius only from {2, 4, 8, 12}; a lint test scans QSS/painter code for other values.
10. Surfaces are separated by 1 px device-pixel hairlines and small lightness steps; shadows only on menus, popovers and dialogs, painted from cached 9-patch pixmaps (not `QGraphicsDropShadowEffect` on scrolling content).
11. Dark mode: page ≈ OKLCH L 0.18, panels 0.22, raised 0.26, popovers 0.30; accents re-derived for dark (lower chroma), primary text 88–92% white-equivalent; follow OS colour scheme by default with manual override.
12. Icons: one set only (Lucide, ISC, as base), 16/20/24 px logical sizes, 1.5–2 px stroke consistently, recoloured from tokens at runtime, pixmaps cached per DPR; text labels beside icons in primary navigation; no SF Symbols.
13. Every interactive widget has designed rest/hover/pressed/focus/disabled/selected/error states; the keyboard focus ring is 2 px accent with ≥ 3:1 contrast and visible on all backgrounds including thumbnails.
14. Motion: 100–200 ms ease-out for hover/selection tweens, none for data changes in tables; respect OS reduced-motion; no animation longer than 250 ms.
15. Accent used only for primary action, selection, and focus; at most one filled primary button per view.
16. Architecture: Fusion base + token-generated `QPalette` + templated QSS + QProxyStyle (metrics, focus) + custom-painted signature widgets; one `ThemeManager` with a `themeChanged` signal; never call per-widget `setStyleSheet` in hot paths.
17. Test matrix: screenshots in light/dark × 100/125/150/200% DPI × 1366×768/1920×1080 for each of the six tabs; hairline crispness checked visually.
18. Do not add PyQt-Fluent-Widgets (GPLv3/commercial [4][5]) or any dependency that requires PyQt instead of PySide6; record all asset licences (fonts, icons) in a `THIRD_PARTY.md`.

## Qt/PySide6 feasibility notes (summary)
- Feasible in QSS: flat, hairline, token-driven theming; light/dark switch by regenerating stylesheet + palette.
- Needs custom painting: shadows, hover tweens, status badges, thumbnail-timeline cells (use `QStyledItemDelegate`/custom `QAbstractItemView` painting; thousands of items must not be widgets), focus rings with offset, toggle switches.
- Risks: variable-font weights on Windows; OpenType feature (`tnum`) API availability by Qt version; dynamic-property re-polish; effects cost on low-end office PCs; fractional-DPI hairline blur. Prototype each on a low-spec Windows machine early.

## Sources (accessed 2026-11-12 unless noted)
- [1] https://github.com/rsms/inter — Inter: OFL-1.1, tabular numbers, variable font.
- [2] https://github.com/googlefonts/atkinson-hyperlegible-next — Atkinson Hyperlegible Next: OFL-1.1, 6 weights, archived.
- [3] https://github.com/lucide-icons/lucide — Lucide: ISC licence; icon count.
- [4] https://github.com/zhiyiYo/PyQt-Fluent-Widgets — GPLv3 for non-commercial, commercial licence otherwise; PySide6 branch.
- [5] https://github.com/zhiyiYo/PyQt-Fluent-Widgets/blob/PySide6/LICENSE — GPLv3 text.
- Not reachable from the sandbox (host not in allowed network): radix-ui.com/colors, doc.qt.io (Qt Style Sheets reference), material.io, w3.org, apcacontrast docs. All **(bg)** items should be re-verified at: Radix Colors docs "Understanding the scale"; Qt "Qt Style Sheets Reference" and "High DPI" pages; WCAG 2.2 SC 1.4.3, 1.4.11, 2.5.8, 2.4.13; APCA readability criterion; W3C DTCG format spec; Material 3 colour/HCT docs; SIL OFL FAQ; Microsoft Segoe UI font redistribution terms.
