# 06 — Visual design craft, and what is achievable in Qt/PySide6

**Research caveat (updated 2026-11-12 after a verification pass).** The first draft was written while most primary sources were blocked. A second pass fetched Radix, W3C (WCAG 2.2, WCAG 3 draft, CSS Color 4, DTCG), Qt 6 docs, Lucide, the Material colour-utilities source, APCA source, icon/font repos and the font files themselves. Verified items now carry citations [n]. **(bg)** = "background knowledge, still not verified against a primary source". The Verification log at the end lists what was confirmed, corrected, or left unverified. Several first-draft claims were wrong and were corrected in place (marked "corrected"). Nothing below is invented; where unsure it says "(unverified)".

## TL;DR

- Build colour in a perceptual space (OKLCH or CIELAB/HCT), not HSL. Generate a 12-step neutral and a 12-step accent ramp per hue, then freeze them as primitives. Ship hex values to Qt.
- Use the Radix 12-step role model: steps 1–2 backgrounds, 3–5 component fills (rest/hover/active), 6–8 borders, 9–10 solid fills, 11–12 text [6]. It makes light and dark themes mechanically derivable.
- Tint neutrals slightly toward the brand hue (chroma about 0.005–0.02 in OKLCH). Avoid pure #000 and #FFF in both themes.
- Contrast: WCAG 2 ratios (4.5:1 body, 3:1 large text and UI components) are the audit floor [7][8]. Use APCA Lc values as a second check [12], because WCAG 2 misjudges dark mode and thin type **(bg)**; APCA is not a W3C standard and the WCAG 3 draft says its contrast algorithm is "yet to be determined" [13]. For our older users, aim above the floor: at least 7:1 for primary text.
- Never signal status by colour alone. Pair every status colour with an icon and a text label. Colour-blind safety is a hard requirement for "nothing silently wrong".
- Type: one UI family, bundled (OFL). Inter, IBM Plex Sans and Atkinson Hyperlegible Next are all strong candidates: every glyph-tested font has ı İ ş Ş ğ Ğ ç ö ü [21]. Plex has tabular digits by default; Inter and Atkinson have a `tnum` feature [21]. Base size 13–14 px, a modular scale of about 1.125–1.2, line height about 1.4–1.5.
- Spacing on a 4 px base with 8 px rhythm. Radius scale of three or four steps (4/6/8/12). Hairline 1 px borders define surfaces; shadows only for floating layers.
- Dark mode: surfaces at about L 0.18–0.28 in OKLCH, rising with elevation. Desaturate accents. No pure black.
- "Premium" is mostly restraint: hairlines, layered surfaces, one accent, crisp small type, strong focus rings, zero decorative gradients.
- Qt reality: QSS cannot do shadows, transitions or variables. Plan for a token-driven QSS template generator plus a small custom-painted widget layer (QPainter) for the hero components. Avoid PyQt-Fluent-Widgets as a dependency (GPLv3 for non-commercial use, paid licence otherwise, PySide6 branch included [30]; see licence analysis).

## 1. Colour systems

### 1.1 Perceptual spaces
- **HSL** lightness is not perceptual: yellow at L 50% looks far brighter than blue at L 50%. Ramps built in HSL have uneven contrast between steps.
- **CIELAB (L\*a\*b\*)** is roughly perceptual in lightness; hue shifts in blue are known artefacts **(bg)**.
- **OKLab/OKLCH** (Björn Ottosson, 2020) fixes most hue drift and is specified, with `oklab()`/`oklch()` notations, in CSS Color Module Level 4 [29] (a W3C Candidate Recommendation Draft, 3 Nov 2026). L is 0–1, C is chroma (about 0–0.4), H is hue in degrees **(bg)**. Practical benefit: equal L steps give roughly equal perceived steps, so one lightness curve can be reused across hues.
- **Material 3 HCT** = hue and chroma from CAM16 plus CIELAB L\* as "Tone" (0–100) [14]. A `TonalPalette` is one hue and chroma varied over tone [14]. The reference light scheme reads tones 10, 20, 30, 40, 50, 60, 80, 90, 95, 99, 100 from its palettes [14]; tones 0 and 70 of the usual 13-tone list were not seen in the source **(bg)**. Contrast is computed from Y, which maps to L\* [14]. We computed WCAG ratios over tone pairs (script in the Verification log): a tone difference of 40 gives at least 3.17:1, and a difference of 50 gives at least 4.48:1 (worst case T50 vs T100), so **corrected**: 40 is a safe 3:1 rule, 50 is only about 4.5:1; use a difference of 52 or more for a strict 4.5:1 (we measured 4.82 at 52). Rule for us: pick text and background tones at least 55 apart (min 5.37:1) for body text.
- Qt has no OKLCH support. Generate palettes offline (a small Python script using `colour-science` or hand-coded OKLab maths) and commit the resulting hex tokens. Do not compute at runtime.

### 1.2 Radix Colors 12-step scale (role of each step) [6]
Radix says each of the 12 steps "was designed for at least one specific use case" [6]:

| Step | Role |
|---|---|
| 1 | App background |
| 2 | Subtle background (sidebars, striped rows, cards) |
| 3 | UI element background (rest) |
| 4 | UI element background (hover) |
| 5 | UI element background (active/selected) |
| 6 | Subtle borders and separators |
| 7 | UI element border and focus rings |
| 8 | Hovered UI element border |
| 9 | Solid background (highest chroma, the "pure" colour) |
| 10 | Hovered solid background |
| 11 | Low-contrast text |
| 12 | High-contrast text |

