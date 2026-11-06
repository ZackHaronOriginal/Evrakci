import pikepdf
from fakes import make_pdf, text_page

from evrakci.pipeline.render import mm_box_to_pixels, render_page


def test_rotation_applied(tmp_path):
    pdf = make_pdf(tmp_path / "a.pdf", [text_page()])
    upright = render_page(pdf, 0)
    turned = render_page(pdf, 0, rotation=90)
    assert upright.width < upright.height and turned.width > turned.height
    assert upright.mode == "L" and abs(upright.width - 2480) <= 2


def test_pdf_rotate_plus_user_rotation(tmp_path):
    pdf = make_pdf(tmp_path / "a.pdf", [text_page()])
    with pikepdf.open(pdf, allow_overwriting_input=True) as doc:
        doc.pages[0].rotate(90, relative=False)
        doc.save(pdf)
    assert render_page(pdf, 0).width > render_page(pdf, 0).height
    both = render_page(pdf, 0, rotation=90)  # 90 + 90 = upside down portrait
    assert both.width < both.height


def test_box_clipped():
    assert mm_box_to_pixels((200.0, 280.0, 250.0, 320.0), (2480, 3508)) == (2362, 3307, 2480, 3508)
    assert mm_box_to_pixels((10.0, 10.0, 20.0, 20.0), (2480, 3508)) == (118, 118, 236, 236)


def test_box_outside_is_none():
    assert mm_box_to_pixels((220.0, 10.0, 250.0, 20.0), (2480, 3508)) is None
