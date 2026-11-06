import pytest

from evrakci.pipeline.ocr.tesseract import TesseractEngine


def _tesseract_missing() -> str | None:
    return TesseractEngine().available()


needs_tesseract = pytest.mark.skipif(
    _tesseract_missing() is not None, reason="Tesseract (tur) kurulu değil"
)