Radix states that steps 11 and 12 "are guaranteed to Lc 60 and Lc 90 APCA contrast ratio on top of a step 2 background from the same scale" [6]. Note a small inconsistency inside Radix: the overview table gives step 7 as "UI element border and focus rings", but the detailed text says step 8 is for "stronger borders on interactive components and focus rings" [6]; we use step 8 for focus rings. Step 9 has the highest chroma; most step 9 colours take white text, but Sky, Mint, Lime, Yellow and Amber take dark text [6]. Licence: MIT (Radix Colors repo LICENSE, and README "Licensed under the MIT License") [6a]. The takeaway for us: define roles, not colours. A table row hovering in Değerler uses step 3 → 4, a selected row step 5 with a step 7 border, and so on. Radix also ships "alpha" variants of each step so overlays work on any background; in Qt we can use `rgba()` in QSS for these.

### 1.3 Neutral tinting
Neutrals with a hint of the brand hue (Radix's Slate, Mauve, Sage pairings; Tailwind's slate/zinc/stone) feel more cohesive than pure grey **(bg)**. Rule of thumb: chroma 0.005–0.02 in OKLCH, same hue as the accent (or a complementary muted hue). Pure grey next to a coloured accent looks dead, but too much tint reads as a colour cast on scanned-document previews, which matters for us because staff judge page content on the page background. Keep the page-preview surface neutral grey or dark.

### 1.4 Semantic tokens and status colours
- Layers: **primitive** (blue-9) → **semantic** (`accent.solid`, `text.primary`, `status.error.fg`) → **component** (`button.primary.bg`). Code uses only semantic/component names.
- Status set for Evrakçı: success (OK/accepted), warning (needs check), error (failed/cut missing), info (neutral hint), plus "unreviewed/pending". Each needs fg, bg-subtle, border, and solid variants.
- Status must be encoded redundantly: colour + icon shape + word (for example a check circle, a triangle and an octagon, with "Onaylandı", "Kontrol et", "Hata"). About 8% of men have red-green colour deficiency **(bg)**; red/green alone is forbidden.
- Prefer a blue-orange pair over red-green for good/bad where a binary is needed.

### 1.5 Contrast: WCAG 2 vs APCA
- WCAG 2.2 (confirmed): text 4.5:1 (SC 1.4.3, AA) [7]; 7:1 (SC 1.4.6, AAA), with 4.5:1 for large-scale text [11]; large text is defined in points: 18 pt, or 14 pt bold [7] (our earlier px figures, 24 px and 18.66 px bold, are the CSS-pixel equivalents at 96 dpi, **(bg)** arithmetic); large text needs 3:1 under 1.4.3 [7]. UI components and states need at least 3:1 against adjacent colours (SC 1.4.11), except inactive components [8]. WCAG 2.2 added minimum target size 24×24 CSS px (SC 2.5.8, Level AA, with a spacing exception) [9] and Focus Appearance (SC 2.4.13, Level AAA) [10]. Note "CSS pixels" are logical pixels, which is what Qt uses at 100% scale.
- WCAG 2 weaknesses: ignores font weight and size beyond a binary, over-rates mid-dark text on dark backgrounds, and under-rates thin light-on-dark text **(bg)**.
- APCA outputs Lc (about 0–106, negative for light-on-dark). Status **corrected**: the SAPC-APCA repo describes APCA as "a new method for predicting contrast for use in emerging web standards (WCAG 3)" and its Readability Criterion as a work-in-progress draft [12]; the actual WCAG 3.0 Working Draft of 10 Sept 2026 does not name APCA and says "The contrast algorithm used in WCAG 3 is yet to be determined" [13]. So APCA is a candidate and a design aid, not a standard.
- The simple Lc ladder (Lc 90 / 75 / 60 / 45 / 30 / 15) is the "Bronze Simple Mode" and could not be fetched from the primary page, so it stays **(bg)**. What is verified from the APCA library docs and source [12]: (a) the font lookup table (May 2022) says primary reading text should "meet or exceed" the table values; for body text add Lc 15 to any value under Lc 75; sub-fluent text may drop by Lc 15 but never below Lc 30; non-fluent spot text (disabled, placeholder, copyright) may drop by Lc 25 but never below Lc 30; fonts above 24 px with weight 300+ cap at Lc 90 [12]. (b) The lookup matrix in `apca-w3.js` gives minimum Lc by font size and weight; for weight 400: 24 px needs Lc 60, 21.75 px Lc 65, 18 px Lc 75, 16 px Lc 90, 15 px Lc 100, 14 px Lc 110; at weight 500: 16 px Lc 75, 15.5 px Lc 90, 14 px Lc 105; at weight 600: 14.8 px Lc 80, 14 px Lc 95, 13 px Lc 105; at weight 700: 14 px Lc 75 [12]. Corrected consequence: 14 px body text needs about Lc 110 at weight 400, Lc 105 at 500 and Lc 95 at 600; black on white is only about Lc 106, so a 14 px/400 body is out of the table's "fluent reading" range. Either use 15-16 px at weight 400 with Lc 90, or 14 px at weight 600 with Lc 95, or accept that 14 px is secondary text.
- Rule for us: verify every text/background pair with both. Legal/audit floor is WCAG AA; design target is WCAG ≥ 7:1 for body text and APCA Lc at or above the lookup-matrix value for the size and weight actually used (for example 16 px/400 needs Lc 90, 14 px/600 needs Lc 95), never below Lc 75 for readable text. Disabled text may be lower but must stay readable (≥ 3:1, and APCA says never below Lc 30 [12]); never use disabled styling to hide information.
- Automate: a pytest that loads the token file and asserts every declared pair meets its threshold in both themes.

## 2. Typography

