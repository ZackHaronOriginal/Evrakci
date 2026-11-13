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
    screen.move_selected_section(-1)
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
    # the pattern field moved into the inspector (A has no place for it in the left column), and
    # its message is at the field: what was typed stays, the words say what to mend
    assert "Yok" in screen.pattern_error.text() and screen.pattern.text() == "{Yok}"
    QTest.keyClicks(screen.pattern, "x")
    assert screen.pattern_error.isHidden()  # gone at the next key


# -- Phase 3: the A screen ------------------------------------------------------------------------
def _wait_read(qtbot, screen):
    qtbot.waitUntil(lambda: screen._read_task is None, timeout=15000)


def test_a_new_box_is_selected_and_nudged_with_the_arrow_keys_as_one_undo_step(qtbot, screen):
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    assert (screen.variable_name, screen.section_index) == ("Sicil_No", 0)
    assert screen.canvas.selected() == ("Sicil_No", 0)
    steps = screen.undo_stack.count()
    screen.canvas.setFocus()
    for _ in range(3):
        QTest.keyClick(screen.canvas, Qt.Key.Key_Right)
    QTest.keyClick(screen.canvas, Qt.Key.Key_Down, Qt.KeyboardModifier.ShiftModifier)
    box = screen.template.variable("Sicil_No").sections[0].box_mm
    assert box == pytest.approx((10.75, 21.0, 60.75, 31.0))
    assert screen.undo_stack.count() == steps + 1  # four nudges, one step
    assert screen.undo_stack.undoText() == "Kutuyu taşı"
    screen.flush_save()
    assert screen.store.load(screen.template.id).variable("Sicil_No").sections[0].box_mm == box
    screen.undo_stack.undo()
    assert screen.template.variable("Sicil_No").sections[0].box_mm == (10.0, 20.0, 60.0, 30.0)
    screen.undo_stack.redo()
    assert screen.template.variable("Sicil_No").sections[0].box_mm == pytest.approx(box)
    _wait_read(qtbot, screen)


def test_resizing_is_its_own_undo_step_with_its_own_name(qtbot, screen):
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    screen.canvas.box_changed.emit("Sicil_No", 0, (10.0, 20.0, 70.0, 30.0))
    assert screen.undo_stack.undoText() == "Kutuyu yeniden boyutlandır"
    screen.canvas.box_changed.emit("Sicil_No", 0, (11.0, 20.0, 71.0, 30.0))
    assert screen.undo_stack.undoText() == "Kutuyu taşı"
    _wait_read(qtbot, screen)


def test_the_inspector_fields_edit_the_selected_box(qtbot, screen):
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    x, y, w, h = screen.side.spins
    assert (x.value(), y.value(), w.value(), h.value()) == (10.0, 20.0, 50.0, 10.0)
    assert screen.side.top.text() == "Kutu 1 / 1" and screen.side.title.full_text() == "Sicil_No"
    w.setValue(55.5)
    assert screen.template.variable("Sicil_No").sections[0].box_mm == (10.0, 20.0, 65.5, 30.0)
    assert screen.canvas.selected_item().spec.box == (10.0, 20.0, 65.5, 30.0)
    assert screen.side.spins[2].text() == "55,5"  # the Turkish decimal comma
    screen.side.page.setValue(-1)  # "son": the last page
    assert screen.template.variable("Sicil_No").sections[0].page == -1
    assert screen.side.page.text() == "son"
    screen.side.name.setText("Sicil_Numarasi")
    screen.side.name.editingFinished.emit()
    assert screen.template.variable("Sicil_Numarasi")
    assert screen.variable_name == "Sicil_Numarasi"
    screen.side.name.setText("")
    screen.side.name.editingFinished.emit()
    assert "boş" in screen.message.text()
    assert screen.side.name.text() == "Sicil_Numarasi"  # the old name stays
    _wait_read(qtbot, screen)


def test_the_inspector_shows_what_the_box_reads_and_how_sure_it_is(qtbot, screen):
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    qtbot.waitUntil(lambda: screen.side.read_value.text() == "48213", timeout=15000)
    assert screen.side.level.word.text() == "Emin"
    assert screen.side.level.percent.text() == "%95"
    assert screen.side.read_label.text() == "Okunan, örnek 1"
    assert screen.canvas.boxes()[0].reading == "48213"  # for "Okumaları sayfada göster"


