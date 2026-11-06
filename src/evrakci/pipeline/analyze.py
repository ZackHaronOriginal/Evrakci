"""Look at each scanned page once: is it a QR separator, and how much ink does it have?"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pypdfium2 as pdfium
import zxingcpp

from evrakci.pipeline.separator import is_separator_payload

# A page with less ink than this share of its area counts as empty.
EMPTY_INK_RATIO = 0.003
# Pixels darker than this (0-255) count as ink.
_INK_LEVEL = 160
# Ignore this share of each edge; scanners leave dark borders.
_EDGE_MARGIN = 0.06
_RENDER_DPI = 100


class BatchError(Exception):
    """A scanned file that cannot be used. The message is shown to staff (Turkish)."""


@dataclass(frozen=True)
class PageInfo:
    ink_ratio: float
    is_separator: bool

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


def analyze_pdf(
    path: Path, progress: Callable[[int, int], None] | None = None
) -> list[PageInfo]:
    path = Path(path)
    if not path.is_file():
        raise BatchError(f"Dosya bulunamadı: {path.name}")
    try:
        pdf = pdfium.PdfDocument(str(path))
    except pdfium.PdfiumError as error:
        raise BatchError(f"PDF açılamadı: {path.name}") from error
    try:
        total = len(pdf)
        if total == 0:
            raise BatchError(f"PDF boş: {path.name}")
        infos = []
        for index in range(total):
            page = pdf[index]
            try:
                bitmap = page.render(scale=_RENDER_DPI / 72, grayscale=True)
                image = bitmap.to_pil().convert("L")
            finally:
                page.close()
            infos.append(PageInfo(_ink_ratio(image), _is_separator(image)))
            if progress:
                progress(index + 1, total)
        return infos
    finally:
        pdf.close()