### 2.1 Scales
- Modular scale: size_n = base × ratio^n. Common ratios: 1.125 (major second), 1.2 (minor third), 1.25 (major third). Dense desktop UIs need a small ratio (≤ 1.2), because there is little space for large jumps.
- Suggested scale at base 14 px, ratio about 1.15–1.2, rounded to whole pixels: 11 (caption/meta), 12 (secondary), 14 (body), 16 (emphasis/section), 20 (page title), 24 (rare display). Whole-pixel sizes are crisp at 100% scaling on Windows.
- Windows/Fluent reference (unchanged, not fetchable in this pass): Windows type ramp is Caption 12, Body 14, Body Strong 14 semibold, Subtitle 20, Title 28, Display 68 (effective pixels, Segoe UI Variable) **(bg)**. Material 3 body-medium is 14 sp, body-large 16 sp **(bg)**. Our users are older: **minimum 12 px for anything readable, 14 px default body, and a user-selectable scale (100/115/130%)**.
- Line height: 1.4–1.5 for body; 1.2–1.3 for headings; table rows are driven by row height (see spacing), not leading. Measure (line length) 45–75 characters for prose such as the Rehber tab; cap Rehber text width at about 70 characters.
- Weights: use only 400, 500 or 600, and 700 sparingly. Variable fonts allow 450–550 fine-tuning, but Qt handles named weights more reliably (see §9).
- **Tabular figures** (`tnum`) are mandatory for page numbers, counts, amounts and dates in tables so columns align. Qt can request OpenType features via `QFont::setFeature(tag, value)`, which is marked "since 6.7" (same for `setVariableAxis`, `unsetFeature`) [25]. Qt style sheets have no OpenType-feature property [22], so `tnum` must be set in code on a `QFont`. Safer fallback: choose a font whose default digits are tabular. Measured from the font files [21]: IBM Plex Sans (all ten digits 600/1000 em wide), Noto Sans (all 572/1000) and Source Sans 3 (all 472/1000) have equal-width default digits; Inter and Atkinson Hyperlegible Next default to proportional digits and need `tnum` (both have the feature) [21].
- Letter-spacing: the Inter variable font in Google Fonts has an `opsz` axis (optical size) alongside `wght` [21]; at UI sizes use default tracking. Do not apply negative tracking to 12–14 px text. Qt supports `QFont::setLetterSpacing` [25] and, **corrected**, the QSS reference does list a `letter-spacing` property (type Length) [22].

### 2.2 Font candidates (bundling, licence, Turkish)
Turkish needs ı, İ, ğ/Ğ, ş/Ş, ç, ö, ü, with correct dotted/dotless capitals. All Latin Extended-A fonts below cover these; confirm with a glyph test string ("İıĞğŞşÇçÖöÜü ISIK ığdır").

| Font | Licence | Notes |
|---|---|---|
| Inter | SIL OFL 1.1; "Inter" is a Reserved Font Name [1][21] | Variable and static weights, tabular numbers, slashed zero [1]; v4.001 variable font has `opsz` and `wght` axes, features `tnum`, `zero`, `case`, `cv11`, `ss01`, `ss02` [21]. Turkish: **glyph-verified** ı İ ş Ş ğ Ğ ç Ç ö Ö ü Ü â î û all present [21]. Default digits are proportional (need `tnum`). Best all-round UI choice. |
| Atkinson Hyperlegible Next | SIL OFL 1.1, no Reserved Font Name stated [2][21] | Designed by the Braille Institute for low vision; 6 weights with italics [2]. Repo is archived read-only [2]. Turkish: **glyph-verified** all Turkish letters present, plus a `locl` language system for Turkish (TRK) [21]. **Corrected**: it does have `tnum` and `pnum` features [21] (default digits proportional). Variable font is only ~115 KB [21]. Excellent legibility for older users. |
| IBM Plex Sans | SIL OFL 1.1, Reserved Font Name "Plex" [21][21a] | Turkish **glyph-verified** [21]. Default digits are tabular (all 600/1000 em); it has `zero`, `onum`, `lnum`, `ss01`, `ss02` but no `tnum`/`pnum` feature because tabular is already the default [21]. Slightly "technical" tone. Variable `wght`+`wdth` (Google Fonts build 3.201) [21]. |
| Noto Sans | SIL OFL 1.1, no Reserved Font Name stated [21] | Turkish **glyph-verified** [21]; default digits tabular (572/1000), has `tnum` and `pnum` [21]. Large file (~2 MB variable) [21]. Maximal script coverage across Latin, Greek, Cyrillic; a little wide **(bg)**. Safe fallback. |
| Source Sans 3 | SIL OFL 1.1, Reserved Font Name "Source" [21][21a] | Turkish **glyph-verified** plus Turkish `locl` language system [21]; default digits tabular (472/1000) [21]; variable `wght` ~650 KB [21]. Compact, good at small sizes **(bg)**. |
| Segoe UI / Segoe UI Variable | Proprietary Microsoft; ships with Windows, **not redistributable** **(bg)** | Use as the *system* fallback on Windows only (`font-family` list), never bundle. |
| SF Pro | Apple licence, restricted to Apple platforms **(bg)** | Do not bundle. |

OFL practicalities: the Inter README quotes the OFL: licensed fonts may be "used, studied, modified and redistributed" and "sold with any software", provided that reserved names are respected, and the font itself "cannot be released under any other type of license" [1]. The OFL.txt files confirm the Reserved Font Name clause (modified versions must not use the RFN) [21]. Ship the OFL text and copyright notice alongside. Compatibility with an AGPL app as a separate asset (fonts are data, not linked code) is **(bg)**, not a legal opinion.

**Recommendation to test**: Inter (default UI), with Atkinson Hyperlegible Next as an optional "high legibility" user setting. Both OFL and both Turkish-complete [21]. If we want tabular digits with zero code, IBM Plex Sans or Source Sans 3 are the zero-effort options. Run an A/B at 13/14 px on a 1366×768 panel before deciding.

## 3. Spacing and density
- 4 px base unit, 8 px rhythm: 4, 8, 12, 16, 24, 32, 48. Material uses an 8 dp grid with 4 dp for small components/icons **(bg)**; Fluent uses 4 px multiples **(bg)**.
- Density scales: Material defines density -1…-3 in 4 dp steps (compact rows 48→40→36→32 dp) **(bg)**. Windows Fluent standard control height is 32 px; compact is 24 px **(bg)**.
- Proposed for Evrakçı (office staff, long sessions, 1366×768 screens): three user-selectable densities. Comfortable (row 40, control 36), Default (row 32, control 32), Compact (row 28, control 28). Never go below 24 px hit height (WCAG 2.2 SC 2.5.8 minimum) **(bg)**; prefer ≥ 32 for primary actions.
- Padding inside controls: horizontal = 2× vertical. Group spacing 16, section spacing 24–32. Use the same few values everywhere; arbitrary values (5, 7, 10 px) are the main cause of "amateur" feel.
- Align text baselines of labels and inputs; align numeric columns right (tabular figures).

