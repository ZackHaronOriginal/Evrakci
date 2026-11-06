import inspect
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_entry_points_call_freeze_support():
    import importlib

    from evrakci import app

    cli_main = importlib.import_module("evrakci.cli.main")
    for function in (cli_main.main, app.main):
        assert "freeze_support()" in inspect.getsource(function)


def test_notice_lists_components():
    notice = (ROOT / "packaging" / "licenses" / "NOTICE.txt").read_text(encoding="utf-8")
    for component in ("PySide6", "Qt", "Tesseract", "OCRmyPDF", "pikepdf", "cx_Freeze", "LGPL"):
        assert component in notice
    for text in ("LGPL-3.0.txt", "GPL-3.0.txt", "Apache-2.0.txt", "AGPL-3.0.txt"):
        assert (ROOT / "packaging" / "licenses" / text).is_file()


def test_build_refuses_wrong_tur_best(tmp_path):
    bad = tmp_path / "tur.traineddata"
    bad.write_bytes(b"wrong")
    result = subprocess.run(
        [sys.executable, str(ROOT / "packaging" / "build.py"), "--tur-best", str(bad), "--kontrol"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0 and "doğrulanamadı" in result.stderr


def test_build_check_mode_accepts_good_inputs(tmp_path):
    from evrakci.pipeline.ocr.tesseract import tessdata_dir

    good = tessdata_dir("best") / "tur.traineddata"
    if not good.is_file():
        pytest.skip("tur_best not downloaded here")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "packaging" / "build.py"),
            "--tur-best",
            str(good),
            "--kontrol",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
