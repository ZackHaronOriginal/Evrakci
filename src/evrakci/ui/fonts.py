"""Bundled fonts: Inter (SIL OFL 1.1, see assets/fonts/OFL.txt) registered with Qt.

`register_fonts()` loads the static Inter files once; `font_stack()` is the family order for
the stylesheet; `tabular()` turns on tabular figures for numbers that line up in columns.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtGui import QFont, QFontDatabase

FONT_FILES = ("Inter-Regular.otf", "Inter-Medium.otf", "Inter-SemiBold.otf",
              "InterDisplay-SemiBold.otf")
FALLBACK_STACK = ["Segoe UI Variable", "Segoe UI"]

_loaded: list[str] | None = None


def font_dirs() -> list[Path]:
    """Where the font files may be: the package folder, then the folder build's lib/."""
    here = Path(__file__).resolve().parent / "assets" / "fonts"
    frozen = Path(sys.executable).resolve().parent / "lib" / "evrakci" / "ui" / "assets" / "fonts"
    return [here, frozen]


def register_fonts() -> list[str]:
    """Register the bundled fonts with Qt. Safe to call again; returns the family names."""
    global _loaded
    if _loaded is not None:
        return list(_loaded)
    folder = next((d for d in font_dirs() if d.is_dir()), None)
    families: list[str] = []
    if folder is not None:
        for name in FONT_FILES:
            path = folder / name
            if not path.is_file():
                continue
            font_id = QFontDatabase.addApplicationFont(str(path))
            if font_id < 0:
                continue
            for family in QFontDatabase.applicationFontFamilies(font_id):
                if family not in families:
                    families.append(family)
    _loaded = families
    return list(families)


def font_stack() -> list[str]:
    """Family order for the UI: Inter when it loaded, then the Windows system fonts."""
    register_fonts()
    return (["Inter"] if "Inter" in (_loaded or []) else []) + FALLBACK_STACK


def tabular(font: QFont) -> QFont:
    """Enable tabular figures ("tnum"), Qt 6.7+. Returns the font; a no-op on older Qt."""
    try:
        font.setFeature(QFont.Tag("tnum"), 1)
    except (AttributeError, TypeError):
        pass
    return font
