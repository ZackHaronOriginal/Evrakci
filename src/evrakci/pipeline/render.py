"""Render job pages as images, and convert millimetre boxes to pixels."""

from __future__ import annotations

from pathlib import Path

import pypdfium2 as pdfium
from PIL import Image

DPI = 300


def render_page(batch_file: Path, index: int, rotation: int = 0, dpi: int = DPI) -> Image.Image:
    """The page as displayed (its own /Rotate applied), turned `rotation` degrees clockwise."""
    pdf = pdfium.PdfDocument(str(batch_file))
    try:
        page = pdf[index]
        try:
            image = page.render(scale=dpi / 72, grayscale=True).to_pil().convert("L")
        finally:
            page.close()
    finally:
        pdf.close()
    if rotation % 360:
        image = image.rotate(-(rotation % 360), expand=True, fillcolor=255)
    return image


class PageRenderer:
    """Render several pages of one PDF while opening it only once."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._pdf = None

    def __enter__(self) -> PageRenderer:
        self._pdf = pdfium.PdfDocument(str(self.path))
        return self

    def __exit__(self, *exc) -> None:
        self._pdf.close()

    def render(self, index: int, rotation: int = 0, dpi: int = DPI) -> Image.Image:
        page = self._pdf[index]
        try:
            image = page.render(scale=dpi / 72, grayscale=True).to_pil().convert("L")
        finally:
            page.close()
        if rotation % 360:
            image = image.rotate(-(rotation % 360), expand=True, fillcolor=255)
        return image


def mm_box_to_pixels(
    box_mm: tuple[float, float, float, float], size: tuple[int, int], dpi: int = DPI
) -> tuple[int, int, int, int] | None:
    """Pixel box clipped to the image, or None when it lies wholly outside."""
    x0, y0, x1, y1 = (round(v / 25.4 * dpi) for v in box_mm)
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(size[0], x1), min(size[1], y1)
    if x0 >= x1 or y0 >= y1:
        return None
    return x0, y0, x1, y1
