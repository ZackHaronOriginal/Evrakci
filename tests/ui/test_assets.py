"""Bundled font (Inter) and the Lucide icon set with its legacy aliases."""
from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtGui import QFont, QFontDatabase, QRawFont

from evrakci.ui import fonts, icons, lucide

TURKISH = "İıŞşĞğÇçÖöÜü"


def test_fonts_register_inter(qapp):
    families = fonts.register_fonts()
    assert "Inter" in families
    assert fonts.register_fonts() == families  # idempotent
    assert "Inter" in QFontDatabase.families()
    assert fonts.font_stack() == ["Inter", "Segoe UI Variable", "Segoe UI"]


def test_font_files_and_licence_ship():
    folder = Path(fonts.__file__).parent / "assets" / "fonts"
    for name in (*fonts.FONT_FILES, "OFL.txt"):
        assert (folder / name).is_file(), name
    assert "The Inter Project Authors" in (folder / "OFL.txt").read_text(encoding="utf-8")


def test_inter_registers_and_has_turkish_glyphs(qapp):
    """Inter must load on every platform, and each bundled file must draw every Turkish letter.
    The glyphs are checked on the file itself (QRawFont), not through the platform's family
    lookup, which on Windows offscreen may answer for a different font."""
    assert "Inter" in fonts.register_fonts()
    assert fonts.font_stack()[0] == "Inter"
    folder = Path(fonts.__file__).parent / "assets" / "fonts"
    for name in fonts.FONT_FILES:
        raw = QRawFont(str(folder / name), 16)
        assert raw.isValid(), name
        for char in TURKISH:
            # ord(): PySide converts a non-ASCII str to QChar wrongly.
            assert raw.supportsCharacter(ord(char)), (name, char)


def test_tabular_figures_flag(qapp):
    font = fonts.tabular(QFont("Inter"))
    assert font.family() == "Inter"


def test_font_stack_without_inter(monkeypatch):
    monkeypatch.setattr(fonts, "_loaded", [])
    assert fonts.font_stack() == ["Segoe UI Variable", "Segoe UI"]


def test_lucide_entries_are_plain_markup():
    assert len(lucide.ICONS) >= 70
    for name, inner in lucide.ICONS.items():
        assert inner.strip(), name
        assert "<svg" not in inner, name


@pytest.mark.parametrize("name", sorted(lucide.ICONS))
def test_every_lucide_icon_renders(qapp, name):
    image = icons.pixmap(name, "#112233", 24, 1.0).toImage()
    opaque = sum(1 for x in range(image.width()) for y in range(image.height())
                 if image.pixelColor(x, y).alpha() > 0)
    assert opaque > 0, name


def test_stroke_option():
    assert 'stroke-width="2.0"' in lucide.svg("check")
    assert 'stroke-width="1.75"' in icons.svg("check", "#000000")
    assert 'stroke-width="1.5"' in icons.svg("check", "#000000", 1.5)


def test_legacy_aliases_resolve(qapp):
    assert icons.ALIASES
    for old, new in icons.ALIASES.items():
        assert new in lucide.ICONS or new in icons.PATHS, old
        assert icons.resolve(old) == new
        assert not icons.pixmap(old, "ink", 16, 1.0).isNull()


def test_no_name_collisions():
    assert not set(icons.ALIASES) & set(lucide.ICONS)
    assert not set(icons.PATHS) & set(lucide.ICONS)
    assert not set(icons.PATHS) & set(icons.ALIASES)


def test_unknown_icon_raises():
    with pytest.raises(KeyError):
        icons.svg("nope", "#000000")


def test_icon_file_written(qapp):
    path = Path(icons.icon_file("warn", "ink"))
    assert path.is_file()
    assert "<svg" in path.read_text(encoding="utf-8")
