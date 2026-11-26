import pikepdf
import zxingcpp

from evrakci.pipeline.separator import (
    SEPARATOR_PAYLOAD,
    is_separator_payload,
    make_separator_pdf,
    render_separator_image,
)


def test_payload_recognised():
    assert is_separator_payload(SEPARATOR_PAYLOAD)
    assert is_separator_payload("EVRAKCI-AYIRAC-2")
    assert not is_separator_payload("https://example.com")


def test_separator_pdf_has_front_and_back(tmp_path):
    path = make_separator_pdf(tmp_path / "ayirac.pdf", sheets=3)
    with pikepdf.open(path) as pdf:
        assert len(pdf.pages) == 6


def test_separator_image_qr_decodes():
    texts = [b.text for b in zxingcpp.read_barcodes(render_separator_image(dpi=100))]
    assert texts == [SEPARATOR_PAYLOAD]


def test_b057_separator_text_uses_inter_and_draws_turkish_letters():
    from PIL import Image, ImageDraw

    from evrakci.pipeline import separator

    assert separator._inter_path() is not None
    font = separator._font(80)
    assert "Inter" in font.getname()[0]

    def glyph(char, f):
        img = Image.new("L", (200, 200), 255)
        ImageDraw.Draw(img).text((20, 20), char, fill=0, font=f)
        return img.tobytes()

    # the missing-glyph box is what the font draws for a character it lacks
    assert glyph("\u00c7", font) != glyph("\uffff", font)
    assert glyph("\u0130", font) != glyph("\uffff", font)


def test_b057_separator_falls_back_when_font_is_missing(monkeypatch):
    from evrakci.pipeline import separator

    monkeypatch.setattr(separator, "_inter_path", lambda: None)
    assert render_separator_image(dpi=100).size == (827, 1169)


def test_b057_frozen_builds_carry_the_separator_font():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    freeze = (root / "packaging" / "freeze_setup.py").read_text(encoding="utf-8")
    assert "lib/evrakci/ui/assets/fonts" in freeze
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert '"evrakci.ui" = ["assets/fonts/*"]' in pyproject
