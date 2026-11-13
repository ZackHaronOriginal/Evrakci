"""Print the QR separator sheets (A4, QR on both sides of each sheet) with QPrinter."""

from __future__ import annotations

from PIL import Image
from PySide6.QtCore import QMarginsF, QRect
from PySide6.QtGui import QImage, QPageLayout, QPageSize, QPainter
from PySide6.QtPrintSupport import QPrinter

from evrakci.pipeline.separator import render_separator_image

SHEETS = (1, 200)  # what "Kaç adet" accepts


def prepare(printer: QPrinter) -> None:
    """A4, portrait, no margins (the sheet is drawn edge to edge, as the PDF is)."""
    printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    printer.setPageOrientation(QPageLayout.Orientation.Portrait)
    printer.setPageMargins(QMarginsF(0, 0, 0, 0), QPageLayout.Unit.Millimeter)


def _to_qimage(page: Image.Image) -> QImage:
    gray = page.convert("L")
    data = gray.tobytes()
    image = QImage(data, gray.width, gray.height, gray.width, QImage.Format.Format_Grayscale8)
    return image.copy()  # own the pixels: `data` goes away with this frame


def print_separators(printer: QPrinter, sheets: int) -> int:
    """Draw `sheets` sheets, front and back each, and return the number of pages printed.

    The page is rendered once at the printer's resolution and reused, so 200 sheets cost the
    same as one. Raises ValueError for a count outside 1..200 and RuntimeError when the printer
    refuses to start.
    """
    if not SHEETS[0] <= sheets <= SHEETS[1]:
        raise ValueError("sheets must be between 1 and 200")
    prepare(printer)
    image = _to_qimage(render_separator_image(dpi=max(150, min(printer.resolution(), 600))))
    painter = QPainter()
    if not painter.begin(printer):
        raise RuntimeError("printer did not start")
    try:
        pages = 2 * sheets
        for number in range(pages):
            if number:
                printer.newPage()
            area = painter.viewport()
            painter.drawImage(QRect(0, 0, area.width(), area.height()), image)
    finally:
        painter.end()
    return 2 * sheets
