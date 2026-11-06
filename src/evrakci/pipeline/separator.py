"""Printable QR separator sheets.

A separator sheet only marks a cut between documents. It is printed with the
same QR code on both sides, so it works in single- and double-sided scans.
"""

from __future__ import annotations

import io
from pathlib import Path

import segno
from PIL import Image, ImageDraw, ImageFont

SEPARATOR_PAYLOAD = "EVRAKCI-AYIRAC-1"
_PAYLOAD_PREFIX = "EVRAKCI-AYIRAC"

_A4_MM = (210, 297)
_QR_WIDTH_MM = 90


def is_separator_payload(text: str) -> bool:
    return text.startswith(_PAYLOAD_PREFIX)


def _mm_to_px(mm: float, dpi: int) -> int:
    return round(mm / 25.4 * dpi)


def render_separator_image(dpi: int = 150) -> Image.Image:
    """One A4 separator page as a grayscale image."""
    width, height = (_mm_to_px(mm, dpi) for mm in _A4_MM)
    page = Image.new("L", (width, height), 255)

    buffer = io.BytesIO()
    segno.make(SEPARATOR_PAYLOAD, error="h").save(buffer, kind="png", scale=10, border=4)
    buffer.seek(0)
    qr_size = _mm_to_px(_QR_WIDTH_MM, dpi)
    qr = Image.open(buffer).convert("L").resize((qr_size, qr_size), Image.Resampling.NEAREST)
    qr_top = (height - qr_size) // 2
    page.paste(qr, ((width - qr_size) // 2, qr_top))

    draw = ImageDraw.Draw(page)
    title_font = ImageFont.load_default(size=_mm_to_px(16, dpi))
    note_font = ImageFont.load_default(size=_mm_to_px(7, dpi))
    gap = _mm_to_px(12, dpi)
    draw.text((width // 2, qr_top - gap), "AYIRAÇ", fill=0, font=title_font, anchor="ms")
    draw.text(
        (width // 2, qr_top + qr_size + gap),
        "Bu sayfa çıktıya girmez",
        fill=0,
        font=note_font,
        anchor="mt",
    )
    return page


def make_separator_pdf(path: Path, sheets: int = 1) -> Path:
    """Write `sheets` separator sheets (front and back each) to `path`."""
    if sheets < 1:
        raise ValueError("sheets must be at least 1")
    dpi = 150
    image = render_separator_image(dpi=dpi)
    pages = [image] * (2 * sheets)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pages[0].save(path, save_all=True, append_images=pages[1:], resolution=dpi)
    return path
