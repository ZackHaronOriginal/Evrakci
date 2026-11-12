import pytest
from fakes import job_from_kinds, make_pdf, text_page
from PIL import Image
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from evrakci.pipeline.ocr.engine import Reading
from evrakci.pipeline.render import mm_box_to_pixels
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui.controller import JobController
from evrakci.ui.sablon import PageCanvas, SablonScreen


def _drag(canvas, start, end):
    viewport = canvas.viewport()
    a = canvas.mapFromScene(*start)
    b = canvas.mapFromScene(*end)
    QTest.mousePress(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, a)
    QTest.mouseMove(viewport, b)
    QTest.mouseRelease(viewport, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, b)


@pytest.mark.parametrize("size", [(827, 1169), (850, 1100), (1169, 827)])  # A4, Letter, A4 rotated
def test_drawing_a_box_gives_millimetres_matching_the_reader(qtbot, size):
    canvas = PageCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(900, 900)
    canvas.set_page(Image.new("L", size, 255), dpi=100)
    canvas.drawing = True
    got = []
    canvas.box_drawn.connect(got.append)
    _drag(canvas, (100, 200), (300, 260))
    assert len(got) == 1
    x0, y0, x1, y1 = got[0]
    assert (x0, y0) == pytest.approx((25.4, 50.8), abs=0.3)
    assert (x1, y1) == pytest.approx((76.2, 66.04), abs=0.3)
    assert mm_box_to_pixels(got[0], size, dpi=100) == pytest.approx((100, 200, 300, 260), abs=1)


class FakeEngine:
    name = "sahte"

    def available(self):
        return None

    def read_region(self, image):
        return Reading("48213", 0.95)


@pytest.fixture
def screen(qtbot, tmp_path):
    pdf = make_pdf(tmp_path / "b1.pdf", [text_page("A"), text_page("B"), text_page("C")])
    store = JobStore(tmp_path / "jobs")
    job = job_from_kinds({"b1": "ppp"})
    (store.batch_file(job, job.batches[0])).parent.mkdir(parents=True)
    (store.batch_file(job, job.batches[0])).write_bytes(pdf.read_bytes())
    store.save(job)
    ctl = JobController(store, job)
    ctl.add_cut("b1/1")
    ctl.add_cut("b1/2")
    templates = TemplateStore(tmp_path / "tpl")
    template = templates.create("Kapasite Raporu")
    template.add_variable("Sicil_No", required=True)
    templates.save(template)
    widget = SablonScreen(templates, lambda: ctl, engine=FakeEngine)
    qtbot.addWidget(widget)
    widget.resize(1366, 700)
    widget.open_template(template.id)
    widget.select_variable("Sicil_No")
    return widget


def test_boxes_from_two_examples_become_ordered_variants(screen):
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    screen.set_example(3)
    screen.add_box((150.0, 260.0, 185.0, 270.0))
    sections = screen.template.variable("Sicil_No").sections
    assert [s.box_mm for s in sections] == [(10.0, 20.0, 60.0, 30.0), (150.0, 260.0, 185.0, 270.0)]
    assert sections[0].example != sections[1].example
    assert "Belge 3" in sections[1].example
    assert screen.store.load(screen.template.id).variable("Sicil_No").sections == sections


def test_moving_a_variant_up_changes_the_try_order(screen):
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    screen.set_example(2)
    screen.add_box((15.0, 25.0, 65.0, 35.0))
    screen.select_section("Sicil_No", 1)
    screen.section_up_button.click()
    boxes = [s.box_mm for s in screen.template.variable("Sicil_No").sections]
    assert boxes == [(15.0, 25.0, 65.0, 35.0), (10.0, 20.0, 60.0, 30.0)]


def test_live_panel_shows_what_the_boxes_read(qtbot, screen):
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    qtbot.waitUntil(lambda: "48213" in screen.reads_text(), timeout=10000)


def test_pattern_uses_variable_names(screen):
    screen.pattern.setText("{Sicil_No}_belge")
    screen.pattern.editingFinished.emit()
    assert screen.template.filename_pattern == "{Sicil_No}_belge"
    screen.pattern.setText("{Yok}")
    screen.pattern.editingFinished.emit()
    assert screen.template.filename_pattern == "{Sicil_No}_belge"
    assert "Yok" in screen.message.text()
