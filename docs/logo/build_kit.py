"""Build the Evrakçı logo kit (concept C, "Kademeli sekmeler") from one geometry.

    python3 docs/logo/build_kit.py

Writes SVG masters to docs/logo/kit/, and updates the app copies:
packaging/linux/evrakci.svg, packaging/evrakci.ico and src/evrakci/ui/logo_data.py.
The wordmark is Inter Display SemiBold (SIL OFL 1.1) converted to outlines, so no font is needed.
"""

from __future__ import annotations

from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
KIT = HERE / "kit"
FONT = Path("/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf")

GREEN = "#3f5a4c"  # cabinet green (DESIGN.md: shell)
GREEN_DARK = "#344b3f"
MANILA = "#e9d9a6"  # guide card (manila)
ORANGE = "#e8731a"  # the rider: "needs a check"
INK = "#1d2a23"
WHITE = "#ffffff"

# Master geometry on a 256 grid. Three filed documents seen from above: a 192 x 40 card with
# a 64 px tab (60° sides) at the left, centre and right, the app's three cut positions.
ROWS = [(26, 44), (96, 96), (166, 148)]  # (tab top, tab left)
CARD_X, CARD_W, CARD_H, CARD_R = 32, 192, 40, 9


def _tab(top: float, left: float) -> str:
    base = top + 25  # 1 px under the card's top edge, so the shapes overlap cleanly
    return f"M{left} {base}l14-25h36l14 25z"


def _card(top: float) -> str:
    y = top + 24
    x, w, h, r = CARD_X, CARD_W, CARD_H, CARD_R
    return (f"M{x + r} {y}h{w - 2 * r}a{r} {r} 0 0 1 {r} {r}v{h - 2 * r}a{r} {r} 0 0 1 -{r} {r}"
            f"h-{w - 2 * r}a{r} {r} 0 0 1 -{r} -{r}v-{h - 2 * r}a{r} {r} 0 0 1 {r} -{r}z")


def symbol_paths(card: str, tabs: tuple[str, str, str]) -> str:
    out = []
    for (top, left), tab in zip(ROWS, tabs, strict=True):
        out.append(f'<path d="{_tab(top, left)}" fill="{tab}"/>')
        out.append(f'<path d="{_card(top)}" fill="{card}"/>')
    return "\n  ".join(out)


# Small-size cuts, drawn on the pixel grid (16 px): tabs become 1 px steps.
def small_symbol(card: str, tabs: tuple[str, str, str]) -> str:
    rows = [(1, 2), (6, 6), (11, 10)]
    out = []
    for (y, x), tab in zip(rows, tabs, strict=True):
        out.append(f'<rect x="{x}" y="{y}" width="4" height="1" fill="{tab}"/>')
        out.append(f'<rect x="1" y="{y + 1}" width="14" height="3" rx=".6" fill="{card}"/>')
    return "\n  ".join(out)


def small_tile(card: str, tabs: tuple[str, str, str], tile: str) -> str:
    rows = [(2, 3), (6, 6), (10, 9)]
    out = [f'<rect width="16" height="16" rx="3.5" fill="{tile}"/>']
    for (y, x), tab in zip(rows, tabs, strict=True):
        out.append(f'<rect x="{x}" y="{y}" width="4" height="1" fill="{tab}"/>')
        out.append(f'<rect x="2" y="{y + 1}" width="12" height="2" rx=".5" fill="{card}"/>')
    return "\n  ".join(out)


def svg(view: str, body: str, title: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{view}">\n'
            f"  <title>{title}</title>\n  {body}\n</svg>\n")


def wordmark(text: str, height: float, colour: str) -> tuple[str, float]:
    """Outlined text with cap height `height`; returns (paths, width)."""
    font = TTFont(FONT)
    glyphs = font.getGlyphSet()
    cmap = font.getBestCmap()
    cap = font["OS/2"].sCapHeight
    scale = height / cap
    tracking = -0.01 * font["head"].unitsPerEm  # a hair tighter than the default
    kern = _kerning(font)
    pen = SVGPathPen(glyphs)
    x = 0.0
    names = [cmap[ord(ch)] for ch in text]
    for i, name in enumerate(names):
        glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, x * scale, height)))
        x += glyphs[name].width + tracking
        if i + 1 < len(names):
            x += kern.get((name, names[i + 1]), 0)
    return f'<path d="{pen.getCommands()}" fill="{colour}"/>', (x - tracking) * scale