def test_confidence_levels_use_the_apps_one_vocabulary():
    from evrakci.pipeline.templates.values import SectionReading, VariableValue
    from evrakci.ui.sablon_read import level_of, shown_for

    assert level_of("", 0.9, 0.7) == "okunamadi"
    assert level_of("x", 0.5, 0.7) == "kontrol"
    assert level_of("x", 0.8, 0.7) == "orta"
    assert level_of("x", 0.95, 0.7) == "emin"
    assert level_of("x", 0.95, 0.99) == "kontrol"
    flagged = VariableValue("", 0.0, None, True, "48213", (SectionReading(0, "48Z13", 0.4),))
    assert shown_for(flagged, None, 0.7).level == "kontrol"
    assert shown_for(flagged, None, 0.7).text == "48213"  # the suggestion
    assert shown_for(flagged, 0, 0.7).text == "48Z13"
    unread = shown_for(flagged, 1, 0.7)  # a later section is not tried after an earlier one wins
    assert unread.level == "okunmadi" and "denenmedi" in unread.note
    assert shown_for(None, None, 0.7).level == "okunmadi"


def test_duplicating_and_deleting_a_box_are_undoable(qtbot, screen):
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    screen.duplicate_box()
    sections = screen.template.variable("Sicil_No").sections
    assert [s.box_mm for s in sections] == [(10.0, 20.0, 60.0, 30.0), (15.0, 25.0, 65.0, 35.0)]
    assert screen.section_index == 1
    screen.delete_selected()
    assert len(screen.template.variable("Sicil_No").sections) == 1
    assert screen.undo_stack.undoText() == "Kutuyu sil"
    screen.undo_stack.undo()
    assert len(screen.template.variable("Sicil_No").sections) == 2
    _wait_read(qtbot, screen)


def test_delete_on_a_variable_removes_it_and_undo_brings_it_back(qtbot, screen):
    screen.select_variable("Sicil_No")
    screen.delete_selected()
    assert screen.template.variables == []
    assert "Değişken yok" in screen.side.title.full_text()
    screen.undo_stack.undo()
    assert [v.name for v in screen.template.variables] == ["Sicil_No"]
    _wait_read(qtbot, screen)


def test_alt_arrows_move_the_chosen_variable_or_section(qtbot, screen):
    screen.ask_variable = lambda: None
    screen._edit("Değişken ekle", lambda t: t.add_variable("Firma"))
    screen.select_variable("Firma")
    screen.move_selected(-1)
    assert [v.name for v in screen.template.variables] == ["Firma", "Sicil_No"]
    assert screen.variable_name == "Firma"
    screen.move_variable_to(0, 1)  # what a drag in the list asks for
    assert [v.name for v in screen.template.variables] == ["Sicil_No", "Firma"]
    screen.set_example(1)
    screen.select_variable("Sicil_No")
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    screen.set_example(2)
    screen.add_box((15.0, 25.0, 65.0, 35.0))
    screen.variables.section_moved.emit("Sicil_No", 1, 0)
    assert [s.box_mm for s in screen.template.variable("Sicil_No").sections] == [
        (15.0, 25.0, 65.0, 35.0), (10.0, 20.0, 60.0, 30.0)]
    assert screen.section_index == 0
    _wait_read(qtbot, screen)


def test_the_list_marks_required_variables_and_numbers_them(screen):
    item = screen.variables.item_for("Sicil_No")
    assert item.data(0, Qt.ItemDataRole.AccessibleTextRole) == (
        "Değişken 1: Sicil_No, zorunlu kutu yok")
    from evrakci.ui.sablon_nav import ROLE_NUMBER, ROLE_REQUIRED

    assert item.data(0, ROLE_NUMBER) == 1 and item.data(0, ROLE_REQUIRED) is True


def test_a_failed_save_is_said_in_words_and_can_be_retried(qtbot, screen, monkeypatch):
    def broken(_template):
        raise OSError("disk dolu")

    monkeypatch.setattr(screen.store, "save", broken)
    screen.save()
    assert "kaydedilemedi" in screen.message.text() and screen._save_error
    monkeypatch.undo()
    screen.save()
    assert screen.message.text() == "" and not screen._save_error


