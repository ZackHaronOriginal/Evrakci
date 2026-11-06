import pikepdf
import zxingcpp

from evrakci.pipeline.separator import (
    SEPARATOR_PAYLOAD,
    is_separator_payload,
    make_separator_pdf,
    render_separator_image,
)


def test_payload_recognised():
    assert is_separator_payload(SEPARATOR_PAYLOAD)
    assert is_separator_payload("EVRAKCI-AYIRAC-2")
    assert not is_separator_payload("https://example.com")


def test_separator_pdf_has_front_and_back(tmp_path):
    path = make_separator_pdf(tmp_path / "ayirac.pdf", sheets=3)
    with pikepdf.open(path) as pdf:
        assert len(pdf.pages) == 6


def test_separator_image_qr_decodes():
    texts = [b.text for b in zxingcpp.read_barcodes(render_separator_image(dpi=100))]
    assert texts == [SEPARATOR_PAYLOAD]
