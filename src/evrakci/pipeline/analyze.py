"""Look at each scanned page once: is it a QR separator, and how much ink does it have?"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium
import zxingcpp

from evrakci.pipeline.pdfium_lock import PDFIUM_LOCK
from evrakci.pipeline.separator import is_separator_payload

# A page with less ink than this share of its area counts as empty.
EMPTY_INK_RATIO = 0.003
# Pixels darker than this (0-255) count as ink.
_INK_LEVEL = 160
# Ignore this share of each edge; scanners leave dark borders.
_EDGE_MARGIN = 0.06
_RENDER_DPI = 100
_PT_MM = 25.4 / 72  # one PDF point in millimetres


class BatchError(Exception):
    """A scanned file that cannot be used. The message is shown to staff (Turkish)."""


@dataclass(frozen=True)
class PageInfo:
    ink_ratio: float
    is_separator: bool
    # The page as displayed, before the job's own rotation, in millimetres; 0.0 = unknown
    # (jobs made before the sizes were kept: the window reads them once when the job opens).
    width_mm: float = 0.0
    height_mm: float = 0.0

    @property
    def has_size(self) -> bool:
        return self.width_mm > 0 and self.height_mm > 0

    @property
    def is_empty(self) -> bool:
        return self.ink_ratio < EMPTY_INK_RATIO and not self.is_separator


def _ink_ratio(image) -> float:
    w, h = image.size
    mx, my = int(w * _EDGE_MARGIN), int(h * _EDGE_MARGIN)
    histogram = image.crop((mx, my, w - mx, h - my)).histogram()
    total = sum(histogram)
    return sum(histogram[:_INK_LEVEL]) / total if total else 0.0


def _is_separator(image) -> bool:
    found = zxingcpp.read_barcodes(image, formats=zxingcpp.BarcodeFormat.QRCode)
    return any(is_separator_payload(barcode.text) for barcode in found)


def _open(path: Path) -> pdfium.PdfDocument:
    if not path.is_file():
        raise BatchError(f"Dosya bulunamadı: {path.name}")
    with PDFIUM_LOCK:
        try:
            pdf = pdfium.PdfDocument(str(path))
        except pdfium.PdfiumError as error:
            raise BatchError(f"PDF açılamadı: {path.name}") from error
        if len(pdf) == 0:
            pdf.close()
            raise BatchError(f"PDF boş: {path.name}")
    return pdf


def count_pages(path: Path) -> int:
    """Page count, with the same checks as `analyze_pdf`. Fast: nothing is rendered."""
    pdf = _open(Path(path))
    with PDFIUM_LOCK:
        try:
            return len(pdf)
        finally:
            pdf.close()


def _mm(points: float) -> float:
    return round(points * _PT_MM, 1)


def read_page_sizes(path: Path) -> list[tuple[float, float]]:
    """(width, height) in millimetres of every page, as displayed. Nothing is rendered: one
    open of the file and a size lookup per page."""
    path = Path(path)
    pdf = _open(path)
    try:
        with PDFIUM_LOCK:
            total = len(pdf)
        sizes = []
        for index in range(total):
            with PDFIUM_LOCK:  # per page, so thumbnail threads can render in between
                width, height = pdf.get_page_size(index)
            sizes.append((_mm(width), _mm(height)))
        return sizes
    except pdfium.PdfiumError as error:
        raise BatchError(f"PDF açılamadı: {path.name}") from error
    finally:
        with PDFIUM_LOCK:
            pdf.close()


def analyze_pdf(path: Path, progress: Callable[[int, int], None] | None = None) -> list[PageInfo]:
    path = Path(path)
    pdf = _open(path)
    try:
        total = len(pdf)
        infos = []
        for index in range(total):
            try:
                with PDFIUM_LOCK:  # per page, so thumbnail threads can render in between
                    page = pdf[index]
                    try:
                        width, height = (_mm(side) for side in page.get_size())
                        bitmap = page.render(scale=_RENDER_DPI / 72, grayscale=True)
                        image = bitmap.to_pil().convert("L")
                    finally:
                        page.close()
            except pdfium.PdfiumError as error:
                raise BatchError(f"Sayfa {index + 1} okunamadı: {path.name}") from error
            infos.append(PageInfo(_ink_ratio(image), _is_separator(image), width, height))
            if progress:
                progress(index + 1, total)
        return infos
    finally:
        with PDFIUM_LOCK:
            pdf.close()
