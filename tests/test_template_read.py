from conftest import needs_tesseract
from fakes import render_line
from PIL import Image

from evrakci.pipeline.ocr.engine import Reading
from evrakci.pipeline.templates.model import Section, Template
from evrakci.pipeline.templates.read import read_document

A4 = (2480, 3508)  # 300 dpi


def read_by_name(template, *args):
    """read_document keys values by variable key; tests look them up by name."""
    names = template.names_by_key()
    return {names[key]: value for key, value in read_document(template, *args).items()}


class SizeEngine:
    """Answers by crop size: lets tests decide what each section 'reads'."""

    name = "fake"

    def __init__(self, answers):
        self.answers = answers
        self.calls = 0

    def available(self):
        return None

    def read_region(self, image):
        self.calls += 1
        return Reading(*self.answers.get(image.size, ("", 0.0)))


def px(mm):
    return round(mm / 25.4 * 300)


def blank(_index):
    return Image.new("L", A4, 255)


def template(*sections, required=False):
    t = Template(id="t", name="T")
    t.add_variable("Ünvan", required=required)
    for s in sections:
        t.add_section("Ünvan", s)
    return t


def test_first_confident_variant_wins():
    small = Section(1, (10.0, 10.0, 50.0, 20.0))
    wide = Section(1, (10.0, 10.0, 110.0, 20.0))
    engine = SizeEngine(
        {
            (px(50) - px(10), px(20) - px(10)): ("ÖRNEK", 0.40),
            (px(110) - px(10), px(20) - px(10)): ("Örnek Ltd.", 0.93),
        }
    )
    value = read_by_name(template(small, wide), 1, blank, engine)["Ünvan"]
    assert value.value == "Örnek Ltd." and value.section == 1 and not value.flagged
    assert [r.text for r in value.readings] == ["ÖRNEK", "Örnek Ltd."]


def test_stops_at_first_confident():
    first = Section(1, (10.0, 10.0, 50.0, 20.0))
    second = Section(1, (10.0, 10.0, 110.0, 20.0))
    engine = SizeEngine({(px(50) - px(10), px(20) - px(10)): ("Örnek", 0.95)})
    value = read_by_name(template(first, second), 1, blank, engine)["Ünvan"]
    assert value.section == 0 and engine.calls == 1 and len(value.readings) == 1


def test_none_confident_flagged_with_suggestion():
    a = Section(1, (10.0, 10.0, 50.0, 20.0))
    b = Section(1, (10.0, 10.0, 110.0, 20.0))
    engine = SizeEngine(
        {
            (px(50) - px(10), px(20) - px(10)): ("Ornek", 0.30),
            (px(110) - px(10), px(20) - px(10)): ("Örnek", 0.55),
        }
    )
    value = read_by_name(template(a, b), 1, blank, engine)["Ünvan"]
    assert value.flagged and value.value == "" and value.suggestion == "Örnek"
    assert value.section is None and len(value.readings) == 2


def test_last_page_and_missing_page():
    last = Section(-1, (10.0, 10.0, 50.0, 20.0))
    third = Section(3, (10.0, 10.0, 50.0, 20.0))
    seen = []

    def page(index):
        seen.append(index)
        return blank(index)

    engine = SizeEngine({(px(50) - px(10), px(20) - px(10)): ("X", 0.9)})
    assert read_by_name(template(last), 2, page, engine)["Ünvan"].value == "X"
    assert seen == [1]
    value = read_by_name(template(third), 2, page, engine)["Ünvan"]
    assert value.flagged and value.readings[0].problem == "sayfa yok"


def test_box_outside_page():
    outside = Section(1, (230.0, 10.0, 260.0, 20.0))
    value = read_by_name(template(outside), 1, blank, SizeEngine({}))["Ünvan"]
    assert value.flagged and value.readings[0].problem == "kutu sayfa dışında"


def test_variable_without_sections():
    value = read_by_name(template(), 1, blank, SizeEngine({}))["Ünvan"]
    assert value.flagged and value.readings == ()


@needs_tesseract
def test_real_tesseract_reads_box():
    from evrakci.pipeline.ocr.tesseract import default_engine

    page = Image.new("L", A4, 255)
    page.paste(render_line("Örnek Kayıt 2026", 60), (px(20), px(30)))
    t = template(Section(1, (15.0, 25.0, 150.0, 45.0)))
    value = read_by_name(t, 1, lambda i: page, default_engine())["Ünvan"]
    assert value.value == "Örnek Kayıt 2026" and value.confidence > 0.7


# -- weakest examples first (I-28) --------------------------------------------------------------
def _weak_value(*confidences, flagged=True):
    from evrakci.pipeline.templates.values import SectionReading, VariableValue

    readings = tuple(SectionReading(i, "x", c) for i, c in enumerate(confidences))
    return VariableValue("" if flagged else "x", 0.0 if flagged else 0.95, None, flagged,
                         "x" if flagged else "", readings)


def test_weakest_examples_are_ordered_by_flagged_count_then_lowest_confidence():
    from evrakci.pipeline.templates.read import ExampleWeakness, weakest_examples

    results = {
        1: {"a": _weak_value(0.6)},
        2: {"a": _weak_value(0.5), "b": _weak_value(0.3)},
        3: {"a": _weak_value(0.2)},
        4: {"a": _weak_value(0.9, flagged=False)},
    }
    got = weakest_examples(results)
    assert got == [ExampleWeakness(2, 2, 0.3), ExampleWeakness(3, 1, 0.2),
                   ExampleWeakness(1, 1, 0.6)]  # example 4 has nothing to check: left out
    assert [w.number for w in weakest_examples(results, limit=2)] == [2, 3]


def test_weakest_examples_break_a_full_tie_by_example_number():
    from evrakci.pipeline.templates.read import weakest_examples

    results = {5: {"a": _weak_value(0.4)}, 2: {"a": _weak_value(0.4)}, 9: {"a": _weak_value(0.4)}}
    assert [w.number for w in weakest_examples(results)] == [2, 5, 9]


def test_weakest_examples_use_the_best_reading_of_a_flagged_variable():
    from evrakci.pipeline.templates.read import weakest_examples

    got = weakest_examples({1: {"a": _weak_value(0.2, 0.55)}})
    assert got[0].lowest_confidence == 0.55  # the reading it would suggest, not the worst box


def test_a_variable_with_no_box_is_not_counted_as_weak():
    from evrakci.pipeline.templates.read import flagged_count, weakest_examples
    from evrakci.pipeline.templates.values import VariableValue

    nothing = VariableValue("", 0.0, None, True)  # no box: nothing was tried
    assert flagged_count({"k": nothing}) == 0
    assert weakest_examples({1: {"k": nothing}, 2: {}}) == []