## 4. Iconography

| Set | Licence | Grid/stroke |
|---|---|---|
| Lucide | ISC [3][17]; a fork of Feather, some icons derive from the Feather project [17] | 24×24 pixel canvas with at least 1 px safe zone, 2 px centred strokes, round joins and caps [16]; "1600+" icons per the repo README [3] |
| Phosphor | MIT (LICENSE and README) [18] | Assets grouped by weight, including a duotone weight [18]; the "6 weights" and 256 grid details remain **(bg)** |
| Tabler Icons | MIT (LICENSE, "Copyright (c) 2020-2026 Paweł Kuna") [19] | Each icon on a 24x24 grid with a 2 px stroke; 6287 icons, 5233 outline (README) [19] |
| Fluent System Icons | MIT (LICENSE, "Copyright (c) 2020 Microsoft Corporation") [20] | Regular and Filled lists in README [20]; the sizes 12-48 and optical-size claim remain **(bg)**. Note the MIT licence covers the icons; Microsoft trademark/branding terms were not checked **(unverified)** |
| SF Symbols | Apple licence: only for Apple platform apps **(bg)** | **Cannot be used.** |

Rules: Lucide's own spec requires a 1 px safe zone (so a 22 px live area on 24, not the 20 px we previously assumed, **corrected**), one 2 px stroke width ("don't mix stroke widths"), round joins, round caps on open paths, centred strokes, and alignment to the pixel grid [16]. Lucide can render at other sizes with `stroke-width` changed **(bg)**, but its spec fixes 2 px at 24 px, so at 16 px a 2 px stroke is proportionally heavy (it renders as 1.33 px in a 16 px box if scaled; arithmetic). Optical sizing (16 px icons drawn separately, Fluent) remains **(bg)**. Filled variant = selected/active state, outline = default. Icons beside text align to the cap-height centre; pair with text labels in all primary navigation for non-technical users (icon-only is acceptable only for universally known actions with tooltips).

Qt SVG notes are engineering advice from background knowledge **(bg)**: SVG icons render through `QSvgRenderer`/`QIcon`. Use `currentColor` replacement (read SVG, substitute stroke colour, render to QPixmap at devicePixelRatio) so icons follow theme tokens. Cache pixmaps per (name, size, colour, dpr). Render at integer logical sizes (16/20/24) to keep strokes crisp.

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
- Provide light, dark, and follow-system. Verified [23]: the `colorScheme` property (`Qt::ColorScheme`) is documented "since 6.5", `colorSchemeChanged(Qt::ColorScheme)` is a signal, `setColorScheme()` is "since 6.8", and `unsetColorScheme()` resets to the system value; the docs warn that overriding is a hint and "not supported on all platforms" [23]. Windows 11 style "supports Windows dark mode" [28]. Qt 6.10 also adds `QStyleHints.accessibility` (high-contrast hint) [23].

## 7. Data-viz of status (job progress, page states)
- A page-state strip in Kontrol (thousands of thumbnails) needs ≤ 5–6 states, each with distinct colour **and** shape/icon/pattern: OK, split-here, uncertain, manually cut, error, skipped.
- Use colour-blind-safe ramps (Okabe-Ito palette is the standard **(bg)**). Use sequential single-hue ramps for ordered quantities such as OCR confidence; diverging only for signed values.
- Progress: determinate bars with a numeric label ("312/640 sayfa"); never an unlabeled spinner longer than ~1 s. Mini-map/overview of the 800 pages should show state ticks at ≥ 3:1 against its track.
- Categories ≤ 6 colours; beyond that, use labels or position.

## 8. Design tokens architecture
- Three tiers: primitive (raw values: `blue.9 = #3E63DD`), semantic (`color.accent.solid -> blue.9`), component (`button.primary.bg -> color.accent.solid`). Themes swap only the primitive→semantic mapping.
- Source of truth: one JSON file in the **W3C Design Tokens Community Group format** (DTCG; `$value`, `$type`, `$description`, aliases like `{color.blue.9}` **(bg for syntax details)**). Status verified [15]: the Design Tokens Community Group announced the first stable version, **Design Tokens Format Module 2025.10, on 28 Oct 2025**, with companion Color Module 2025.10 and Resolver Module 2025.10 [15]. It is a Community Group report, not a W3C Recommendation (W3C Community Groups are not standards-track) **(bg)**. Tools: Style Dictionary can transform it **(bg)**.
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

