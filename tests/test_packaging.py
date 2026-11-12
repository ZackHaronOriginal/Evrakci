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


def test_iss_has_required_settings():
    iss = (ROOT / "packaging" / "evrakci.iss").read_text(encoding="utf-8-sig")
    assert "AppId={{" in iss and "LicenseFile=" in iss
    assert "Languages\\Turkish.isl" in iss
    assert "evrakci-arayuz.exe" in iss and "{autodesktop}" in iss
    lowered = iss.lower()
    assert "userappdata" not in lowered
    # Job data lives in {localappdata}\Evrakci: only the OCR cache below it may be removed.
    for line in lowered.splitlines():
        if "{localappdata}" in line and not line.lstrip().startswith((";", "//")):
            assert "evrakci\\ascii" in line, line


def test_smoke_script_makes_and_checks_a_pdf(tmp_path):
    from evrakci.pipeline.ocr.tesseract import default_engine

    reason = default_engine().available()
    if reason:
        pytest.skip(reason)
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "packaging" / "smoke_test.py"),
            "--komut",
            sys.executable,
            "--modul",
            "--klasor",
            str(tmp_path),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Duman testi geçti" in result.stdout


def test_iss_output_and_privileges():
    iss = (ROOT / "packaging" / "evrakci.iss").read_text(encoding="utf-8-sig")
    assert "OutputDir={#SourcePath}..\\dist" in iss  # repo-level dist\, where CI uploads from
    assert "PrivilegesRequired=lowest" in iss  # per-user by default; matches the HKCU PATH entry


def test_iss_removes_old_files_and_cleans_path():
    iss = (ROOT / "packaging" / "evrakci.iss").read_text(encoding="utf-8-sig")
    assert "[InstallDelete]" in iss
    for folder in ("lib", "tesseract", "tessdata_best", "licenses"):
        assert f'Name: "{{app}}\\{folder}"' in iss
    assert "CurUninstallStepChanged" in iss and "RemoveFromPath" in iss and "AddToPath" in iss
    # Only this user's cache: the shared ProgramData folder is never deleted as a whole.
    assert "[UninstallDelete]" in iss and "RemoveSharedCache" in iss


def test_notice_covers_more_components():
    notice = (ROOT / "packaging" / "licenses" / "NOTICE.txt").read_text(encoding="utf-8")
    for component in ("img2pdf", "cryptography", "cffi", "leptonica", "libtiff"):
        assert component in notice
    # No LGPL-2.1 part ships any more (the old Tesseract DLLs); its text is not needed.
    assert not (ROOT / "packaging" / "licenses" / "LGPL-2.1.txt").exists()


def test_collect_licenses_writes_versions(tmp_path):
    sys.path.insert(0, str(ROOT / "packaging"))
    from collect_licenses import collect_from_build
    from test_packaging_review2 import fake_lib

    collect_from_build(fake_lib(tmp_path / "lib", "pikepdf", "openpyxl"), tmp_path)
    versions = (tmp_path / "VERSIONS.txt").read_text(encoding="utf-8")
    assert "pikepdf==" in versions and "openpyxl==" in versions
    assert any((tmp_path / "python").rglob("*"))
