"""Direction B copy of ../../_contrast.py. Compute WCAG contrast for every token pair in tokens.css (D10) and print the proof table.

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
    ("text", "base", 7, "body text / base"),
    ("text", "panel", 7, "body text / panel"),
    ("text", "well", 7, "body text / well"),
    ("text", "hover", 7, "body text / hover"),
    ("text", "selected", 7, "body text / selected"),
    ("text", "popover", 7, "body text / popover"),
    ("text", "check-wash", 7, "body text / kontrol wash"),
    ("text-2", "base", 4.5, "secondary / base"),
    ("text-2", "panel", 4.5, "secondary / panel"),
    ("text-2", "well", 4.5, "secondary / well"),
    ("text-2", "selected", 4.5, "secondary / selected"),
    ("text-2", "popover", 4.5, "secondary / popover"),
    ("text-on-accent", "accent", 7, "on-accent / accent"),
    ("text-accent", "panel", 4.5, "accent text / panel"),
    ("text-accent", "base", 4.5, "accent text / base"),
    ("text-accent", "selected", 4.5, "accent text / selected"),
    ("manila-ink", "manila", 7, "manila ink / manila"),
    ("rider-ink", "rider", 4.5, "rider ink / rider (13px/600)"),
    ("check-text", "panel", 4.5, "kontrol text / panel"),
    ("check-text", "base", 4.5, "kontrol text / base"),
    ("check-text", "selected", 4.5, "kontrol text / selected"),
    ("check-text", "check-wash", 4.5, "kontrol text / kontrol wash"),
    ("ok", "panel", 4.5, "ok text / panel"),
    ("ok", "selected", 4.5, "ok text / selected"),
    ("danger", "panel", 4.5, "danger text / panel"),
    ("danger", "popover", 4.5, "danger text / popover"),
    ("edge", "panel", 3, "input edge / panel"),
    ("edge", "well", 3, "input edge / well"),
    ("edge", "base", 3, "input edge / base"),
    ("icon", "panel", 3, "icon / panel"),
    ("icon", "base", 3, "icon / base"),
    ("icon-2", "panel", 3, "icon-2 / panel"),
    ("icon-2", "base", 3, "icon-2 / base"),
    ("icon-2", "popover", 3, "icon-2 / popover"),
    ("accent", "panel", 3, "accent (pill, ring) / panel"),
    ("accent", "base", 3, "accent (pill) / base"),
    ("accent", "selected", 3, "accent (ring) / selected tray"),
    ("focus-outer", "panel", 3, "focus outer / panel"),
    ("focus-outer", "base", 3, "focus outer / base"),
    ("focus-outer", "selected", 3, "focus outer / selected tray"),
    ("focus-outer", "popover", 3, "focus outer / popover"),
    ("rider-edge", "panel", 3, "rider edge / panel"),
    ("rider-edge", "selected", 3, "rider edge / selected tray"),
    ("manila-edge", "panel", 3, "manila edge / panel"),
    ("manila-edge", "selected", 3, "manila edge / selected tray"),
    ("cut-qr", "panel", 3, "QR cut / panel"),
    ("cut-filter", "panel", 3, "filter cut / panel"),
    ("cut-manual", "panel", 3, "manual cut / panel"),
]

# D1: orange means kontrol only. Every saturated non-kontrol token must sit >= 30 deg of hue away
# from --rider. Neutral tokens (HSL saturation < 0.2) cannot read as orange and are skipped.
# Manila is exempt: it is the D1 brand tint for "filed", told apart by lightness (L 0.78 vs 0.51).
HUE_TOKENS = ["cut-qr", "cut-filter", "cut-manual", "ok", "danger", "accent", "text-accent"]
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
        new = re.sub(r"( \* LIGHT\n.*?)(\n \*\n \* \(end of proof\))", lambda m: table + m.group(2), css, flags=re.S)
        TOKENS.write_text(new, encoding="utf-8")
    print(f"{failures} failing pairs", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
