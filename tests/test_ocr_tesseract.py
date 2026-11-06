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


@needs_tesseract
def test_separate_tessdata_folder_with_only_the_language_file(tmp_path):
    import shutil

    from evrakci.pipeline.ocr.compare import _system_tessdata

    shutil.copy(_system_tessdata() / "tur.traineddata", tmp_path / "tur.traineddata")
    reading = TesseractEngine(tessdata_dir=tmp_path).read_region(render_line("Kayıt Şişli 2026"))
    assert reading.text == "Kayıt Şişli 2026"


def test_tessdata_best_env(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr.tesseract import tessdata_best_dir

    monkeypatch.setenv("EVRAKCI_TESSDATA_BEST", str(tmp_path))
    assert tessdata_best_dir() == tmp_path


def test_tur_best_checksum_checked(tmp_path, monkeypatch):
    from evrakci.pipeline.ocr.tesseract import TUR_BEST_SHA256, verify_tur_best

    (tmp_path / "tur.traineddata").write_bytes(b"truncated")
    assert len(TUR_BEST_SHA256) == 64 and verify_tur_best(tmp_path) is False
    assert not (tmp_path / "tur.traineddata").exists()
