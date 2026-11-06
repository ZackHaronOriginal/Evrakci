import pytest

from evrakci.pipeline.ocr.compare import compare_synthetic, render_report
from evrakci.pipeline.ocr.engine import Reading, Word
from evrakci.pipeline.ocr.synthetic import make_pages


@pytest.fixture(scope="module")
def fake_pages():
    return make_pages(1, seed=5, degrade=False)


class PerfectEngine:
    """Reads back the truth: looks up each crop by its size."""

    name = "mükemmel"

    def __init__(self, pages):
        self.page = pages[0]
        self.by_size = {
            (f.box[2] - f.box[0], f.box[3] - f.box[1]): f.text for f in self.page.fields
        }

    def available(self):
        return None

    def read_page(self, image):
        return [Word(w.text, w.box, 1.0) for w in self.page.words]

    def read_region(self, image):
        return Reading(self.by_size[image.size], 1.0)


class Unavailable:
    name = "bozuk"

    def available(self):
        return "yok"


def test_perfect_engine_scores_full(fake_pages):
    [r] = compare_synthetic([PerfectEngine(fake_pages)], fake_pages)
    assert r.exact == r.fields and r.cer == 0 and r.tr_wrong == 0
    assert r.aligned == r.words and r.tr_total > 0 and r.page_seconds >= 0


def test_unavailable_engine_listed(fake_pages):
    results = compare_synthetic([Unavailable()], fake_pages)
    assert results[0].unavailable == "yok"
    assert "kullanılamıyor: yok" in render_report(results, {}, "T", [])


def test_report_has_table(fake_pages):
    results = compare_synthetic([PerfectEngine(fake_pages)], fake_pages)
    text = render_report(results, {"mükemmel": 5 * 1024 * 1024}, "Başlık", ["not"])
    assert "| Motor |" in text and "100.0" in text and "not" in text and "5.0" in text


class Exploding:
    name = "patlayan"

    def available(self):
        return None

    def read_page(self, image):
        from evrakci.pipeline.ocr.engine import EngineUnavailable

        raise EngineUnavailable("çöktü")

    read_region = read_page


def test_other_engines_still_run(fake_pages):
    results = compare_synthetic([Unavailable(), Exploding(), PerfectEngine(fake_pages)], fake_pages)
    assert [r.unavailable for r in results] == ["yok", "çöktü", None]
    assert results[2].exact == results[2].fields > 0
    assert f"Alan sayısı: {results[2].fields}." in render_report(results, {}, "T", [])


def test_pipe_in_reading_escaped(fake_pages):
    from evrakci.pipeline.ocr.compare import EngineResult

    r = EngineResult("x", fields=1, samples=[("a|b", "c|d")])
    text = render_report([r], {}, "T", [])
    assert "a\\|b" in text and "c\\|d" in text


def test_preprocessing_applied_to_all_engines(fake_pages):
    seen = []

    class Spy(PerfectEngine):
        def read_region(self, image):
            seen.append(set(image.tobytes()) <= {0, 255})
            return super().read_region(image)

    compare_synthetic([Spy(fake_pages)], fake_pages, preprocess=True)
    assert seen and all(seen)
