# DESIGN.md tokens against the nearest Fluent token (read-only)

DESIGN.md is not changed by this guide. "Match" = the same number; "Differs" = a deliberate or
open deviation. Fluent values are in tokens.md (with sources and flags).

| Our token (DESIGN.md) | Ours | Nearest Fluent token | Fluent | Verdict |
|---|---|---|---|---|
| spacing scale | 4, 8, 12, 16, 24, 32, 48 | XS S M L XXL XXXL; 48 from the F2 ramp | 4, 8, 12, 16, 24, 32; 48 | Match. We omit 2, 6, 10, 20 |
| rounded.paper | 2 | borderRadiusSmall | 2 | Match |
| rounded.control | 4 | borderRadiusMedium, ControlCornerRadius | 4 | Match |
| rounded.layer (cards, menus, popovers, toasts) | 8 | borderRadiusXLarge, OverlayCornerRadius | 8 | Match for menus, popovers, toasts. Cards and the work layer are in-page containers, where Windows uses 4; ours is 8 by owner decision (A's deviation 3) |
| tooltip radius | 4 | Learn ToolTip exception | 4 | Match |
| rider radius | 3 | none | n/a | Brand element |
| typography.caption | 13 / 18 | caption1 | 12 / 16 | Differs +1 px; still above the Learn minimum (12 regular) |
| typography.body | 15 / 21 | body1 (body2 is 16 / 22) | 14 / 20 | Differs +1 px (Inter runs smaller than Segoe at equal size) |
| typography.section | 17 / 24, 600 | subtitle2 | 16 / 22, 600 | Differs +1; no 17 in Fluent |
| typography.panel | 20 / 28, 600 | subtitle1 | 20 / 28, 600 | Match |
| typography.page | 24 / 32, 600 | title3 | 24 / 32, 600 | Match (letter spacing is ours) |
| weights | 400, 500, 600 | Regular, Medium, Semibold (+ Bold 700) | | Match; the Windows ramp uses only 400 and 600, so our 500 is an extra |
| font family | Inter, Segoe UI Variable, Segoe UI | Segoe UI (web), Segoe UI Variable (Windows 11) | | Differs on purpose (D3, bundled OFL) |
| sizes.control | 32 | text box and dialog button height | 32 | Match (verified) |
| density Sıkı control 28 | 28 | compact control | 24-28 | Unverified |
| sizes.row | 40 | ListViewItemMinHeight | 40 | Match (verified); Sıkı 32 unverified |
| table header | 36 | ListViewHeaderItemMinHeight | 44 | Differs (ours tighter) |
| menu item | 34 | MenuFlyoutThemeMinHeight | 32 | Differs by 2 |
| icon button | 36 | none (app bar compact 40, touch 44) | | No equivalent |
| command bar | 44 | AppBarThemeCompactHeight | 40 | Differs +4 |
| title band | 44 | title bar 32 / 48 | unverified | Ours carries tabs; nearer the tall bar |
| status bar | 28 | none | | No Fluent number |
| checkbox / radio | 20 | 20 | unverified | Plausible |
| scrollbar thin | 9 | ScrollBarSize full 16; thin 2-6 unverified | | Differs |
| slider track | 4 | SliderTrackThemeHeight | 2 | Differs +2 |
| motion.durations | 80, 120, 180, 240 | Faster 100, Fast 150, Normal 200, Gentle 250; Windows 167 / 250 / 333; fade 83 | | Differs: not Fluent steps. Nearest: 80 to 83, 120 to 100, 180 to 167 or 200, 240 to 250 |
| motion.standard | (.2,0,0,1) | EasyEaseMax (.8,0,.2,1) or DecelerateMid (0,0,0,1) | | Differs; ours is a custom decelerate |
| motion.enter | (0,0,0,1) | curveDecelerateMid, Windows direct entrance | (0,0,0,1) | Match |
| motion.exit | (.3,0,1,1) | curveAccelerateMid, Windows gentle exit | (1,0,1,1) | Close, not identical |
| menus 180 ms, toasts 240 ms | | Normal 200, Gentle 250 | | Close |
| focus ring | 2 px outer + 1 px inner, 1 px outside | Stroke Focus1 / Focus2, Thick 2 | white and black pair | Match in concept; offset unverified |
| stroke | 1 px | strokeWidthThin | 1 | Match |
| text / text-2 | `#16201a` / `#4a5550` | Foreground1 / 2 | `#242424` / `#424242` | Role match; ours darker and green-tinted |
| base / layer / card | `#e1e6e3` / `#f3f5f4` / `#ffffff` | Background4-5 / Background3 / Background1 | `#f0f0f0`-`#ebebeb` / `#f5f5f5` / white | Role order matches; ours tinted; Mica is translucent |
| stroke / stroke-soft | `#d8dedb` / `#e6eae7` | Stroke1 / Stroke2 | `#d1d1d1` / `#e0e0e0` | Role match |
| edge (3:1) | `#7a8680` | StrokeAccessible | `#616161` | Ours is lighter; keep the D10 3:1 test as the judge |
| hover / pressed / selected | `#e7ebe8` / `#dce2de` / `#dde9e2` | Subtle hover / pressed / selected | grey96 / grey88 / grey92 | Role match; Fluent selected is neutral |
| accent | `#3f5a4c` | Brand background | `#0f6cbd` | Differs on purpose (D1) |
| text-on-accent | white | ForegroundOnBrand | white | Match |
| danger / ok | `#b3123a` / `#1d6a3a` | danger fg / success fg | `#b10e1c` / `#0e700e` | Close |
| high contrast | Window, WindowText, Highlight, Hotlight, GrayText | Canvas, CanvasText, Highlight, Hyperlink, Disabled | | Match in role; use live system colours |
| dark base / layer / card | `#191c1a` / `#232725` / `#2b302d` | Background3 / 2 / 1 | `#141414` / `#1f1f1f` / `#292929` | Role order matches; ours lighter and tinted |
| float shadow | 0 8 24 / 7 % + 0 2 6 / 6 % | shadow16 or shadow28 | key .14, ambient .12 | Differs: ours is much softer |
| dialog buttons | see decisions | primary left, close right, default = accent + Enter, Esc closes | | Check each dialog against tokens.md section 10 |
| toast timing | 240 ms enter | Windows toast about 5 s | unverified | Do not decide on it |

Unverified items to resolve before a look row depends on them: title bar heights, compact
control and list heights, checkbox size, thin scrollbar width, focus ring offset, toast
lifetime. The WinUI Gallery (Microsoft Store) or the newer `microsoft-ui-xaml` `dev/CommonStyles`
files can confirm them.
