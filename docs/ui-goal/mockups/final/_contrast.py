"""Final spec: compute WCAG contrast for every token pair in tokens.css (D10), for light, dark and hc.

HC follows the OS palette (D9): the hc block maps every token to one of the Windows system colours
(--sys-*). The proof runs for "High Contrast Black" and the four Windows 11 contrast themes
(Aquatic, Desert, Dusk, Night sky), each read from its [data-hc="…"] block. The D1 hue rule
(orange only for Kontrol) does not apply in HC, where the OS owns the colours; instead HC checks
that Kontrol ink differs from the link colour (Hotlight) and that Kontrol is not drawn in Hotlight.

Usage:  python3 docs/ui-goal/mockups/final/_contrast.py           # print, exit 1 on any failure
        python3 docs/ui-goal/mockups/final/_contrast.py --write   # also refresh the table in tokens.css
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
    ("text", "layer", 7, "body text / layer"),
    ("text", "card", 7, "body text / card"),
    ("text", "popover", 7, "menu text / popover"),
    ("text", "hover", 7, "body text / hover"),
    ("text", "selected", 7, "body text / selected row"),
    ("text", "check-wash", 7, "body text / kontrol wash"),
    ("text", "well", 7, "body text / well"),
    ("paper-ink", "paper", 7, "paper ink / paper"),
    ("text-2", "base", 4.5, "secondary / base"),
    ("text-2", "layer", 4.5, "secondary / layer"),
    ("text-2", "card", 4.5, "secondary / card"),
    ("text-2", "popover", 4.5, "secondary / popover"),
    ("text-2", "selected", 4.5, "secondary / selected row"),
    ("text-2", "hover", 4.5, "secondary / hover"),
    ("text-2", "well", 4.5, "secondary / well"),
    ("text-on-accent", "accent-fill", 4.5, "on-accent / accent fill (15px/600)"),
    ("text-on-accent", "accent-fill-hover", 4.5, "on-accent / accent fill hover"),
    ("text-accent", "card", 4.5, "accent text / card"),
    ("text-accent", "layer", 4.5, "accent text / layer"),
    ("text-accent", "popover", 4.5, "accent text / popover (Geri al)"),
    ("text-accent", "selected", 4.5, "accent text / selected row"),
    ("manila-ink", "manila", 7, "manila ink / manila"),
    ("rider-ink", "rider", 4.5, "rider ink / rider (13px/600)"),
    ("check-text", "card", 4.5, "kontrol text / card"),
    ("check-text", "layer", 4.5, "kontrol text / layer"),
    ("check-text", "selected", 4.5, "kontrol text / selected row"),
    ("check-text", "check-wash", 4.5, "kontrol text / kontrol wash"),
    ("ok", "card", 4.5, "ok text / card"),
    ("ok", "layer", 4.5, "ok icon / layer"),
    ("ok", "base", 4.5, "ok icon / base (status bar)"),
    ("ok", "popover", 4.5, "ok icon / popover"),
    ("danger", "card", 4.5, "danger text / card"),
    ("danger", "popover", 4.5, "danger text / popover"),
    ("danger", "layer", 4.5, "danger text / layer"),
    ("danger", "well", 4.5, "danger text / well"),
    ("edge", "card", 3, "input edge / card"),
    ("edge", "layer", 3, "input edge / layer"),
    ("edge", "popover", 3, "input edge / popover"),
    ("icon", "base", 3, "icon / base"),
    ("icon", "layer", 3, "icon / layer"),
    ("icon", "card", 3, "icon / card"),
    ("icon", "hover", 3, "icon / hover"),
    ("icon", "well", 3, "icon / well"),
    ("accent", "well", 3, "accent line, selection ring / well"),
    ("accent", "layer", 3, "accent line / layer"),
    ("accent", "card", 3, "accent line / card"),
    ("accent", "track", 3, "slider fill / track"),
    ("accent", "selected", 3, "selected-row bar / selected row"),
    ("accent", "card", 3, "selector pill / card"),
    ("focus-outer", "base", 3, "focus outer / base"),
    ("focus-outer", "layer", 3, "focus outer / layer"),
    ("focus-outer", "card", 3, "focus outer / card"),
    ("focus-outer", "well", 3, "focus outer / well"),
    ("focus-outer", "selected", 3, "focus outer / selected row"),
    ("focus-outer", "popover", 3, "focus outer / popover"),
    ("rider-edge", "well", 3, "rider edge / well"),
    ("rider-edge", "track", 3, "kontrol tick edge / track"),
    ("rider-edge", "card", 3, "uncertain-char underline / card"),
    ("accent", "track", 3, "reviewed tick / track (overview)"),
    ("manila-edge", "well", 3, "guide tab edge / well"),
    ("manila-edge", "card", 3, "guide tab edge / card"),
    ("cut-qr", "manila", 3, "QR pictogram / manila"),
    ("cut-filter", "manila", 3, "filter pictogram / manila"),
    ("cut-manual", "manila", 3, "manual pictogram / manila"),
    ("on-manila-ok", "manila", 3, "reviewed check / manila"),
    ("paper-box", "paper", 3, "field box / scan crop"),
    ("paper-mark", "paper", 3, "uncertain box / scan crop"),
    ("paper-head", "paper", 3, "crop label ink (scan) / paper"),
    ("cut-filter-text", "card", 3, "filter pictogram / card"),
    ("text", "hover-pop", 7, "menu text / menu hover"),
    ("danger", "hover-pop", 4.5, "danger item / menu hover"),
    ("text-dis", "layer", 3, "disabled text / layer"),
    ("ghost-edge", "well", 3, "deleted-page outline / well"),
    ("edge", "base", 3, "slider groove + thumb edge / base"),
    ("accent", "card", 3, "checked checkbox edge / card"),
    ("rider-edge", "layer", 3, "Kontrol segment edge / layer"),
    ("text-on-accent", "accent-fill", 4.5, "selected row ink / Highlight (HC rows)"),
]
HC_PALETTES = ["black", "aquatic", "desert", "dusk", "nightsky"]

# D1: orange means kontrol only. Every saturated non-kontrol token must sit >= 30 deg of hue away
# from --rider. Neutral tokens (HSL saturation < 0.2) cannot read as orange and are skipped.
# Manila is exempt: it is the D1 brand tint for "filed", told apart by lightness (L 0.78 vs 0.51).
HUE_TOKENS = ["cut-qr", "cut-filter", "cut-manual", "ok", "danger", "accent", "accent-fill", "text-accent"]
HUE_MIN = 30


def block(css: str, selector_regex: str) -> dict[str, str]:
    """Custom properties of one rule: hex values and var(--name) references (resolved later)."""
    match = re.search(selector_regex + r"\s*\{(.*?)\}", css, re.S)
    if not match:
        raise SystemExit(f"block not found: {selector_regex}")
    found = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", match.group(1)))
    found.update({k: "@" + v for k, v in re.findall(r"--([\w-]+):\s*var\(--([\w-]+)\)", match.group(1))})
    return found


def resolve(theme: dict[str, str]) -> dict[str, str]:
    out = {}
    for key, value in theme.items():
        seen = 0
        while value.startswith("@") and seen < 8:
            value, seen = theme[value[1:]], seen + 1
        out[key] = value
    return out


def luminance(hex_value: str) -> float:
    channels = [int(hex_value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def lstar(hex_value: str) -> float:
    y = luminance(hex_value)
    return 116 * (y ** (1 / 3) if y > 0.008856 else 7.787 * y + 16 / 116) - 16


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
    light = resolve(block(css, r':root,\s*\[data-theme="light"\]'))
    dark = resolve({**light, **block(css, r'\[data-theme="dark"\]')})
    hc_base = {**light, **block(css, r'\[data-theme="hc"\]')}
    themes = [("LIGHT", light), ("DARK", dark)]
    for pal in HC_PALETTES:
        extra = {} if pal == "black" else block(css, r'\[data-theme="hc"\]\[data-hc="' + pal + r'"\]')
        themes.append((f"HC {pal}", resolve({**hc_base, **extra})))
    lines, failures = [], 0
    for name, theme in themes:
        lines.append(f" * {name}")
        for fg, bg, minimum, label in PAIRS:
            value, shown = ratio(theme[fg], theme[bg]), theme[fg]
            ok = value >= minimum
            failures += not ok
            lines.append(f" *   {label:<34} {shown:>8} on {theme[bg]}  {value:5.2f}:1"
                         f"  min {minimum:<3} {'ok' if ok else 'FAIL'}")
        if name.startswith("HC"):
            ok = theme["check-text"].lower() != theme["text-accent"].lower()
            failures += not ok
            lines.append(f" *   Kontrol ink {theme['check-text']} differs from link (Hotlight) {theme['text-accent']}"
                         f"            {'ok' if ok else 'FAIL'}")
            lines.append(" *   hue rule: n/a in HC (OS colours); Kontrol = triangle + word + outlined rider")
            continue
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
        lines.append(f" *   surface steps (CIELAB L*)          " + "  ".join(f"{t} {lstar(theme[t]):.1f}" for t in ("base", "layer", "card", "well")))
        if theme["danger"].lower() == theme["rider"].lower():
            failures += 1
            lines.append(" *   danger equals rider                                              FAIL")
    table = "\n".join(lines)
    print(table)
    if "--write" in sys.argv:
        new = re.sub(r" \* LIGHT\n.*?(\n \* END PROOF)", lambda m: table + m.group(1), css, flags=re.S)
        TOKENS.write_text(new, encoding="utf-8")
    print(f"{failures} failing pairs", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
