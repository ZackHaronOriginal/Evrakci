import pytest

from evrakci.pipeline.ocr.tesseract import TesseractEngine


def _tesseract_missing() -> str | None:
    return TesseractEngine().available()


needs_tesseract = pytest.mark.skipif(
    _tesseract_missing() is not None, reason="Tesseract (tur) kurulu değil"
)


def _rapidocr_missing() -> str | None:
    try:
        from evrakci.pipeline.ocr.rapid import RapidOcrEngine
    except ImportError:
        return "rapidocr yok"
    return RapidOcrEngine(download=False).available()


needs_rapidocr = pytest.mark.skipif(
    _rapidocr_missing() is not None, reason="RapidOCR veya modelleri yok"
)
