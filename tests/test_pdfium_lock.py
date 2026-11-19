"""PDFium is not thread-safe; every Evrakçı call into it runs under one lock."""

from concurrent.futures import ThreadPoolExecutor

from fakes import make_pdf, qr_page, text_page

from evrakci.pipeline import analyze, render
from evrakci.pipeline.pdfium_lock import PDFIUM_LOCK


def test_render_page_holds_the_lock(tmp_path, monkeypatch):
    pdf = make_pdf(tmp_path / "a.pdf", [text_page("A")])
    seen = []
    real = render.pdfium.PdfDocument

    def opened(*args, **kwargs):
        seen.append(PDFIUM_LOCK._is_owned())
        return real(*args, **kwargs)

    monkeypatch.setattr(render.pdfium, "PdfDocument", opened)
    render.render_page(pdf, 0, dpi=40)
    with render.PageRenderer(pdf) as pages:
        pages.render(0, dpi=40)
    assert seen == [True, True]


def test_many_threads_render_and_analyse_at_once(tmp_path):
    pdfs = [make_pdf(tmp_path / f"{n}.pdf", [text_page("A"), qr_page(), text_page(), text_page()])
            for n in range(3)]

    def work(n):
        pdf = pdfs[n % len(pdfs)]
        if n % 4 == 0:
            return len(analyze.analyze_pdf(pdf))
        with render.PageRenderer(pdf) as pages:
            return sum(pages.render(i, dpi=30).size[0] > 0 for i in range(4)) + \
                render.render_page(pdf, n % 4, dpi=30).size[0] * 0

    with ThreadPoolExecutor(8) as pool:
        results = list(pool.map(work, range(48)))
    assert results == [4] * 48
