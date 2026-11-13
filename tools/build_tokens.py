"""Build the design tokens from direction A's tokens.css (the approved spec).

    python3 tools/build_tokens.py          # rewrite tokens.json and generated.py
    python3 tools/build_tokens.py --check  # exit 1 if either file is out of date

Reads docs/ui-goal/mockups/final-a/tokens.css (custom properties per theme: light, dark, hc,
plus type, spacing, radii, sizes, motion and the 150 % text block) and writes:

- src/evrakci/ui/tokens/tokens.json: DTCG format ($value / $type), hc values as aliases to the
  Windows system colours they stand for;
- src/evrakci/ui/tokens/generated.py: the same values as plain Python dicts, so the frozen app
  needs no JSON parsing. It is the only module with hex colour literals (besides logo_data.py).

Density steps (D5): Normal is A's :root sizes; Geniş (comfortable) is the size part of A's
[data-text="150"] block ("the chrome one density up"); Sıkı (compact) is not drawn in A and takes
D5's control 28 / row 32 with the matching icon button and command bar (COMPACT below).
"""
from __future__ import annotations

import json
import pprint
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSS = ROOT / "docs" / "ui-goal" / "mockups" / "final-a" / "tokens.css"
OUT_DIR = ROOT / "src" / "evrakci" / "ui" / "tokens"
JSON_OUT = OUT_DIR / "tokens.json"
PY_OUT = OUT_DIR / "generated.py"

# D5 Sıkı: rows 32, controls 28. A draws 32 px small icon buttons (.iconbtn.sm); the command
# bar keeps 4 px around them. Everything else stays at Normal.
COMPACT = {"control-h": 28, "row-h": 32, "icon-btn": 32, "commandbar-h": 40}
TEXT_SCALES = {"100": 1.0, "115": 1.15, "130": 1.3, "150": 1.5}
DENSITY_STEP_UP_FROM = 130  # text 130 % and 150 % move the chrome one density up (D5)

SELECTORS = {
    "light": r':root,\s*\[data-theme="light"\]\s*\{',
    "dark": r'\[data-theme="dark"\]\s*\{',
    "hc": r'\[data-theme="hc"\]\s*\{',
    "root": r'(?m)^:root\s*\{',
    "text150": r'\[data-text="150"\]\s*\{',
}


def _block(css: str, selector: str) -> dict[str, str]:
    match = re.search(selector + r"(.*?)\n\}", css, re.S)
    if not match:
        raise SystemExit(f"tokens.css: block not found: {selector}")
    return {k: v.strip() for k, v in re.findall(r"--([\w-]+)\s*:\s*([^;]+);", match.group(1))}


def _px(value: str) -> float:
    number = float(value.removesuffix("px"))
    return int(number) if number.is_integer() else number


def _dim(value: float, unit: str = "px") -> dict:
    return {"value": value, "unit": unit}


def _rgba_hex(text: str) -> str:
    if text == "transparent":
        return "#00000000"
    if text.startswith("#"):
        return text.lower()
    r, g, b, a = (p.strip() for p in re.match(r"rgba\((.*)\)", text).group(1).split(","))
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}{round(float(a) * 255):02x}"


def _shadow(value: str) -> list[dict]:
    layers = []
    for part in re.split(r",\s*(?![^()]*\))", value):
        inset = part.strip().startswith("inset")
        part = part.replace("inset", "").strip()
        colour = re.search(r"(rgba\([^)]*\)|#[0-9a-fA-F]+|transparent)", part).group(1)
        nums = [_px(n) for n in re.findall(r"-?[\d.]+px|\b0\b", part.replace(colour, ""))]
        nums += [0] * (4 - len(nums))
        layers.append({"color": _rgba_hex(colour), "offsetX": _dim(nums[0]),
                       "offsetY": _dim(nums[1]), "blur": _dim(nums[2]),
                       "spread": _dim(nums[3]), "inset": inset})
    return layers


def _theme(decls: dict[str, str]) -> tuple[dict, dict]:
    colours, shadows = {}, {}
    for name, value in decls.items():
        if name.startswith("shadow-") or name == "edge-light":
            shadows[name] = {"$type": "shadow", "$value": _shadow(value)}
        elif name.startswith("sys-"):
            continue
        elif value.startswith("var(--"):
            ref = value[6:-1]
            colours[name] = {"$type": "color", "$value": "{color.system." + ref + "}"}
        elif value.startswith("#"):
            colours[name] = {"$type": "color", "$value": value.lower()}
    return colours, shadows


