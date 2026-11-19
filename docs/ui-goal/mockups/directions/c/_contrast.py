"""Compute WCAG contrast for every token pair in tokens.css (D10) and print the proof table.

Usage:  python3 docs/ui-goal/mockups/_contrast.py           # print, exit 1 on any failure
        python3 docs/ui-goal/mockups/_contrast.py --write   # also refresh the table in tokens.css
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOKENS = HERE / "tokens.css"

# (foreground, background, D10 minimum, label). "focus-best" = the better of the two focus rings.
PAIRS = [
    ("text", "bg-base", 7, "body text / desk"),
    ("text", "bg-layer", 7, "body text / layer"),
    ("text", "bg-well", 7, "body text / well"),
    ("text", "bg-popover", 7, "menu text / popover"),
    ("text", "bg-selected", 7, "text / selected row"),
    ("text", "bg-hover", 7, "text / hover"),
    ("text-on-paper", "paper", 7, "text / paper"),
    ("text-2", "bg-base", 4.5, "secondary / desk"),
    ("text-2", "bg-layer", 4.5, "secondary / layer"),
    ("text-2", "bg-well", 4.5, "secondary / well"),
    ("text-2", "bg-popover", 4.5, "secondary / popover"),
    ("text-2", "bg-selected", 4.5, "secondary / selected"),
    ("text-2", "bg-hover", 4.5, "secondary / hover"),
    ("on-shell", "shell", 7, "tab text / band"),
    ("on-shell-2", "shell", 4.5, "idle tab text / band"),
    ("on-shell-2", "shell-hover", 4.5, "idle tab text / band hover"),
    ("on-accent", "accent", 7, "on-accent / accent (15px/600)"),
    ("on-accent", "accent-hover", 7, "on-accent / accent hover"),
    ("accent-text", "bg-layer", 4.5, "accent text / layer"),
    ("accent-text", "bg-base", 4.5, "accent text / desk"),
    ("manila-ink", "manila", 7, "manila ink / manila"),
    ("rider-ink", "rider", 4.5, "rider ink / rider (13px/600)"),
    ("check-text", "bg-layer", 4.5, "kontrol text / layer"),
    ("check-text", "bg-base", 4.5, "kontrol text / desk"),
    ("check-text", "bg-selected", 4.5, "kontrol text / selected row"),
    ("text", "check-wash", 7, "text / uncertain-char wash"),
    ("ok", "bg-layer", 4.5, "ok text / layer"),
    ("ok", "bg-selected", 4.5, "ok text / selected row"),
    ("danger", "bg-layer", 4.5, "danger text / layer"),
    ("danger", "bg-popover", 4.5, "danger text / popover"),
    ("danger", "bg-selected", 4.5, "danger text / selected row"),
    ("text-disabled", "bg-layer", 3, "disabled text / layer"),
    ("edge", "bg-layer", 3, "input edge / layer"),
    ("edge", "bg-base", 3, "input edge / desk"),
    ("edge", "bg-popover", 3, "input edge / popover"),
    ("icon", "bg-base", 3, "icon / desk"),
    ("icon", "bg-layer", 3, "icon / layer"),
    ("on-shell", "shell", 3, "band icon / band"),
    ("accent", "bg-layer", 3, "accent fill / layer"),
    ("accent", "bg-base", 3, "accent fill / desk"),
    ("select-ring", "bg-base", 3, "selection ring / desk"),
    ("select-ring", "bg-selected", 3, "selection ring / selected tray"),
    ("focus-outer", "bg-base", 3, "focus outer / desk"),
    ("focus-outer", "bg-layer", 3, "focus outer / layer"),
    ("focus-outer", "bg-selected", 3, "focus outer / selected tray"),
    ("focus-outer", "bg-popover", 3, "focus outer / popover"),
    ("focus-on-shell", "shell", 3, "focus on band / band"),
    ("rider-edge", "bg-base", 3, "rider edge / desk"),
    ("rider-edge", "bg-layer", 3, "rider edge / layer"),
    ("rider-edge", "bg-selected", 3, "rider edge / selected tray"),
    ("manila-edge", "bg-base", 3, "guide tab edge / desk"),
    ("manila-edge", "bg-selected", 3, "guide tab edge / selected tray"),
    ("reviewed", "manila", 3, "reviewed glyph / manila"),
]

# D1: orange means kontrol only. Every saturated non-kontrol token must sit >= 30 deg of hue away
# from --rider. Neutral tokens (HSL saturation < 0.2) cannot read as orange and are skipped.
# Manila is exempt: it is the D1 brand tint for "filed", told apart by lightness (L 0.78 vs 0.51).
HUE_TOKENS = ["ok", "danger", "info", "accent", "accent-text", "select-ring", "reviewed"]
HUE_MIN = 30


def block(css: str, selector_regex: str) -> dict[str, str]:
    match = re.search(selector_regex + r"\s*\{(.*?)\n\}", css, re.S)
    if not match:
        raise SystemExit(f"block not found: {selector_regex}")
    return dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", match.group(1)))


def luminance(hex_value: str) -> float:
    channels = [int(hex_value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def hue_sat(hex_value: str) -> tuple[float, float]:
    import colorsys
    h, _l, sat = colorsys.rgb_to_hls(*[int(hex_value[i:i + 2], 16) / 255 for i in (1, 3, 5)])
    return h * 360, sat


def hue_gap(a: float, b: float) -> float:
    d = abs(a - b) % 360
    return min(d, 360 - d)


def main() -> int:
    css = TOKENS.read_text(encoding="utf-8")
    light = block(css, r':root,\s*\[data-theme="light"\]')
    dark = {**light, **block(css, r'\[data-theme="dark"\]')}
    lines, failures = [], 0
    for name, theme in (("LIGHT", light), ("DARK", dark)):
        lines.append(f" * {name}")
        for fg, bg, minimum, label in PAIRS:
            value, shown = ratio(theme[fg], theme[bg]), theme[fg]
            ok = value >= minimum
            failures += not ok
            lines.append(f" *   {label:<34} {shown:>8} on {theme[bg]}  {value:5.2f}:1"
                         f"  min {minimum:<3} {'ok' if ok else 'FAIL'}")
        rider_hue, _ = hue_sat(theme["rider"])
        for token in HUE_TOKENS:
            h, sat = hue_sat(theme[token])
            if sat < 0.2:
                lines.append(f" *   hue {token:<30} {theme[token]:>8} neutral (sat {sat:.2f})      skip")
                continue
            gap = hue_gap(h, rider_hue)
            ok = gap >= HUE_MIN
            failures += not ok
            lines.append(f" *   hue {token:<30} {theme[token]:>8} {gap:5.0f} deg from rider"
                         f"  min {HUE_MIN} {'ok' if ok else 'FAIL'}")
        if theme["danger"].lower() == theme["rider"].lower():
            failures += 1
            lines.append(" *   danger equals rider                                              FAIL")
    table = "\n".join(lines)
    print(table)
    if "--write" in sys.argv:
        new = re.sub(r"( \* LIGHT\n.*?)(\n \*\n \* High contrast)", lambda m: table + m.group(2), css, flags=re.S)
        TOKENS.write_text(new, encoding="utf-8")
    print(f"{failures} failing pairs", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
