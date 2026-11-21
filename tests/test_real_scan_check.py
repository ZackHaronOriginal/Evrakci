import importlib.util
import shutil
import sys
from pathlib import Path

import pytest
from fakes import make_pdf, qr_page, text_page

TOOL = Path(__file__).resolve().parents[1] / "tools" / "real_scan_check.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("real_scan_check", TOOL)
    module = importlib.util.module_from_spec(spec)
    sys.modules["real_scan_check"] = module
    spec.loader.exec_module(module)
    return module


def scans(tmp_path):
    folder = tmp_path / "taramalar"
    folder.mkdir()
    make_pdf(folder / "a.pdf", [text_page("x")] * 2 + [qr_page()] + [text_page("y")] * 3)
    make_pdf(folder / "b.pdf", [text_page("z")] * 2)
    return folder


def test_window_and_cli_agree_with_ocr_off(tmp_path, capsys, monkeypatch):
    tool = load_tool()
    out = tmp_path / "sonuc"
    assert tool.main([str(scans(tmp_path)), "--cikti", str(out), "--ocr", "kapali"]) == 0
    text = capsys.readouterr().out
    assert "RESULT: PASS" in text and "index.xlsx values" in text
    assert "export, window function, OCR off" in text and "export, CLI, OCR off" in text
    assert (out / "ozet.txt").is_file() and not (out / "is-kopyasi").exists()
    window, cli = (len(list((out / d).glob("*.pdf"))) for d in ("pencere-0", "komut-0"))
    assert window == cli and window > 0


@pytest.mark.skipif(shutil.which("tesseract") is None, reason="Tesseract not installed")
def test_ocr_on_and_off_both_compared(tmp_path, capsys):
    tool = load_tool()
    assert tool.main([str(scans(tmp_path)), "--cikti", str(tmp_path / "s")]) == 0
    text = capsys.readouterr().out
    assert "OCR on: page count per file" in text and "OCR off: page count per file" in text


def test_detects_a_difference(tmp_path):
    tool = load_tool()
    a, b = tmp_path / "a", tmp_path / "b"
    for folder, count in ((a, 2), (b, 3)):
        folder.mkdir()
        make_pdf(folder / "belge.pdf", [text_page()] * count)
    report = tool.Report()
    tool.compare_outputs("t", a, b, report)
    failed = {label for label, ok, _ in report.checks if not ok}
    assert "t: page count per file" in failed


def test_refuses_a_used_output_folder_and_empty_input(tmp_path, capsys):
    tool = load_tool()
    used = tmp_path / "dolu"
    used.mkdir()
    (used / "x").write_text("x")
    assert tool.main([str(scans(tmp_path)), "--cikti", str(used)]) == 2
    empty = tmp_path / "bos"
    empty.mkdir()
    assert tool.main([str(empty), "--cikti", str(tmp_path / "o")]) == 2
