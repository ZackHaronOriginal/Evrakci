from conftest import needs_tesseract
from fakes import render_line

from evrakci.pipeline.ocr.tesseract import TesseractEngine


@needs_tesseract
def test_reads_turkish_region():
    reading = TesseractEngine().read_region(render_line("İSTANBUL Şişli Çağrı Öğün ığdır"))
    assert reading.text == "İSTANBUL Şişli Çağrı Öğün ığdır" and reading.confidence > 0.5


@needs_tesseract
def test_page_words_have_boxes():
    words = TesseractEngine().read_page(render_line("Kayıt 2026"))
    assert [w.text for w in words] == ["Kayıt", "2026"]
    assert all(w.box[2] > w.box[0] and w.box[3] > w.box[1] for w in words)


def test_missing_language_reported(tmp_path):
    assert "dil" in (TesseractEngine(lang="tur", tessdata_dir=tmp_path).available() or "")
