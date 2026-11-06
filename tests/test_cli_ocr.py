import json

from conftest import needs_tesseract
from fakes import a4_with, make_pdf, render_line, text_page

from evrakci.cli import main


@needs_tesseract
def test_synthetic_report(tmp_path, capsys):
    out = tmp_path / "r.md"
    assert main(["ocr-karsilastir", "--sentetik", "1", "--cikti", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "tesseract-tur" in text and "| Motor |" in text
    assert str(out) in capsys.readouterr().out


@needs_tesseract
def test_real_mode_with_boxes_in_mm(tmp_path):
    pdf = make_pdf(tmp_path / "a.pdf", [a4_with(render_line("Örnek Kayıt 2026", 30), (20, 30))])
    boxes = tmp_path / "k.json"
    boxes.write_text(
        json.dumps(
            [
                {
                    "pdf": "a.pdf",
                    "sayfa": 1,
                    "kutu_mm": [15, 25, 150, 45],
                    "beklenen": "Örnek Kayıt 2026",
                }
            ]
        ),
        encoding="utf-8",
    )
    out = tmp_path / "r.md"
    assert main(["ocr-karsilastir", str(pdf), "--kutular", str(boxes), "--cikti", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "Örnek Kayıt 2026" in text and "Saniye/sayfa" in text


def test_bad_boxes_file(tmp_path, capsys):
    pdf = make_pdf(tmp_path / "a.pdf", [text_page()])
    bad = tmp_path / "k.json"
    bad.write_text("{", encoding="utf-8")
    code = main(
        ["ocr-karsilastir", str(pdf), "--kutular", str(bad), "--cikti", str(tmp_path / "r.md")]
    )
    assert code == 2
    assert "Kutu dosyası okunamadı" in capsys.readouterr().err


def test_box_outside_page(tmp_path, capsys):
    pdf = make_pdf(tmp_path / "a.pdf", [text_page()])
    boxes = tmp_path / "k.json"
    boxes.write_text(
        json.dumps([{"pdf": "a.pdf", "sayfa": 1, "kutu_mm": [10, 10, 400, 20]}]), encoding="utf-8"
    )
    code = main(
        ["ocr-karsilastir", str(pdf), "--kutular", str(boxes), "--cikti", str(tmp_path / "r.md")]
    )
    assert code == 2
    assert "Kutu sayfanın dışında" in capsys.readouterr().err
