import ocrmypdf
import pikepdf
import pytest
from conftest import needs_tesseract
from fakes import a4_with, make_pdf, page_text, render_line, text_page

from evrakci.pipeline.ocr.engine import EngineUnavailable
from evrakci.pipeline.ocr.textlayer import add_text_layer


def scan(folder):
    folder.mkdir(parents=True, exist_ok=True)
    line = a4_with(render_line("Örnek Kayıt Şişli 2026", 30), (20, 30))
    return make_pdf(folder / "giriş.pdf", [line, text_page()])


@needs_tesseract
def test_pdfa_with_turkish_text(tmp_path):
    folder = tmp_path / "Şükrü"
    out = folder / "çıktı.pdf"
    result = add_text_layer(scan(folder), out)
    assert result.pdfa and result.note is None and result.path == out
    with pikepdf.open(out) as pdf:
        assert pdf.open_metadata().pdfa_status == "2B"
    assert "Örnek Kayıt Şişli 2026" in page_text(out, 0)


@needs_tesseract
def test_falls_back_to_plain_pdf(tmp_path, monkeypatch):
    real = ocrmypdf.ocr
    calls = []

    def flaky(*args, **kwargs):
        calls.append(kwargs["output_type"])
        if kwargs["output_type"].startswith("pdfa"):
            return ocrmypdf.ExitCode.pdfa_conversion_failed
        return real(*args, **kwargs)

    monkeypatch.setattr(ocrmypdf, "ocr", flaky)
    out = tmp_path / "o.pdf"
    result = add_text_layer(scan(tmp_path), out)
    assert calls == ["pdfa-2", "pdf"]
    assert not result.pdfa and "PDF/A" in result.note and out.is_file()
    assert "Örnek" in page_text(out, 0)


@needs_tesseract
def test_page_with_existing_text_kept(tmp_path):
    src = scan(tmp_path)
    with pikepdf.open(src, allow_overwriting_input=True) as pdf:
        page = pikepdf.Page(pdf.pages[1])
        font = pdf.make_indirect(
            pikepdf.Dictionary(
                Type=pikepdf.Name.Font, Subtype=pikepdf.Name.Type1, BaseFont=pikepdf.Name.Helvetica
            )
        )
        name = page.add_resource(font, pikepdf.Name.Font, prefix="F")
        text = f"BT {name} 12 Tf 50 50 Td (Dijital metin) Tj ET".encode()
        page.contents_add(pdf.make_stream(text))
        pdf.save(src)
    out = tmp_path / "o.pdf"
    result = add_text_layer(src, out)
    assert out.is_file() and result.path == out
    assert "Dijital metin" in page_text(out, 1)


@needs_tesseract
def test_real_pdfa_failure_falls_back(tmp_path):
    src = scan(tmp_path)
    with pikepdf.open(src, allow_overwriting_input=True) as pdf:  # text with a missing font
        pikepdf.Page(pdf.pages[1]).contents_add(pdf.make_stream(b"BT /Yok 12 Tf (x) Tj ET"))
        pdf.save(src)
    result = add_text_layer(src, tmp_path / "o.pdf")
    assert not result.pdfa and result.note == "PDF/A doğrulanamadı; normal PDF yazıldı"
    assert "Örnek" in page_text(tmp_path / "o.pdf", 0)


@needs_tesseract
def test_encrypted_input(tmp_path):
    src = scan(tmp_path)
    locked = tmp_path / "kilitli.pdf"
    with pikepdf.open(src) as pdf:
        pdf.save(locked, encryption=pikepdf.Encryption(user="x", owner="y"))
    with pytest.raises(EngineUnavailable, match="şifreli"):
        add_text_layer(locked, tmp_path / "o.pdf")


@needs_tesseract
def test_plain_pdf_option(tmp_path):
    out = tmp_path / "o.pdf"
    result = add_text_layer(scan(tmp_path), out, pdfa=False)
    assert not result.pdfa and result.note is None
    with pikepdf.open(out) as pdf:
        assert pdf.open_metadata().pdfa_status == ""
    assert "Örnek" in page_text(out, 0)


@needs_tesseract
def test_broken_input_turkish_message(tmp_path):
    bad = tmp_path / "bozuk.pdf"
    bad.write_bytes(scan(tmp_path).read_bytes()[:400])
    with pytest.raises(EngineUnavailable) as caught:
        add_text_layer(bad, tmp_path / "o.pdf")
    assert "PDF okunamadı veya bozuk: bozuk.pdf" in str(caught.value)
    assert "()" not in str(caught.value)


def test_ocrmypdf_logging_quiet():
    import logging

    import evrakci.pipeline.ocr.textlayer  # noqa: F401

    assert logging.getLogger("ocrmypdf").getEffectiveLevel() >= logging.ERROR


@needs_tesseract
def test_fresh_data_folder_end_to_end(tmp_path):
    import shutil

    from evrakci.pipeline.ocr.tesseract import TessData, system_tessdata

    folder = tmp_path / "Şükrü" / "veri"
    folder.mkdir(parents=True)
    shutil.copy(system_tessdata() / "tur.traineddata", folder)
    out = tmp_path / "o.pdf"
    result = add_text_layer(scan(tmp_path), out, tessdata=TessData("tur", folder))
    assert result.pdfa and "Örnek" in page_text(out, 0)


def test_prefix_restored(monkeypatch, tmp_path):
    import os

    from evrakci.pipeline.ocr.textlayer import _tessdata_prefix

    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)
    with _tessdata_prefix(tmp_path):
        assert os.environ["TESSDATA_PREFIX"] == str(tmp_path)
    assert "TESSDATA_PREFIX" not in os.environ
