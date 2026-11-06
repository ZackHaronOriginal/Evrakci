from evrakci.pipeline.ocr.metrics import TURKISH_CHARS
from evrakci.pipeline.ocr.synthetic import make_pages


def test_pages_deterministic_and_rich_in_turkish():
    a, b = make_pages(2, seed=7), make_pages(2, seed=7)
    assert [f.text for f in a[0].fields] == [f.text for f in b[0].fields]
    fields = [f for p in a for f in p.fields]
    assert 8 <= len(a[0].fields) <= 12
    assert sum(any(c in TURKISH_CHARS for c in f.text) for f in fields) * 2 >= len(fields)
    assert a[0].image.size == (2480, 3508) and a[0].image.mode == "L"


def test_boxes_inside_page_and_contain_ink():
    page = make_pages(1, seed=3, degrade=False)[0]
    for field in page.fields:
        x0, y0, x1, y1 = field.box
        assert 0 <= x0 < x1 <= page.image.width and 0 <= y0 < y1 <= page.image.height
        crop = page.image.crop(field.box)
        assert crop.getextrema()[0] < 100  # some dark text inside
    assert len(page.words) >= len(page.fields)


def test_degrade_does_not_change_page_content():
    clean = make_pages(6, seed=4, degrade=False)
    scanned = make_pages(6, seed=4, degrade=True)
    texts = [[f.text for f in p.fields] for p in clean]
    assert texts == [[f.text for f in p.fields] for p in scanned]


def test_skew_option():
    from evrakci.pipeline.ocr.preprocess import estimate_skew

    page = make_pages(1, seed=4, degrade=True, max_skew=3.0, skew=2.5)[0]
    assert abs(estimate_skew(page.image) - 2.5) < 0.4
