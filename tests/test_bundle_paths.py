import shutil
import stat
import sys

from evrakci.pipeline.ocr import tesseract
from evrakci.pipeline.ocr.models import app_dir


def fake_app(tmp_path, monkeypatch):
    folder = tmp_path / "Program Files" / "Evrakçı Uygulama"
    (folder / "tesseract").mkdir(parents=True)
    monkeypatch.setenv("EVRAKCI_UYGULAMA_KLASORU", str(folder))
    monkeypatch.delenv("EVRAKCI_TESSERACT", raising=False)
    return folder


def test_bundled_tesseract_first(tmp_path, monkeypatch):
    folder = fake_app(tmp_path, monkeypatch)
    name = "tesseract.exe" if sys.platform == "win32" else "tesseract"
    exe = folder / "tesseract" / name
    exe.write_text("#!/bin/sh\necho bundled\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    assert tesseract.find_tesseract() == exe


def test_bundled_tessdata_used(tmp_path, monkeypatch):
    folder = fake_app(tmp_path, monkeypatch)
    real = tesseract.tessdata_dir("best")
    monkeypatch.delenv("EVRAKCI_TESSDATA_BEST", raising=False)
    bundled = folder / "tessdata_best"
    bundled.mkdir()
    source = real / "tur.traineddata"
    if not source.is_file():
        import pytest

        pytest.skip("tur_best not downloaded here")
    shutil.copy(source, bundled / "tur.traineddata")
    assert tesseract.tessdata_dir("best") == bundled


def test_wrong_bundled_data_is_not_used(tmp_path, monkeypatch):
    folder = fake_app(tmp_path, monkeypatch)
    monkeypatch.delenv("EVRAKCI_TESSDATA_FAST", raising=False)
    (folder / "tessdata_fast").mkdir()
    (folder / "tessdata_fast" / "tur.traineddata").write_bytes(b"wrong")
    assert tesseract.tessdata_dir("fast") != folder / "tessdata_fast"
    assert (folder / "tessdata_fast" / "tur.traineddata").exists()  # never deletes bundled files


def test_not_frozen_means_no_app_dir(monkeypatch):
    monkeypatch.delenv("EVRAKCI_UYGULAMA_KLASORU", raising=False)
    assert app_dir() is None