def _kerning(font: TTFont) -> dict:
    """Pair kerning from the GPOS 'kern' feature (format 1 pairs and format 2 classes)."""
    pairs: dict = {}
    if "GPOS" not in font:
        return pairs
    gpos = font["GPOS"].table
    lookups = set()
    for record in gpos.FeatureList.FeatureRecord:
        if record.FeatureTag == "kern":
            lookups.update(record.Feature.LookupListIndex)
    for index in lookups:
        lookup = gpos.LookupList.Lookup[index]
        for sub in lookup.SubTable:
            if lookup.LookupType == 9:
                sub = sub.ExtSubTable
            if getattr(sub, "LookupType", 2) != 2 and lookup.LookupType not in (2, 9):
                continue
            if sub.Format == 1:
                for first, pairset in zip(sub.Coverage.glyphs, sub.PairSet, strict=True):
                    for rec in pairset.PairValueRecord:
                        value = getattr(rec.Value1, "XAdvance", 0) or 0
                        pairs.setdefault((first, rec.SecondGlyph), value)
            elif sub.Format == 2:
                class1 = sub.ClassDef1.classDefs
                class2 = sub.ClassDef2.classDefs
                for first in sub.Coverage.glyphs:
                    row = sub.Class1Record[class1.get(first, 0)]
                    for second, c2 in class2.items():
                        value = getattr(row.Class2Record[c2].Value1, "XAdvance", 0) or 0
                        if value:
                            pairs.setdefault((first, second), value)
    return pairs


def lockup(card: str, tabs: tuple[str, str, str], word: str, name: str, title: str,
           background: str | None = None) -> None:
    """Horizontal lockup: symbol 256 tall, wordmark cap height = card stack height x 0.5."""
    text, width = wordmark("Evrakçı", 118, word)
    gap = 56
    total = 256 + gap + width + 24
    body = []
    if background:
        body.append(f'<rect width="{total:.0f}" height="256" fill="{background}"/>')
    body.append(symbol_paths(card, tabs))
    body.append(f'<g transform="translate({256 + gap - 24} 69)">{text}</g>')
    (KIT / name).write_text(svg(f"0 0 {total:.0f} 256", "\n  ".join(body), title),
                            encoding="utf-8")


def stacked(card: str, tabs: tuple[str, str, str], word: str, name: str, title: str) -> None:
    text, width = wordmark("Evrakçı", 70, word)
    total_w = max(256, width + 32)
    sx = (total_w - 256) / 2
    body = [f'<g transform="translate({sx:.1f} 0)">{symbol_paths(card, tabs)}</g>',
            f'<g transform="translate({(total_w - width) / 2:.1f} 270)">{text}</g>']
    (KIT / name).write_text(svg(f"0 0 {total_w:.0f} 366", "\n  ".join(body), title),
                            encoding="utf-8")


