"""Phase 4 Şablonlar fixes: F-sablonlar-01, 03, 07/08 (B-017), 10 (B-016), 11."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QScrollArea
from test_ledger_c import _sablon

from evrakci.ui.sablon_inspector import InspectorPanel, InspectorState
from evrakci.ui.sablon_read import Shown


def _panel(qtbot, state, width=380):
    panel = InspectorPanel()
    qtbot.addWidget(panel)
    panel.resize(width, 700)
    panel.show()
    panel.show_state(state)
    qtbot.wait(30)
    return panel


def _fits(panel):
    scroll = panel.findChild(QScrollArea)
    return scroll.widget().width() <= scroll.viewport().width()


@pytest.mark.parametrize("width", [320, 380])
def test_long_unbroken_read_value_stays_inside_the_inspector(qtbot, width):  # F-sablonlar-01
    text = "X" * 150
    state = InspectorState(mode="box", top="Kutu 1 / 1", title="Sicil_No", box=(10, 10, 60, 20),
                           shown=Shown(text, "emin", 90))
    panel = _panel(qtbot, state, width)
    assert _fits(panel)
    assert panel.read_value.toolTip() == text


@pytest.mark.parametrize("points", [16, 20])
@pytest.mark.parametrize("width", [320, 380])
def test_wide_glyphs_do_not_push_the_inspector_past_its_viewport(qtbot, width, points):
    """Windows fonts are wider than the Linux ones: the panel's minimum must follow the content
    (a break mark every 12 glyphs, an unwrapped caption, the row of the page field)."""
    app = QApplication.instance()
    old = app.font()
    wide = QFont(old)
    wide.setPointSize(points)
    app.setFont(wide)
    try:
        state = InspectorState(mode="box", top="Kutu 1 / 1", title="Sicil_No",
                               box=(10, 10, 60, 20), shown=Shown("X" * 150, "emin", 90))
        panel = _panel(qtbot, state, width)
        assert _fits(panel)
    finally:
        app.setFont(old)


def test_variable_less_template_inspector_fits(qtbot):  # F-sablonlar-03
    state = InspectorState(mode="none", title="Şablon",
                           sub="Eklemek için Ctrl+Shift+N tuşlarına basın.")
    panel = _panel(qtbot, state, 300)
    assert panel.sub.wordWrap()
    assert _fits(panel)


def test_b017_damaged_file_named_in_the_list(qtbot, tmp_path):
    screen, templates, _t = _sablon(qtbot, tmp_path)
    (templates.root / "abcdef1234.json").write_text("{ not json", encoding="utf-8")
    screen.refresh_templates()
    assert "abcdef1234" in screen.message.text()


def test_f08_opening_a_damaged_or_deleted_template_is_handled(qtbot, tmp_path):
    screen, templates, template = _sablon(qtbot, tmp_path)
    other = templates.create("Başka")
    templates.save(other)
    screen.refresh_templates()
    (templates.root / f"{other.id}.json").write_text("{ not json", encoding="utf-8")
    screen.open_template(other.id)  # must not raise
    assert screen.template.id == template.id
    assert "okunamadı" in screen.message.text()
    (templates.root / f"{other.id}.json").unlink()
    screen.message.setText("")
    screen.open_template(other.id)  # KeyError path
    assert screen.template.id == template.id and screen.message.text()
    current = screen.templates.currentItem()
    assert current is not None and current.data(Qt.ItemDataRole.UserRole + 0) is not None


def _screen_with_box(qtbot, tmp_path):
    screen, _templates, _template = _sablon(qtbot, tmp_path)
    screen.set_example(1)
    screen.add_box((10.0, 20.0, 60.0, 30.0))
    return screen


def _box(screen):
    return screen.template.variable("Sicil_No").sections[0].box_mm


def test_b016_inspector_fields_keep_the_box_on_the_sheet(qtbot, tmp_path):
    screen = _screen_with_box(qtbot, tmp_path)
    sheet_w, sheet_h = screen.canvas.page_mm()
    x, y, w, h = screen.side.spins
    w.setValue(sheet_w)
    x.setValue(sheet_w - 5.0)
    h.setValue(sheet_h)
    y.setValue(sheet_h - 5.0)
    x0, y0, x1, y1 = _box(screen)
    assert 0 <= x0 and x1 <= sheet_w + 0.01 and 0 <= y0 and y1 <= sheet_h + 0.01
    assert x.value() == pytest.approx(x0, abs=0.01)


def test_inspector_width_edit_is_cut_at_the_sheet_edge(qtbot, tmp_path):
    screen = _screen_with_box(qtbot, tmp_path)
    sheet_w, _ = screen.canvas.page_mm()
    screen.side.spins[2].setValue(sheet_w)  # x stays 10: the width is cut, x is not moved
    x0, _y0, x1, _y1 = _box(screen)
    assert x0 == pytest.approx(10.0) and x1 == pytest.approx(sheet_w, abs=0.01)


def test_drag_cannot_leave_the_sheet(qtbot, tmp_path):
    screen = _screen_with_box(qtbot, tmp_path)
    canvas = screen.canvas
    item = canvas.selected_item()
    box = _box(screen)
    canvas._drag = ("move", item, item.mapToScene(item.rect().center()), box, 0)
    far = item.mapToScene(item.rect().center())
    far.setX(far.x() + 100000)
    far.setY(far.y() + 100000)
    canvas._drag_to(far)
    sheet_w, sheet_h = canvas.page_mm()
    x0, y0, x1, y1 = item.spec.box
    assert x1 <= sheet_w + 0.01 and y1 <= sheet_h + 0.01 and x0 >= 0 and y0 >= 0
    canvas._drag = ("size", item, item.mapToScene(item.rect().center()), box, 3)
    canvas._drag_to(far)
    x0, y0, x1, y1 = item.spec.box
    assert x1 <= sheet_w + 0.01 and y1 <= sheet_h + 0.01


def _off_sheet(screen, box):
    canvas = screen.canvas
    screen._set_box("Sicil_No", 0, box)
    canvas.update_box("Sicil_No", 0, box)
    return canvas


@pytest.mark.parametrize("key,mods,axis", [
    (Qt.Key.Key_Up, Qt.KeyboardModifier.NoModifier, 1),
    (Qt.Key.Key_Left, Qt.KeyboardModifier.NoModifier, 0),
    (Qt.Key.Key_Right, Qt.KeyboardModifier.ControlModifier, 2),
    (Qt.Key.Key_Down, Qt.KeyboardModifier.ControlModifier, 3),
])
def test_f11_one_arrow_press_moves_an_off_sheet_box_a_quarter_millimetre(
        qtbot, tmp_path, key, mods, axis):
    screen = _screen_with_box(qtbot, tmp_path)
    canvas = _off_sheet(screen, (400.0, 500.0, 460.0, 520.0))
    canvas.setFocus()
    before = canvas.selected_item().spec.box
    QTest.keyClick(canvas, key, mods)
    after = canvas.selected_item().spec.box
    moved = [abs(a - b) for a, b in zip(after, before, strict=True)]
    assert max(moved) <= 0.26, (before, after)


def test_break_marks_are_display_only(qtbot):  # F-sablonlar-01 round 1
    from PySide6.QtWidgets import QApplication
    text = "AB12" * 30
    state = InspectorState(mode="box", top="Kutu 1 / 1", title="Sicil_No", box=(10, 10, 60, 20),
                           shown=Shown(text, "emin", 90))
    panel = _panel(qtbot, state, 320)
    label = panel.read_value
    assert "​" in label.text()  # it does break on screen
    assert label.accessibleName() == text and "​" not in label.accessibleName()
    label.setFocus()
    label.setSelection(0, len(label.text()))
    QApplication.clipboard().setText(label.selectedText())
    qtbot.wait(30)
    assert "​" not in QApplication.clipboard().text()
    assert QApplication.clipboard().text() == text
    label.setText("Okunuyor…")
    assert label.accessibleName() == "Okunuyor…"


def test_a_refresh_does_not_overwrite_the_name_being_typed(qtbot):
    """A read finishing or the busy timer re-shows the same variable while the user types."""
    state = InspectorState(mode="variable", top="Değişken 1 / 1", title="Sicil_No",
                           name="Sicil_No")
    panel = _panel(qtbot, state)
    panel.name.setFocus()
    qtbot.waitUntil(panel.name.hasFocus)
    panel.name.setText("abc")
    panel.name.setCursorPosition(1)
    panel.show_state(InspectorState(mode="variable", top="Değişken 1 / 1", title="Sicil_No",
                                    name="Sicil_No", busy=True))
    panel._fit()
    qtbot.wait(30)
    assert panel.name.text() == "abc"
    assert panel.name.cursorPosition() == 1
    # another variable shown is a real change and does replace the text
    panel.show_state(InspectorState(mode="variable", title="Firma", name="Firma"))
    assert panel.name.text() == "Firma"
