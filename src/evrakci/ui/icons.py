"""The icon set: Lucide (ISC, see lucide.py), 24px, 1.75 stroke by default, round caps.

Icons are kept as SVG markup in code so the frozen app needs no data files. Old short names
(`ALIASES`) still work. `icon()` paints
one in any token colour; `icon_file()` writes one to a cache folder for stylesheet `url()`s.
"""
from __future__ import annotations

import tempfile
from functools import cache
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from evrakci.ui import lucide, theme
from evrakci.ui.logo_data import APP_ICON_SMALL_SVG, APP_ICON_SVG

# App-specific glyphs with no Lucide equivalent (inner SVG markup, 24px viewBox). None today.
PATHS: dict[str, str] = {}

# Legacy short names -> Lucide names. A key is never itself a Lucide name.
ALIASES: dict[str, str] = {
    "undo": "undo-2", "redo": "redo-2", "sc": "scissors", "qr": "qr-code",
    "tpl": "layout-template", "rot": "rotate-cw", "del": "trash-2", "warn": "triangle-alert",
    "ok": "circle-check", "no": "circle-minus", "open": "external-link", "blank": "square-dashed",
    "ch": "chevron-right", "chl": "chevron-left", "box": "scan", "grid": "grid-3x3",
    "pen": "pencil", "up": "arrow-up", "down": "arrow-down", "drop": "download",
    "print": "printer", "grip": "grip-vertical", "gear": "settings",
    "chd": "chevron-down", "chu": "chevron-up", "stop": "square",
}


def resolve(name: str) -> str:
    """The Lucide (or PATHS) name behind `name`, following legacy aliases."""
    name = ALIASES.get(name, name)
    if name not in lucide.ICONS and name not in PATHS:
        raise KeyError(f"unknown icon: {name}")
    return name


def svg(name: str, colour: str, stroke: float = 1.75) -> str:
    """One icon as a standalone SVG document, stroked in `colour` (a hex value)."""
    name = resolve(name)
    if name in lucide.ICONS:
        return lucide.svg(name, colour, stroke)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{colour}" stroke-width="{stroke}" stroke-linecap="round" '
        f'stroke-linejoin="round">{PATHS[name]}</svg>'
    )


def _hex(colour: str) -> str:
    return theme.TOKENS.get(colour, colour)


def paint(painter: QPainter, name: str, rect: QRectF, colour: str, stroke: float = 1.75) -> None:
    """Draw an icon into `rect` with an open painter (crisp at any device pixel ratio)."""
    QSvgRenderer(QByteArray(svg(name, _hex(colour), stroke).encode())).render(painter, rect)


@cache
def pixmap(name: str, colour: str = "ink", size: int = 18, ratio: float = 2.0,
           stroke: float = 1.75) -> QPixmap:
    image = QPixmap(QSize(round(size * ratio), round(size * ratio)))
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    paint(painter, name, QRectF(0, 0, image.width(), image.height()), colour, stroke)
    painter.end()
    image.setDevicePixelRatio(ratio)
    return image


@cache
def icon(name: str, colour: str = "ink", disabled: str = "rule_strong") -> QIcon:
    """A QIcon in a token colour (or hex), with a muted variant for disabled widgets."""
    result = QIcon()
    for size in (16, 18, 24, 32):
        result.addPixmap(pixmap(name, colour, size), QIcon.Mode.Normal)
        result.addPixmap(pixmap(name, colour, size), QIcon.Mode.Active)
        result.addPixmap(pixmap(name, colour, size), QIcon.Mode.Selected)
        result.addPixmap(pixmap(name, disabled, size), QIcon.Mode.Disabled)
    return result


@cache
def icon_file(name: str, colour: str = "ink", stroke: float = 1.75) -> str:
    """Path (forward slashes) of an icon written to the cache, for stylesheet url()s."""
    folder = Path(tempfile.gettempdir()) / "evrakci-simgeler"
    folder.mkdir(parents=True, exist_ok=True)
    hex_colour = _hex(colour)
    path = folder / f"{name}-{hex_colour.lstrip('#')}-{stroke}.svg"
    text = svg(name, hex_colour, stroke)
    if not path.is_file() or path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")
    return path.as_posix()


@cache
def app_icon() -> QIcon:
    """The window and taskbar icon (docs/logo/kit); the pixel-grid cut at 24 px and below."""
    result = QIcon()
    large = QSvgRenderer(QByteArray(APP_ICON_SVG.encode()))
    small = QSvgRenderer(QByteArray(APP_ICON_SMALL_SVG.encode()))
    for size in (16, 20, 24, 32, 48, 64, 128, 256):
        image = QPixmap(size, size)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        (small if size <= 24 else large).render(painter, QRectF(0, 0, size, size))
        painter.end()
        result.addPixmap(image)
    return result