def build() -> None:
    KIT.mkdir(exist_ok=True)
    colour_tabs = (MANILA, ORANGE, MANILA)
    brand_tabs = (GREEN, ORANGE, GREEN)
    title = "Evrakçı"
    files = {
        "evrakci-symbol-black.svg": svg("0 0 256 256", symbol_paths(INK, (INK,) * 3), title),
        "evrakci-symbol-white.svg": svg("0 0 256 256", symbol_paths(WHITE, (WHITE,) * 3), title),
        "evrakci-symbol-green.svg": svg("0 0 256 256", symbol_paths(GREEN, (GREEN,) * 3), title),
        "evrakci-symbol-colour.svg": svg("0 0 256 256", symbol_paths(GREEN, brand_tabs), title),
        "evrakci-app-icon.svg": svg(
            "0 0 256 256",
            f'<rect width="256" height="256" rx="56" fill="{GREEN}"/>\n  '
            f'<g transform="translate(25.6 25.6) scale(.8)">'
            f"{symbol_paths(MANILA, colour_tabs)}</g>", title),
        "evrakci-symbol-16.svg": svg("0 0 16 16", small_symbol(GREEN, brand_tabs), title),
        "evrakci-app-icon-16.svg": svg("0 0 16 16", small_tile(MANILA, colour_tabs, GREEN),
                                       title),
    }
    for name, text in files.items():
        (KIT / name).write_text(text, encoding="utf-8")
    lockup(GREEN, brand_tabs, INK, "evrakci-horizontal-colour.svg", title)
    lockup(INK, (INK,) * 3, INK, "evrakci-horizontal-black.svg", title)
    lockup(WHITE, (WHITE,) * 3, WHITE, "evrakci-horizontal-white.svg", title)
    lockup(MANILA, colour_tabs, WHITE, "evrakci-horizontal-on-green.svg", title,
           background=GREEN)
    stacked(GREEN, brand_tabs, INK, "evrakci-stacked-colour.svg", title)
    stacked(INK, (INK,) * 3, INK, "evrakci-stacked-black.svg", title)

    # App copies
    linux = (KIT / "evrakci-app-icon.svg").read_text(encoding="utf-8")
    (ROOT / "packaging/linux/evrakci.svg").write_text(
        linux.replace('viewBox="0 0 256 256">',
                      'viewBox="0 0 256 256" width="256" height="256">'), encoding="utf-8")
    small = (KIT / "evrakci-app-icon-16.svg").read_text(encoding="utf-8")
    (ROOT / "src/evrakci/ui/logo_data.py").write_text(
        '"""The app icon (docs/logo/kit, built by docs/logo/build_kit.py). Do not edit."""\n'
        "# ruff: noqa: E501\n\n"
        f"APP_ICON_SVG = {linux!r}\n\n"
        f"# Pixel-grid cut used at 24 px and below.\nAPP_ICON_SMALL_SVG = {small!r}\n",
        encoding="utf-8")
    print("built", len(list(KIT.glob("*.svg"))), "SVGs")
    build_raster()


def build_raster() -> None:
    """PNG exports and packaging/evrakci.ico, rendered by Qt (pixel-grid cut at 24 px and below)."""
    import io
    import os

    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PIL import Image
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice, QRectF, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])  # noqa: F841 (Qt needs one)

    def render(svg_text: str, width: int, height: int) -> QImage:
        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        QSvgRenderer(QByteArray(svg_text.encode())).render(painter, QRectF(0, 0, width, height))
        painter.end()
        return image

    def to_pil(image: QImage) -> Image.Image:
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        image.save(buffer, "PNG")
        return Image.open(io.BytesIO(bytes(buffer.data()))).convert("RGBA")

    png = KIT / "png"
    png.mkdir(exist_ok=True)
    large = (KIT / "evrakci-app-icon.svg").read_text(encoding="utf-8")
    small = (KIT / "evrakci-app-icon-16.svg").read_text(encoding="utf-8")
    sizes = (256, 128, 64, 48, 32, 24, 20, 16)
    icons = [to_pil(render(small if s <= 24 else large, s, s)) for s in sizes]
    for image in icons:
        image.save(png / f"evrakci-app-icon-{image.width}.png")
    icons[0].save(ROOT / "packaging/evrakci.ico", sizes=[(i.width, i.height) for i in icons],
                  append_images=icons[1:])
    for name in ("horizontal-colour", "horizontal-on-green", "horizontal-white",
                 "horizontal-black", "stacked-colour", "symbol-colour"):
        text = (KIT / f"evrakci-{name}.svg").read_text(encoding="utf-8")
        renderer = QSvgRenderer(QByteArray(text.encode()))
        box = renderer.viewBoxF()
        width = 1024 if name.startswith("symbol") else 1200
        height = round(width * box.height() / box.width())
        render(text, width, height).save(str(png / f"evrakci-{name}.png"))
    print("built packaging/evrakci.ico and", len(list(png.glob("*.png"))), "PNGs")


if __name__ == "__main__":
    build()