def test_a_page_of_a_long_document_can_be_chosen_and_boxes_follow_their_page(qtbot, tmp_path):
    pdf = make_pdf(tmp_path / "b.pdf", [text_page("A"), text_page("B"), text_page("C")])
    store = JobStore(tmp_path / "jobs")
    job = job_from_kinds({"b1": "ppp"})
    store.batch_file(job, job.batches[0]).parent.mkdir(parents=True)
    store.batch_file(job, job.batches[0]).write_bytes(pdf.read_bytes())
    store.save(job)
    controller = JobController(store, job)
    templates = TemplateStore(tmp_path / "tpl")
    template = templates.create("Uzun belge")
    template.add_variable("Tarih")
    templates.save(template)
    widget = SablonScreen(templates, lambda: controller, engine=FakeEngine)
    qtbot.addWidget(widget)
    widget.resize(1366, 700)
    widget.open_template(template.id)
    widget.select_variable("Tarih")
    assert [widget.pages.itemText(i) for i in range(widget.pages.count())] == [
        "1 / 3", "2 / 3", "3 / 3"]
    widget.set_page_number(2)
    widget.add_box((10.0, 20.0, 60.0, 30.0))
    assert widget.template.variable("Tarih").sections[0].page == 2
    assert [b.name for b in widget.canvas.boxes()] == ["Tarih"]
    widget.set_page_number(1)
    assert widget.canvas.boxes() == []  # the box belongs to page 2
    widget.select_section("Tarih", 0)  # choosing it in the list shows its page
    assert widget.page_number == 2 and widget.canvas.selected() == ("Tarih", 0)
    widget.side.page.setValue(3)
    assert widget.page_number == 3
    qtbot.waitUntil(lambda: widget._read_task is None, timeout=15000)


def test_trying_every_example_marks_the_ones_that_need_a_check(qtbot, screen):
    from evrakci.pipeline.ocr.engine import Reading

    class Uncertain:
        name = "kararsiz"
        calls = 0

        def available(self):
            return None

        def read_region(self, image):
            Uncertain.calls += 1
            return Reading("48Z13", 0.4)

    screen.engine = Uncertain
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    _wait_read(qtbot, screen)
    screen.read_all_examples()
    qtbot.waitUntil(lambda: screen._all_task is None and screen._read_task is None, timeout=20000)
    assert sorted(screen.example_values) == [1, 2, 3]
    assert [screen.examples.itemText(i) for i in range(3)] == [
        "Örnek 1, sayfa 1 · 1 kontrol", "Örnek 2, sayfa 2 · 1 kontrol",
        "Örnek 3, sayfa 3 · 1 kontrol"]
    assert not screen.examples.itemIcon(0).isNull()  # the triangle, not colour alone


def test_every_control_has_an_accessible_name(screen):
    from PySide6.QtWidgets import QAbstractButton, QComboBox, QLineEdit, QSpinBox

    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    named = [screen.nav.add_template_button, screen.nav.add_variable_button, screen.templates,
             screen.variables, screen.pattern, screen.examples, screen.pages, screen.canvas,
             screen.well.top, screen.well.left, screen.side.more, screen.side.save,
             screen.side.name, screen.side.required, screen.side.page, *screen.side.spins]
    for widget in named:
        assert widget.accessibleName().strip(), type(widget).__name__
    for kind in (QAbstractButton, QComboBox, QLineEdit, QSpinBox):
        for widget in screen.findChildren(kind):
            if widget.isHidden() or widget.parent() is screen.splitter.parent():
                continue
            if isinstance(widget, QLineEdit) and widget.parent() is not None and isinstance(
                    widget.parent(), QSpinBox):
                continue  # a spin box's inner edit
            assert widget.accessibleName().strip() or widget.text().strip(), (
                type(widget).__name__, widget.objectName())


def test_no_old_per_screen_shortcuts_are_left(screen):
    from PySide6.QtGui import QShortcut

    assert screen.findChildren(QShortcut) == []  # B, G, Ctrl+S/Z/Y/T are registry actions


@pytest.mark.parametrize("mode", ["light", "dark", "hc"])
def test_the_screen_paints_in_every_theme(qtbot, screen, mode):
    from evrakci.ui import theme

    manager = theme.manager()
    manager.set_mode(mode)
    try:
        screen.show()
        screen.set_example(1)
        screen.add_box((10.0, 20.0, 60.0, 30.0))
        assert not screen.grab().isNull()
    finally:
        manager.set_mode("system")
    qtbot.waitUntil(lambda: screen._read_task is None, timeout=15000)


def test_esc_stops_trying_every_example(qtbot, screen):
    import time

    from evrakci.pipeline.ocr.engine import Reading

    class Slow:
        name = "yavas"

        def available(self):
            return None

        def read_region(self, image):
            time.sleep(0.15)
            return Reading("48213", 0.95)

    screen.engine = Slow
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    qtbot.waitUntil(lambda: screen._read_task is None, timeout=15000)
    screen.read_all_examples()
    assert screen._all_task is not None and not screen.window_
    assert screen._escape() is True  # Esc is taken by the long read first
    qtbot.waitUntil(lambda: screen._all_task is None, timeout=15000)
    assert screen.example_values.get(3) is None  # it stopped before the last example
    assert screen._escape() is False  # nothing running: Esc is left to the canvas
