import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")  # window tests run without a screen

import pytest

from evrakci.pipeline.ocr.tesseract import TesseractEngine


@pytest.fixture(autouse=True)
def _private_ui_settings(tmp_path, monkeypatch):
    """Every test gets its own window-settings file (prefs.default_settings_file), so no test
    reads or writes the real ~/.config/Evrakçı/Evrakçı.ini and one run cannot leak column
    widths, geometry or the last tab into the next."""
    monkeypatch.setenv("EVRAKCI_UI_AYARLAR", str(tmp_path / "ui-ayarlar.ini"))


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
