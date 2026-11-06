import pytest
from conftest import needs_rapidocr
from fakes import render_line

from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.ocr.models import ModelFile, ensure_model, official_model


def test_checksum_mismatch_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("EVRAKCI_MODEL_DIR", str(tmp_path))
    model = ModelFile("x", "https://invalid.invalid/x.onnx", "0" * 64, "x.onnx")
    (tmp_path / "x.onnx").write_bytes(b"wrong")
    with pytest.raises(EngineUnavailable):
        ensure_model(model, download=False)
    assert not (tmp_path / "x.onnx").exists()


def test_missing_model_without_download(tmp_path, monkeypatch):
    monkeypatch.setenv("EVRAKCI_MODEL_DIR", str(tmp_path))
    model = ModelFile("x", "https://invalid.invalid/x.onnx", "0" * 64, "x.onnx")
    with pytest.raises(EngineUnavailable, match="Model dosyası yok"):
        ensure_model(model, download=False)


def test_official_model_has_checksum():
    pytest.importorskip("rapidocr")
    m = official_model("PP-OCRv5", "rec", "latin_PP-OCRv5_rec_mobile")
    assert len(m.sha256) == 64 and m.file_name == "latin_PP-OCRv5_rec_mobile.onnx"


@needs_rapidocr
def test_reads_region():
    from evrakci.pipeline.ocr.rapid import RapidOcrEngine

    reading = RapidOcrEngine(download=False).read_region(render_line("Şişli Çağrı Öğün 2026"))
    assert "2026" in reading.text and reading.confidence > 0.5


@needs_rapidocr
def test_page_words_have_boxes():
    from evrakci.pipeline.ocr.rapid import RapidOcrEngine

    words = RapidOcrEngine(download=False).read_page(render_line("Kayıt 2026"))
    centres = [(w.box[0] + w.box[2]) / 2 for w in words]
    assert len(words) == 2 and centres[0] < centres[1]


def test_reading_order_groups_lines():
    from evrakci.pipeline.ocr.rapid import _reading_order

    lines = [
        ("b", (100, 8, 150, 40), 1.0),
        ("a", (0, 0, 50, 40), 1.0),
        ("c", (0, 60, 50, 100), 1.0),
    ]
    assert [t for t, _, _ in _reading_order(lines)] == ["a", "b", "c"]
