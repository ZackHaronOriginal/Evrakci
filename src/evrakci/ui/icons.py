"""The icon set: 24px, 1.75 stroke, round caps (the Kartotek sprite, see DESIGN.md).

Icons are kept as SVG path data in code so the frozen app needs no data files. `icon()` paints
one in any token colour; `icon_file()` writes one to a cache folder for stylesheet `url()`s.
"""
from __future__ import annotations

import tempfile
from functools import cache
from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, QSize, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

from evrakci.ui import theme
from evrakci.ui.logo_data import APP_ICON_SMALL_SVG, APP_ICON_SVG

PATHS: dict[str, str] = {
    "undo": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 0 12h-3"/>',
    "redo": '<path d="m15 14 5-5-5-5"/><path d="M20 9H10a6 6 0 0 0 0 12h3"/>',
    "funnel": '<path d="M3 4h18l-7 8.5V19l-4 2v-8.5z"/>',
    "sc": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M8.1 8.1 20 20M8.1 15.9 20 4"/>',  # noqa: E501
    "qr": '<rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><path d="M14 14h3v3h-3zM20 14v1M14 20h1M18 18h3v3h-3z"/>',  # noqa: E501
    "tpl": '<rect x="4" y="3" width="16" height="18" rx="1"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    "rot": '<path d="M20 12a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/>',
    "del": '<path d="M4 7h16M10 11v6M14 11v6M6 7l1 13h10l1-13M9 7V4h6v3"/>',
    "warn": '<path d="M12 3 2 20h20z"/><path d="M12 10v4M12 17v.5"/>',
    "ok": '<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
    "no": '<circle cx="12" cy="12" r="9"/><path d="M8 12h8"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7"/>',
    "save": '<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v5h7V3M8 21v-7h8v7"/>',
    "open": '<path d="M14 4h6v6M20 4l-9 9M18 14v6H4V6h6"/>',
    "merge": '<path d="M6 4v5a6 6 0 0 0 6 6h6M15 12l3 3-3 3M6 20v-3"/>',
    "blank": '<path d="M6 3h9l4 4v14H6z" stroke-dasharray="3 2.5"/>',
    "ch": '<path d="m9 6 6 6-6 6"/>',
    "chl": '<path d="m15 6-6 6 6 6"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "box": '<path d="M4 8V4h4M16 4h4v4M20 16v4h-4M8 20H4v-4"/>',
    "grid": '<path d="M3 9h18M3 15h18M9 3v18M15 3v18"/>',
    "play": '<path d="M7 4.5v15l12-7.5z"/>',
    "pen": '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    "clock": '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
    "folder": '<path d="M3 6h6l2 2h10v11H3z"/>',
    "file": '<path d="M6 3h9l4 4v14H6z"/><path d="M14 3v5h5"/>',
    "up": '<path d="M12 19V5M6 11l6-6 6 6"/>',
    "down": '<path d="M12 5v14M6 13l6 6 6-6"/>',
    "drop": '<path d="M12 4v11M7 10l5 5 5-5M4 19h16"/>',
    "print": '<path d="M7 9V3h10v6M7 17H4v-8h16v8h-3M7 14h10v7H7z"/>',
    "sheet": '<rect x="3" y="4" width="18" height="16" rx="1"/><path d="M3 9h18M3 14h18M9 4v16"/>',
    "book": '<path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z"/><path d="M4 21V5M8 7h7"/>',
    "grip": '<path d="M9 6h.01M15 6h.01M9 12h.01M15 12h.01M9 18h.01M15 18h.01" stroke-width="3"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',  # noqa: E501
    "x": '<path d="M6 6l12 12M18 6 6 18"/>',
    "chd": '<path d="m6 9 6 6 6-6"/>',
    "chu": '<path d="m6 15 6-6 6 6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7.5v.5"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="1"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',  # noqa: E501
}


def svg(name: str, colour: str, stroke: float = 1.75) -> str:
    """One icon as a standalone SVG document, stroked in `colour` (a hex value)."""
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
