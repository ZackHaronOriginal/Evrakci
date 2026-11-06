import pikepdf
import pytest
from fakes import empty_page, make_pdf, qr_page, text_page

from evrakci.pipeline.analyze import BatchError, analyze_pdf


def test_kinds_detected(tmp_path):
    pdf = make_pdf(tmp_path / "b.pdf", [text_page(), empty_page(), qr_page(), text_page()])
    infos = analyze_pdf(pdf)
    assert [i.is_separator for i in infos] == [False, False, True, False]
    assert [i.is_empty for i in infos] == [False, True, False, False]


def test_small_skewed_qr_still_separator(tmp_path):
    pdf = make_pdf(tmp_path / "b.pdf", [qr_page(scale=0.35, angle=5)])
    assert analyze_pdf(pdf)[0].is_separator


def test_progress_reported(tmp_path):
    pdf = make_pdf(tmp_path / "b.pdf", [text_page(), text_page()])
    calls = []
    analyze_pdf(pdf, progress=lambda done, total: calls.append((done, total)))
    assert calls == [(1, 2), (2, 2)]


def test_not_a_pdf(tmp_path):
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"not a pdf")
    with pytest.raises(BatchError):
        analyze_pdf(bad)


def test_missing_file(tmp_path):
    with pytest.raises(BatchError, match="Dosya bulunamadı"):
        analyze_pdf(tmp_path / "yok.pdf")


def test_folder_instead_of_pdf(tmp_path):
    with pytest.raises(BatchError, match="Dosya bulunamadı"):
        analyze_pdf(tmp_path)


def test_encrypted_pdf(tmp_path):
    src = make_pdf(tmp_path / "a.pdf", [text_page()])
    locked = tmp_path / "kilitli.pdf"
    with pikepdf.open(src) as pdf:
        pdf.save(locked, encryption=pikepdf.Encryption(user="x", owner="y"))
    with pytest.raises(BatchError):
        analyze_pdf(locked)


def test_zero_page_pdf(tmp_path):
    empty = tmp_path / "bos.pdf"
    with pikepdf.new() as pdf:
        pdf.save(empty)
    with pytest.raises(BatchError):
        analyze_pdf(empty)