def build_json(css: str) -> dict:
    """DTCG token tree from the text of tokens.css."""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    blocks = {key: _block(css, sel) for key, sel in SELECTORS.items()}
    light = blocks["light"]
    dark = {**light, **blocks["dark"]}
    hc = {**light, **blocks["hc"]}
    color, shadow = {}, {}
    for name, decls in (("light", light), ("dark", dark), ("hc", hc)):
        color[name], shadow[name] = _theme(decls)
    color["system"] = {k: {"$type": "color", "$value": v.lower()}
                       for k, v in blocks["hc"].items() if k.startswith("sys-")}
    root = blocks["root"]
    families = [f.strip().strip('"') for f in root["font"].split(",")]
    font = {
        "family": {"$type": "fontFamily", "$value": families},
        "weight": {k[2:]: {"$type": "fontWeight", "$value": int(v)}
                   for k, v in root.items() if k.startswith("w-")},
        "size": {k[3:]: {"$type": "dimension", "$value": _dim(_px(v))}
                 for k, v in root.items() if k.startswith("fs-")},
        "line-height": {k[3:]: {"$type": "dimension", "$value": _dim(_px(v))}
                        for k, v in root.items() if k.startswith("lh-")},
        "feature": {k[3:]: {"$type": "string", "$value": " ".join(
            re.findall(r'"(\w+)"', v))} for k, v in root.items() if k.startswith("ff-")},
    }
    sizes = {k: _px(v) for k, v in root.items() if re.match(r"(?!fs-|lh-|w-|s\d|r-|d-)", k)
             and v.endswith("px")}
    comfortable = {k: _px(v) for k, v in blocks["text150"].items()
                   if k in sizes}
    for key, value in blocks["text150"].items():  # the 150 % type must be A's type x 1.5
        if key[:3] in ("fs-", "lh-") and _px(value) != _px(root[key]) * 1.5:
            raise SystemExit(f"tokens.css: --{key} at 150 % is not x1.5")

    def dims(values: dict) -> dict:
        return {k: {"$type": "dimension", "$value": _dim(v)} for k, v in values.items()}

    return {
        "$description": "Evrakçı design tokens, direction A 'Fluent 2 Mica'. Generated by "
                        "tools/build_tokens.py from docs/ui-goal/mockups/final-a/tokens.css; "
                        "do not edit by hand.",
        "color": color,
        "shadow": shadow,
        "font": font,
        "space": dims({k: _px(v) for k, v in root.items() if re.fullmatch(r"s\d+", k)}),
        "radius": dims({k: _px(v) for k, v in root.items() if k.startswith("r-")}),
        "size": {
            "compact": dims({**sizes, **COMPACT}),
            "normal": dims(sizes),
            "comfortable": dims({**sizes, **comfortable}),
        },
        "text-scale": {
            **{k: {"$type": "number", "$value": v} for k, v in TEXT_SCALES.items()},
            "$extensions": {"evrakci.densityStepUpFrom": DENSITY_STEP_UP_FROM},
        },
        "duration": {k: {"$type": "duration", "$value": _dim(int(v.removesuffix("ms")), "ms")}
                     for k, v in root.items() if k.startswith("d-")},
        "easing": {k: {"$type": "cubicBezier", "$value": [float(n) for n in re.findall(
            r"[\d.]+", v)]} for k, v in root.items() if k.startswith("ease-")},
    }


def _value(token: dict):
    value = token["$value"]
    return value["value"] if isinstance(value, dict) and "unit" in value else value


def _resolve(value: str, tree: dict) -> str:
    if isinstance(value, str) and value.startswith("{"):
        node = tree
        for part in value[1:-1].split("."):
            node = node[part]
        return _resolve(node["$value"], tree)
    return value


def _plain_shadow(layers: list[dict]) -> list[dict]:
    return [{"x": s["offsetX"]["value"], "y": s["offsetY"]["value"], "blur": s["blur"]["value"],
             "spread": s["spread"]["value"], "color": s["color"], "inset": s["inset"]}
            for s in layers]


def render_python(tree: dict) -> str:
    """generated.py source for a DTCG token tree (deterministic)."""
    themes = ("light", "dark", "hc")
    colors = {t: {k: _resolve(v["$value"], tree) for k, v in tree["color"][t].items()}
              for t in themes}
    hc_system = {k: v["$value"][len("{color.system."):-1]
                 for k, v in tree["color"]["hc"].items() if v["$value"].startswith("{")}
    font = tree["font"]
    data = {
        "COLORS": colors,
        "SYSTEM_COLORS": {k: v["$value"] for k, v in tree["color"]["system"].items()},
        "HC_SYSTEM": hc_system,
        "SHADOWS": {t: {k: _plain_shadow(v["$value"]) for k, v in tree["shadow"][t].items()}
                    for t in themes},
        "FONT_FAMILIES": font["family"]["$value"],
        "TYPE": {k: {"size": _value(v), "line": _value(font["line-height"][k])}
                 for k, v in font["size"].items()},
        "WEIGHTS": {k: v["$value"] for k, v in font["weight"].items()},
        "FEATURES": {k: v["$value"].split() for k, v in font["feature"].items()},
        "SPACE": {k: _value(v) for k, v in tree["space"].items()},
        "RADII": {k: _value(v) for k, v in tree["radius"].items()},
        "SIZES": {d: {k: _value(v) for k, v in tree["size"][d].items()}
                  for d in ("compact", "normal", "comfortable")},
        "TEXT_SCALES": {int(k): v["$value"] for k, v in tree["text-scale"].items()
                        if not k.startswith("$")},
        "DENSITY_STEP_UP_FROM": tree["text-scale"]["$extensions"]["evrakci.densityStepUpFrom"],
        "DURATIONS": {k: _value(v) for k, v in tree["duration"].items()},
        "EASINGS": {k: v["$value"] for k, v in tree["easing"].items()},
    }
    lines = [
        '"""Design tokens as plain Python data. GENERATED by tools/build_tokens.py from',
        "docs/ui-goal/mockups/final-a/tokens.css (via tokens.json); do not edit by hand.",
        "",
        "The only module in src/evrakci/ui with hex colour literals (besides logo_data.py).",
        '"""',
        "# ruff: noqa: E501",
        "",
    ]
    for name, value in data.items():
        lines.append(f"{name} = {pprint.pformat(value, width=99, sort_dicts=False)}")
        lines.append("")
    return "\n".join(lines)


def render_json(tree: dict) -> str:
    return json.dumps(tree, ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str]) -> int:
    tree = build_json(CSS.read_text(encoding="utf-8"))
    outputs = {JSON_OUT: render_json(tree), PY_OUT: render_python(tree)}
    if "--check" in argv:
        stale = [p for p, text in outputs.items()
                 if not p.is_file() or p.read_text(encoding="utf-8") != text]
        for path in stale:
            print(f"out of date: {path.relative_to(ROOT)}")
        return 1 if stale else 0
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path, text in outputs.items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
