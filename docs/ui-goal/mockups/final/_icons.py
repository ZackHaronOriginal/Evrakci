"""Rebuild icons.js from lucide-static 0.460.0 (ISC). Only real Lucide paths, copied verbatim.

Usage:
    npm pack lucide-static@0.460.0 && tar xzf lucide-static-0.460.0.tgz   # in a scratch folder
    python3 _icons.py /path/to/package/icons

Add a name to NAMES, re-run, and use it as <i class="ic" data-i="name"></i>.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NAMES = sorted({
    # shell
    "menu", "search", "minus", "square", "x", "chevron-down", "chevron-right", "chevron-left",
    "chevron-up", "check", "circle-check", "folder-open", "zoom-in", "zoom-out", "settings",
    # commands
    "undo-2", "redo-2", "scissors", "merge", "rotate-cw", "rotate-ccw", "trash-2", "stamp", "filter",
    "triangle-alert", "circle-dashed", "arrow-right-to-line", "eye", "panel-right", "ellipsis",
    "maximize-2", "scan-text", "list-checks", "shuffle", "check-check", "list-filter", "pencil",
    "copy", "save", "play", "plus", "square-dashed", "magnet", "printer", "external-link",
    "keyboard", "circle-help", "info", "ban", "loader-circle", "refresh-cw", "download", "sheet",
    "file-up", "file-plus", "folder-plus", "folder", "folder-check", "arrow-up", "arrow-down",
    "grip-vertical", "scan-line", "upload", "lock", "braces", "file-text", "command", "history",
    "qr-code", "table", "panel-left", "signal-high", "signal-medium", "circle-x", "book-open", "layers",
})


def inner(svg: str) -> str:
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    return " ".join(line.strip() for line in body.strip().splitlines())


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/lucide/package/icons")
    icons = {name: inner((src / f"{name}.svg").read_text(encoding="utf-8")) for name in NAMES}
    out = [
        "/* Lucide icons v0.460.0 (ISC licence, https://lucide.dev): inner SVG copied verbatim from",
        "   lucide-static@0.460.0 by _icons.py. Usage: <i class=\"ic\" data-i=\"scissors\"></i>.",
        "   In Qt these are the same SVG files rendered by QSvgRenderer and recoloured from tokens (D8). */",
        "const LUCIDE = {",
        ",\n".join(f"{json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}" for k, v in icons.items()),
        "};",
        "function renderIcons(root) {",
        "  (root || document).querySelectorAll('i[data-i]').forEach(el => {",
        "    const n = el.dataset.i;",
        "    if (!LUCIDE[n]) { console.error('missing icon ' + n); return; }",
        "    el.innerHTML = '<svg viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" '",
        "      + 'stroke-linecap=\"round\" stroke-linejoin=\"round\" aria-hidden=\"true\">' + LUCIDE[n] + '</svg>';",
        "  });",
        "}",
        "",
    ]
    (HERE / "icons.js").write_text("\n".join(out), encoding="utf-8")
    print(f"icons.js: {len(icons)} icons")
    return 0


if __name__ == "__main__":
    sys.exit(main())