### 10.1 What QSS can and cannot do (checked against the Qt 6.12 Style Sheets Reference [22])
- **Can** (all appear in the reference [22]): `border`, `border-radius` (clips the background), `outline` with `outline-color/-offset/-style/-radius` (**new finding**, useful for focus rings with an offset), `letter-spacing`, `padding/margin`, `min-/max-width/height`, `qlineargradient`/`qradialgradient`/`qconicalgradient`, pseudo-states (`:hover`, `:pressed`, `:checked`, `:focus`, `:disabled`, `:selected`, `:read-only`, `:alternate` and more), sub-controls, `opacity` (but only for `QToolTip` [22]), `widget-animation-duration` (a style-hint override, available since Qt 5.10 [22]). `rgba()` colours, dynamic-property selectors (`[state="error"]`) and `url()` images are standard QSS **(bg)**; `width`/`height` for images are "supported since Qt 6.13" [22].
- **Cannot** (absent from the property and pseudo-state lists [22]; the page contains no `box-shadow`, `text-shadow`, `transition`, `calc(`, `var(`, `font-feature` or `font-variant`): shadows, transitions, CSS variables, `calc()`, OpenType features, `:focus-visible` (the only focus pseudo-state is `:focus`). `filter`/`backdrop-filter` are not properties (the only match for "filter" is the page's topic search box). The old claim that `letter-spacing` is unsupported was **corrected** above. Per-corner radii are supported (`border-top-left-radius` etc. [22]); "fine control of native elements" remains **(bg)**.
- Dynamic property changes need re-polish: `widget.style().unpolish(w); widget.style().polish(w)`.
- Performance **(bg)**: no performance note was found in the Qt style-sheet pages [22]. The common engineering view is that a global stylesheet routes widgets through `QStyleSheetStyle`, slower on huge widget counts; large tables should use `QStyledItemDelegate` painting rather than styled cell widgets.
- Workarounds: shadows via `QGraphicsDropShadowEffect` or by painting a pre-rendered 9-patch shadow pixmap in `paintEvent` (cheap, recommended). Verified from Qt docs [27]: `QWidget::setGraphicsEffect` "will apply the effect on itself and all its children", and effects are "not supported for OpenGL-based widgets" (`QOpenGLWidget`, `QQuickWidget`); the drop shadow defaults to colour (63,63,63,180), blur radius 1 px, offset 8 px towards the lower right, and its offset is in device coordinates; `QGraphicsEffect` can be disabled with `setEnabled(false)` "on slow platforms, in order to ensure that the user interface is responsive" [27]. **Not found in Qt docs**: any explicit statement that the blur is expensive or CPU-rasterised; that remains **(bg)** (it renders the source to an offscreen pixmap and blurs it). Net: fine on a handful of static cards/dialogs, avoid on scrolling lists, and never put an effect over a thumbnail timeline or any OpenGL widget. Animation via `QPropertyAnimation` on a custom `Property` (e.g., hover progress) with the widget repainting.

### 10.2 Approaches compared
| Approach | Pros | Cons |
|---|---|---|
| Pure QSS (token-templated) | Fast to write, hot-reloadable, themeable by regenerating string | No shadows/animation; subtle quirks; slower with many widgets |
| QSS + custom-painted widgets (QPainter) for key components (buttons, cards, chips, status badges, nav rail, toggles) | Full control: antialiased hairlines, hover tweens, shadows, focus rings | More code; must handle a11y (`accessibleName`), DPI, keyboard focus manually |
| `QProxyStyle` | Tweak metrics (`pixelMetric`), icons, focus rect, standard-pixmap while keeping native behaviours; cheap | Cannot restyle shapes broadly without reimplementing drawing |
| Full `QStyle` subclass | Deepest control, fastest at runtime | Large effort (every control element); Qt-version fragile |
| Fusion + `QPalette` | Consistent cross-platform base, palette-driven, supports dark | Dated look without QSS/painting help |

Recommendation: **Fusion base style + token-generated QPalette + a thin QSS layer for layout/spacing/borders + custom-painted widgets for a short list of signature components + QProxyStyle for metrics/focus-ring**. Qt 6.7 added a Windows 11 style (Qt 6.7 "What's New": "Added Windows 11 style") [28]; the QStyle docs name it `windows11` and say it follows Windows 11 Fluent design [28]; it "supports Windows dark mode" and is the default on Windows 11 [28]. It could be a base on Windows, but Fusion is predictable on all three platforms. `QWidget.setGraphicsEffect` and QSS behave as above regardless of style.

### 10.3 High-DPI, fonts, runtime theming
- Qt 6 enables high-DPI scaling by default; Qt 6 on Windows is "Per-Monitor DPI Aware V2 by default"; the rounding-policy environment variable `QT_SCALE_FACTOR_ROUNDING_POLICY` lists `Round` and `PassThrough (default)`, so fractional scales (125%, 150%) are honoured [26]. The same page notes integer scale factors give the best visuals, "rounding" to 25% increments can also work, and an app with artifacts at fractional scales can call `QGuiApplication::setHighDpiScaleFactorRoundingPolicy()` [26]. The coordinate model is that application coordinates are device-independent [26]. The hairline-at-0.5 advice below is engineering advice **(bg)**. Hairlines: draw rects at `x + 0.5` in logical coordinates or compute in device pixels using `devicePixelRatioF()` to keep 1 px borders crisp; test at 100/125/150/200%. Provide `@2x`-independent assets (SVG) only.
- Bundle fonts: `QFontDatabase.addApplicationFont(fileName)` loads a font file and returns an id, or -1 on failure; "currently only TrueType fonts, TrueType font collections, and OpenType fonts are supported"; `applicationFontFamilies(id)` returns the family names; `addApplicationFontFromData(QByteArray)` loads from memory (useful for resources) [24]. Qt 6.8 adds `addApplicationFallbackFontFamily(script, family)` [24]. "Call before creating widgets" is advice **(bg)**; check the return value is not -1. Qt 6.7 added variable-font axis control (`QFont::setVariableAxis`) [25], but Windows weight mapping of variable fonts through Qt remains unverified; **static per-weight TTFs (Regular, Medium, SemiBold) are the safe choice** **(bg)**. Google Fonts offers these fonts as variable files [21]; static instances would have to be generated from upstream releases or with fontTools instancer. Set app default with `QApplication.setFont()`, and set hinting preference (`QFont.PreferFullHinting` vs `PreferNoHinting`) per screenshot tests, since Windows ClearType rendering affects crispness.
- Runtime theming: keep a `ThemeManager` that holds the active token set; on switch, regenerate QPalette + QSS (`app.setStyleSheet(...)`) and emit a `themeChanged` signal for custom-painted widgets to repaint and for icon caches to flush. Follow OS via the `QStyleHints.colorSchemeChanged` signal (property since 6.5) [23]. Avoid per-widget `setStyleSheet` calls; they are slow and fragment the rules.
- Accessibility: Qt exposes UI Automation on Windows, so set `accessibleName/Description` on every custom widget; ensure focus order and visible focus; support Windows High Contrast by respecting `QPalette` when the system reports forced colours (partial; unverified).

## 11. Reference Qt apps and libraries
- **Krita** (KDE, GPL): highly customisable dark/light themes, dense pro UI; good reference for docker/panel density **(bg)**.
- **OBS Studio 30+**: Qt 6 with a refreshed "Yami"/"Rachni" theme set (QSS with a variables-like preprocessing step — OBS themes use a `.obt` theme format with variables, resolved before QSS is applied) **(bg, unverified detail)**. Closest precedent for token-templated QSS in a large Qt app.
- **Telegram Desktop**: fully custom-painted widgets (its own UI toolkit on Qt), smooth animations, crisp at all DPIs; shows the ceiling of the custom-paint route **(bg)**.
- **KDE apps / Breeze**: a real `QStyle` plugin with a coherent token-like palette scheme **(bg)**.
- **qt-material** (MIT **(bg)**): Material-style QSS generator for PySide/PyQt via XML theme files and Jinja templates; good proof of the template approach, but a Material look is heavy for our density **(bg)**.
- **PyQt-Fluent-Widgets** (zhiyiYo): Fluent-style widgets; **licence GPLv3 for non-commercial projects, commercial licence required otherwise** [4]; its `LICENSE` file is GPLv3 [5]. **Corrected**: the PySide6 branch README does state a licence: "PySide6-Fluent-Widgets adopts dual licenses. Non-commercial usage is licensed under GPLv3. For commercial purposes, please purchase commercial license" [30]. All variants share the package name `qfluentwidgets` [30].

### Licence check: PyQt-Fluent-Widgets vs our AGPL
- GPLv3 §13 expressly permits linking/combining GPLv3 code with AGPLv3 code; the combined work is then governed by AGPLv3 for the network-use clause **(bg: standard FSF position)**. So a GPLv3 dependency is *technically compatible* with an AGPL app.
- Issues: (1) the README frames GPLv3 as the "non-commercial" option and sells a commercial licence [4]; ambiguity for chambers of commerce deployments (public bodies) → legal risk, unverified. (2) It bundles Fluent icons/assets whose provenance/licensing would also need auditing **(unverified)**. (3) Its look is opinionated Windows 11 Fluent; theming deeper than its API allows is hard. (4) PyQt variant depends on PyQt (GPL); the PySide6 branch is needed to keep PySide's LGPL stack.
- **Recommendation: do not depend on it.** Use it only as a visual reference; implement our own small widget kit.

## Rules we should adopt for Evrakçı

1. All colours come from a single DTCG-format JSON token file (primitive → semantic → component); no hex literals in widget code or QSS templates. Enforce with a grep test.
2. Palettes are generated in OKLCH offline, as 12-step ramps for neutral + accent + 4 status hues, with the Radix role mapping (1–2 bg, 3–5 component, 6–8 borders, 9–10 solid, 11–12 text).
3. Neutrals are tinted toward the accent hue at OKLCH chroma 0.005–0.02; no #000000 or #FFFFFF backgrounds in either theme. Page-preview matte is a neutral, untinted grey.
4. Every text/background token pair is unit-tested: body text ≥ 7:1 WCAG and APCA |Lc| at or above the size/weight lookup value [12] (e.g. 16 px/400 ≥ Lc 90, 14 px/600 ≥ Lc 95) and never below Lc 75; secondary text ≥ 4.5:1; UI component boundaries and focus rings ≥ 3:1; in both themes.
5. Status is never colour-only: each state has a unique icon, a Turkish text label, and a colour; verify with a colour-blind simulation (protanopia, deuteranopia, tritanopia) in screenshot review.
6. Bundle one OFL UI font (Inter, IBM Plex Sans and Atkinson Hyperlegible Next are all glyph-verified for İıĞğŞş [21]; choose by A/B on 1366×768); ship static Regular/Medium/SemiBold TTFs and the OFL text; use Segoe UI only as a non-bundled system fallback.
7. Type scale in whole pixels: 12 / 14 (default) / 16 / 20 / 24; no text below 12 px; line height 1.4–1.5 body; prose measure ≤ 70 characters; tabular figures on all numeric columns.
8. Provide a user-facing UI scale (100/115/130%) and three densities (row heights 40/32/28); no interactive target under 24 px, primary targets ≥ 32 px.
9. Spacing only from {4, 8, 12, 16, 24, 32, 48}; radius only from {2, 4, 8, 12}; a lint test scans QSS/painter code for other values.
10. Surfaces are separated by 1 px device-pixel hairlines and small lightness steps; shadows only on menus, popovers and dialogs, painted from cached 9-patch pixmaps (not `QGraphicsDropShadowEffect` on scrolling content).
11. Dark mode: page ≈ OKLCH L 0.18, panels 0.22, raised 0.26, popovers 0.30; accents re-derived for dark (lower chroma), primary text 88–92% white-equivalent; follow OS colour scheme by default with manual override.
12. Icons: one set only (Lucide, ISC, as base), 16/20/24 px logical sizes, one stroke weight consistently (Lucide spec: 2 px on a 24 px canvas with 1 px safe zone [16]; re-check stroke at 16 px), recoloured from tokens at runtime, pixmaps cached per DPR; text labels beside icons in primary navigation; no SF Symbols.
13. Every interactive widget has designed rest/hover/pressed/focus/disabled/selected/error states; the keyboard focus ring is 2 px accent with ≥ 3:1 contrast and visible on all backgrounds including thumbnails.
14. Motion: 100–200 ms ease-out for hover/selection tweens, none for data changes in tables; respect OS reduced-motion; no animation longer than 250 ms.
15. Accent used only for primary action, selection, and focus; at most one filled primary button per view.
16. Architecture: Fusion base + token-generated `QPalette` + templated QSS + QProxyStyle (metrics, focus) + custom-painted signature widgets; one `ThemeManager` with a `themeChanged` signal; never call per-widget `setStyleSheet` in hot paths.
17. Test matrix: screenshots in light/dark × 100/125/150/200% DPI × 1366×768/1920×1080 for each of the six tabs; hairline crispness checked visually.
18. Do not add PyQt-Fluent-Widgets (GPLv3 non-commercial / paid commercial licence, including the PySide6 branch [4][5][30]) or any dependency that requires PyQt instead of PySide6; record all asset licences (fonts, icons) in a `THIRD_PARTY.md`.

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
- [6] https://www.radix-ui.com/colors/docs/palette-composition/understanding-the-scale — 12 steps and use cases; Lc 60/90 statement. Accessed 2026-11-12.
- [6a] https://raw.githubusercontent.com/radix-ui/colors/main/LICENSE and README.md — MIT.
- [7] https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html — SC 1.4.3 (4.5:1; large text 18 pt / 14 pt bold). Accessed 2026-11-12.
- [8] https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html — SC 1.4.11 (3:1).
- [9] https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html — SC 2.5.8 (24x24 CSS px, AA).
- [10] https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html — SC 2.4.13 (AAA; 3:1 change, 2 CSS px perimeter).
- [11] https://www.w3.org/WAI/WCAG22/Understanding/contrast-enhanced.html — SC 1.4.6 (7:1; 4.5:1 large text, AAA).
- [12] https://github.com/Myndex/SAPC-APCA (README) ; https://github.com/Myndex/apca-w3 (README: Font Lookup Table notes; src/apca-w3.js `fontMatrixAscend`, dated May 2022). Accessed 2026-11-12.
- [13] https://www.w3.org/TR/wcag-3.0/ — W3C Working Draft 10 Sept 2026; "contrast algorithm ... yet to be determined".
- [14] https://github.com/material-foundation/material-color-utilities (README; typescript/palettes/tonal_palette.ts, scheme/scheme.ts, contrast/contrast.ts). m3.material.io pages are JavaScript-rendered and returned no text.
- [15] https://www.w3.org/community/design-tokens/ — Format/Color/Resolver Module 2025.10 (28 Oct 2025) and the stable-version announcement.
- [16] https://lucide.dev/guide/design/icon-design-guide — 24x24 canvas, 1 px safe zone, 2 px strokes, round joins/caps.
- [17] https://lucide.dev/license and https://raw.githubusercontent.com/lucide-icons/lucide/main/LICENSE — ISC; Feather-derived icon list.
- [18] https://raw.githubusercontent.com/phosphor-icons/core/main/LICENSE and README.md — MIT.
- [19] https://raw.githubusercontent.com/tabler/tabler-icons/main/LICENSE and README.md — MIT, 24x24, 2 px, 6287 icons.
- [20] https://raw.githubusercontent.com/microsoft/fluentui-system-icons/main/LICENSE — MIT.
- [21] Font files and OFL.txt from https://github.com/google/fonts (ofl/inter, ibmplexsans, atkinsonhyperlegiblenext, notosans, sourcesans3), inspected with fontTools 4.68 (cmap, GSUB features, hmtx digit widths). Upstream: https://github.com/IBM/plex, https://github.com/adobe-fonts/source-sans (LICENSE headers).
- [21a] https://raw.githubusercontent.com/IBM/plex/master/LICENSE.txt and adobe-fonts/source-sans LICENSE.md — Reserved Font Names "Plex" and "Source".
- [22] https://doc.qt.io/qt-6/stylesheet-reference.html (Qt 6.12 page).
- [23] https://doc.qt.io/qt-6/qstylehints.html
- [24] https://doc.qt.io/qt-6/qfontdatabase.html
- [25] https://doc.qt.io/qt-6/qfont.html
- [26] https://doc.qt.io/qt-6/highdpi.html
- [27] https://doc.qt.io/qt-6/qgraphicsdropshadoweffect.html ; https://doc.qt.io/qt-6/qgraphicseffect.html ; https://doc.qt.io/qt-6/qwidget.html (`setGraphicsEffect`)
- [28] https://doc.qt.io/qt-6/whatsnew67.html and https://doc.qt.io/qt-6/qstyle.html — Windows 11 style.
- [29] https://www.w3.org/TR/css-color-4/ — oklab()/oklch() (CRD 3 Nov 2026).
- [30] https://raw.githubusercontent.com/zhiyiYo/PyQt-Fluent-Widgets/PySide6/README.md and master/README.md — GPLv3 non-commercial / commercial licence.
- Still not re-verified (kept **(bg)**): Material 3 type scale and density figures, Windows/Fluent type ramp and control sizes, Segoe UI / SF Pro licence terms, SF Symbols terms, Phosphor/Fluent icon-size details, Okabe-Ito, colour-deficiency prevalence, Radix/Linear/Vercel design practice, Krita/OBS/Telegram/qt-material facts, Qt style-sheet performance, QGraphicsDropShadowEffect cost, WCAG 3 Bronze Simple Mode Lc ladder.


## Verification log (2026-11-12)

Method: pages fetched with curl/WebFetch from the newly allowed hosts; fonts inspected as binary files. Status key: CONFIRMED, CORRECTED (first draft was wrong or imprecise), PARTIAL, UNVERIFIED (tag kept).

| Item | Status | Finding |
|---|---|---|
| Radix 12-step roles | CONFIRMED [6] | All 12 roles match. Minor: overview table says step 7 = "border and focus rings", body text says step 8 = focus rings. |
| Radix Lc 60 / Lc 90 | CONFIRMED [6] | "guaranteed to Lc 60 and Lc 90 ... on top of a step 2 background from the same scale" (steps 11 and 12). |
| Radix licence MIT | CONFIRMED [6a] | MIT, copyright WorkOS. |
| WCAG 4.5:1 / 3:1 / large text | CONFIRMED, units CORRECTED [7][11] | Large text is defined in points (18 pt, 14 pt bold). 24 px / 18.66 px are CSS-pixel conversions of those at 96 dpi (our arithmetic). |
| WCAG 1.4.11 3:1 non-text | CONFIRMED [8] | Excludes inactive components. |
| WCAG 2.5.8 24x24 CSS px | CONFIRMED, AA [9] | Has a spacing exception; 2.5.5 (AAA) uses 44x44. |
| WCAG 2.4.13 focus appearance | CONFIRMED, AAA [10] | 3:1 between focused and unfocused states; area at least a 2 CSS px perimeter. |
| APCA is "WCAG 3 candidate" | CORRECTED [12][13] | APCA repo calls itself a method "for use in emerging web standards (WCAG 3)" with a draft criterion; WCAG 3.0 WD (10 Sept 2026) names no algorithm: "yet to be determined". |
| APCA Lc 90/75/60/45/30/15 ladder | UNVERIFIED | The Bronze Simple Mode / readtech.org pages are not reachable. Verified instead: the Lc 15 / 25 relaxations, Lc 30 floor, Lc 90 cap [12], and the size x weight lookup matrix from source [12]. |
| Our earlier rule "Lc >= 90 for 12-13 px text" | CORRECTED | The matrix needs about Lc 110 for 14 px at weight 400, Lc 105 at 500, Lc 95 at 600, and Lc 105 for 13 px at 600 [12]; hence the new rule: test each size/weight against the matrix. |
| Material HCT definition | CONFIRMED [14] | "CAM16 x L*" per the library README; tone = L*. |
| Material tonal palette tone list | PARTIAL [14] | Scheme source uses 10, 20, 30, 40, 50, 60, 80, 90, 95, 99, 100; 0 and 70 not seen. |
| "Tone gap 40 => 3:1, 50 => 4.5:1" | PARTIAL / CORRECTED (computed) | Own computation over T0-T100: gap 40 min 3.17:1; gap 50 min 4.48:1 (just under 4.5); gap 52 min 4.82; gap 55 min 5.37. Script: Y = ((L+16)/116)^3 for L>8 else L/903.3; ratio = (Y_hi+0.05)/(Y_lo+0.05). |
| DTCG format status | CONFIRMED [15] | First stable version 2025.10 on 28 Oct 2025 (Format, Color, Resolver modules). It is a Community Group deliverable. |
| Lucide grid/stroke | CONFIRMED [16] | 24x24 canvas; 1 px safe zone (not 2 px); 2 px stroke; round caps/joins. |
| Lucide licence | CONFIRMED [17] | ISC, "Copyright (c) 2026 Lucide Icons and Contributors"; the licence page lists icons that originate in Feather. Icon count: README says "1600+". |
| Phosphor licence | CONFIRMED MIT [18] | Details of weights/grid UNVERIFIED. |
| Tabler licence | CONFIRMED MIT [19] | 24x24 grid, 2 px stroke, 6287 icons (5233 outline). Earlier "~5,000" was low. |
| Fluent System Icons licence | CONFIRMED MIT [20] | Size set and optical sizing UNVERIFIED. |
| Inter licence + Turkish | CONFIRMED [1][21] | OFL 1.1, RFN "Inter". All of ı İ ş Ş ğ Ğ ç Ç ö Ö ü Ü â Â î Î û Û in cmap (v4.001 Google Fonts). `tnum` present; default digits proportional. |
| IBM Plex Sans | CONFIRMED [21][21a] | OFL 1.1, RFN "Plex"; Turkish complete; default digits tabular; v3.201. |
| Atkinson Hyperlegible Next | CONFIRMED, CORRECTED [2][21] | OFL 1.1; Turkish complete with TRK language system; has `tnum`/`pnum` (earlier "no stated tabular figures" was wrong). v2.001. |
| Noto Sans | CONFIRMED [21] | OFL 1.1; Turkish complete; tabular default digits; has `tnum`. |
| Source Sans 3 | CONFIRMED [21][21a] | OFL 1.1, RFN "Source"; Turkish complete incl. TRK language system; tabular default digits. |
| Segoe UI / SF Pro / SF Symbols licences | UNVERIFIED | Not in the allowed hosts. Tag kept. |
| QSS supported properties | CONFIRMED, CORRECTED [22] | Supports `outline*`, `letter-spacing`, `border-radius`, gradients, `opacity` (QToolTip only), `widget-animation-duration`. No shadow, transition, variable, calc, font-feature, focus-visible. Earlier claim "no letter-spacing" was wrong. |
| QStyleHints.colorScheme | CONFIRMED [23] | Property since 6.5; `setColorScheme`/`unsetColorScheme` since 6.8; signal `colorSchemeChanged`. |
| QFont.setFeature | CONFIRMED [25] | Since 6.7 (also setVariableAxis). |
| Qt 6 high-DPI | CONFIRMED [26] | Default rounding policy `PassThrough`; Windows PMv2 by default. |
| QFontDatabase.addApplicationFont | CONFIRMED [24] | Returns id or -1; TrueType/TTC/OpenType only; `applicationFontFamilies(id)`. |
| QGraphicsDropShadowEffect cost | PARTIAL [27] | Docs give defaults and "applies to itself and all its children" and no OpenGL widgets; no cost statement found, so "expensive/CPU" stays (bg). |
| Qt windows11 style version | CONFIRMED [28] | Added in Qt 6.7. |
| PyQt-Fluent-Widgets licence | CONFIRMED, CORRECTED [30] | GPLv3 non-commercial / commercial licence; PySide6 branch README says "dual licenses" explicitly (earlier "no separate licence stated" was wrong). |
| OKLCH in CSS | CONFIRMED [29] | CSS Color 4 specifies oklab()/oklch(). |

Items in the Rules section changed as a result: rule 4 (APCA thresholds), rule 6 (font candidates are all Turkish-complete), rule 12 (Lucide safe zone), rule 18 (licence wording). See the edits inline.
