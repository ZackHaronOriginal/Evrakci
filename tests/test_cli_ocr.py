import json

from conftest import needs_tesseract
from fakes import a4_with, make_pdf, render_line, text_page
from PIL import Image

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


def _boxes(tmp_path, entries):
    path = tmp_path / "k.json"
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def _run(tmp_path, pdfs, boxes):
    args = ["ocr-karsilastir", *map(str, pdfs), "--kutular", str(boxes)]
    return main([*args, "--cikti", str(tmp_path / "r.md")])


def test_unquoted_number_and_bad_coordinate(tmp_path, capsys):
    pdf = make_pdf(tmp_path / "a.pdf", [text_page()])
    entry = {"pdf": "a.pdf", "sayfa": 1, "kutu_mm": [10, 10, 50, 20], "beklenen": 123456}
    number = _boxes(tmp_path, [entry])
    assert _run(tmp_path, [pdf], number) == 0  # numbers are accepted as text
    bad = _boxes(tmp_path, [{"pdf": "a.pdf", "sayfa": 1, "kutu_mm": [10, 10, 50, "x"]}])
    assert _run(tmp_path, [pdf], bad) == 2
    assert "Kutu dosyası okunamadı" in capsys.readouterr().err


def test_same_name_pdfs_refused(tmp_path, capsys):
    (tmp_path / "x").mkdir()
    one = make_pdf(tmp_path / "a.pdf", [text_page()])
    two = make_pdf(tmp_path / "x" / "a.pdf", [text_page()])
    assert main(["ocr-karsilastir", str(one), str(two), "--cikti", str(tmp_path / "r.md")]) == 2
    assert "Aynı adlı" in capsys.readouterr().err


@needs_tesseract
def test_rotated_letter_page_box(tmp_path):
    import pikepdf

    letter = Image.new("L", (850, 1100), 255)  # US Letter at 100 dpi
    at = (round(20 / 25.4 * 100), round(30 / 25.4 * 100))
    letter.paste(render_line("Örnek Kayıt 2026", 30), at)
    # Stored turned a quarter anticlockwise; /Rotate 90 turns it back clockwise when shown.
    pdf = make_pdf(tmp_path / "l.pdf", [letter.rotate(90, expand=True)])
    with pikepdf.open(pdf, allow_overwriting_input=True) as doc:
        doc.pages[0].rotate(90, relative=False)  # displayed upright again
        doc.save(pdf)
    entry = {"pdf": "l.pdf", "sayfa": 1, "kutu_mm": [15, 25, 150, 45]}
    entry["beklenen"] = "Örnek Kayıt 2026"
    boxes = _boxes(tmp_path, [entry])
    assert _run(tmp_path, [pdf], boxes) == 0
    assert "| tesseract-tur (sistem) | " in (tmp_path / "r.md").read_text(encoding="utf-8")
    assert "1/1" in (tmp_path / "r.md").read_text(encoding="utf-8")


def test_engine_failing_mid_run_is_reported(tmp_path, monkeypatch):
    from evrakci.cli import ocr
    from evrakci.pipeline.ocr.engine import EngineUnavailable, Reading

    class Breaks:
        name = "bozulan"

        def available(self):
            return None

        def read_page(self, image):
            raise EngineUnavailable("Tesseract hata verdi")

        read_region = read_page

    class Works:
        name = "calisan"

        def available(self):
            return None

        def read_page(self, image):
            return []

        def read_region(self, image):
            return Reading("x", 1.0)

    monkeypatch.setattr(ocr, "all_engines", lambda: [Breaks(), Works()])
    pdf = make_pdf(tmp_path / "a.pdf", [text_page()])
    assert main(["ocr-karsilastir", str(pdf), "--cikti", str(tmp_path / "r.md")]) == 0
    text = (tmp_path / "r.md").read_text(encoding="utf-8")
    assert "bozulan | kullanılamıyor: Tesseract hata verdi" in text and "| calisan |" in text


def test_download_exit_code_on_errors(monkeypatch, tmp_path, capsys):
    from evrakci.cli import ocr

    monkeypatch.setenv("EVRAKCI_MODEL_DIR", str(tmp_path / "m"))
    monkeypatch.setattr(ocr, "_TUR_BEST_URL", "https://invalid.invalid/tur")
    monkeypatch.setenv("EVRAKCI_TESSDATA_BEST", str(tmp_path / "d"))
    assert main(["ocr-modelleri-indir"]) == 1
    assert "hata" in capsys.readouterr().out


@needs_tesseract
def test_ocr_command(tmp_path, capsys):
    import pikepdf

    src = make_pdf(tmp_path / "g.pdf", [a4_with(render_line("Örnek Kayıt 2026", 30), (20, 30))])
    out = tmp_path / "c.pdf"
    assert main(["ocr", str(src), str(out)]) == 0
    assert "Metin katmanı eklendi: c.pdf (PDF/A-2b)" in capsys.readouterr().out
    with pikepdf.open(out) as pdf:
        assert pdf.open_metadata().pdfa_status == "2B"


def test_ocr_command_missing_input(tmp_path, capsys):
    assert main(["ocr", str(tmp_path / "yok.pdf"), str(tmp_path / "c.pdf")]) == 2
    err = capsys.readouterr().err
    assert "Dosya bulunamadı:" in err and "yok.pdf" in err


def test_ocr_refuses_overwrite_and_same_file(tmp_path, capsys):
    src = make_pdf(tmp_path / "g.pdf", [text_page()])
    existing = make_pdf(tmp_path / "c.pdf", [text_page()])
    assert main(["ocr", str(src), str(existing)]) == 2
    assert "zaten var" in capsys.readouterr().err
    assert main(["ocr", str(src), str(src)]) == 2
    assert "aynı dosya" in capsys.readouterr().err


def test_ocr_missing_input_shows_folder(tmp_path, capsys):
    assert main(["ocr", str(tmp_path / "yok.pdf"), str(tmp_path / "c.pdf")]) == 2
    assert str(tmp_path / "yok.pdf") in capsys.readouterr().err
