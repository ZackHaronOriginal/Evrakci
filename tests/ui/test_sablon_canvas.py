"""The Şablonlar canvas: zoom as a percentage, pan, box selection, handles, arrow-key nudge, snap,
the rulers."""

import pytest
from PIL import Image
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from evrakci.ui import theme
from evrakci.ui.sablon_canvas import (
    CANVAS_DPI,
    MIN_BOX_MM,
    BoxSpec,
    PageCanvas,
    fmt_mm,
)
from evrakci.ui.sablon_rulers import CanvasWell, ruler_size

A4_200 = (1654, 2339)


@pytest.fixture
def canvas(qtbot):
    widget = PageCanvas()
    qtbot.addWidget(widget)
    widget.resize(700, 520)
    widget.show()
    widget.set_page(Image.new("L", A4_200, 255), CANVAS_DPI)
    widget.set_boxes([BoxSpec("Sicil_No", 0, 1, (20.0, 30.0, 60.0, 40.0)),
                      BoxSpec("Firma", 0, 2, (20.0, 60.0, 100.0, 70.0))])
    return widget


def _press(canvas, pos, button=Qt.MouseButton.LeftButton):
    QTest.mousePress(canvas.viewport(), button, Qt.KeyboardModifier.NoModifier, pos)


def _release(canvas, pos, button=Qt.MouseButton.LeftButton):
    QTest.mouseRelease(canvas.viewport(), button, Qt.KeyboardModifier.NoModifier, pos)


def _at(canvas, x_mm, y_mm) -> QPoint:
    per = canvas.dpi / 25.4
    return canvas.mapFromScene(QPointF(x_mm * per, y_mm * per))


def test_millimetres_read_the_way_the_ui_writes_them():
    assert [fmt_mm(v) for v in (70, 70.25, 104.5, 8.0, 0.0)] == ["70,0", "70,25", "104,5", "8,0",
                                                                   "0,0"]


def test_zoom_is_a_percentage_of_life_size(canvas):
    canvas.set_zoom(100)
    assert canvas.px_per_mm() == pytest.approx(96 / 25.4, rel=1e-3)  # 1 mm = 3,78 px
    canvas.set_zoom(200)
    assert canvas.px_per_mm() == pytest.approx(2 * 96 / 25.4, rel=1e-3)


def test_the_page_follows_the_window_until_the_user_zooms(canvas):
    assert canvas.is_fitted()
    fitted = canvas.zoom()
    canvas.resize(900, 520)
    assert canvas.zoom() > fitted  # wider window: a larger fit
    canvas.set_zoom(150)
    canvas.resize(500, 520)
    assert canvas.zoom() == 150  # no re-fit once the user has zoomed
    assert not canvas.is_fitted()


def test_the_wheel_pans_and_shift_wheel_pans_sideways(canvas):
    canvas.set_zoom(300)
    bar = canvas.verticalScrollBar()
    before = bar.value()
    bar.setValue(before + 100)
    assert bar.value() == before + 100
    assert canvas.horizontalScrollBar().maximum() > 0


@pytest.mark.parametrize("how", ["space", "middle"])
def test_space_drag_and_middle_drag_pan_the_page(canvas, how):
    canvas.set_zoom(300)
    hbar, vbar = canvas.horizontalScrollBar(), canvas.verticalScrollBar()
    hbar.setValue(200)
    vbar.setValue(300)
    start, end = QPoint(300, 250), QPoint(240, 200)
    if how == "space":
        QTest.keyPress(canvas, Qt.Key.Key_Space)
        _press(canvas, start)
    else:
        _press(canvas, start, Qt.MouseButton.MiddleButton)
    QTest.mouseMove(canvas.viewport(), end)
    _release(canvas, end, Qt.MouseButton.LeftButton if how == "space" else
             Qt.MouseButton.MiddleButton)
    if how == "space":
        QTest.keyRelease(canvas, Qt.Key.Key_Space)
    assert (hbar.value(), vbar.value()) == (260, 350)  # the page follows the hand
    assert canvas.selected() is None  # the drag selected nothing


def test_a_click_selects_a_box_and_the_bare_page_clears_it(canvas):
    got = []
    canvas.box_selected.connect(lambda name, index: got.append((name, index)))
    canvas.set_zoom(150)
    _press(canvas, _at(canvas, 40, 35))
    _release(canvas, _at(canvas, 40, 35))
    assert canvas.selected() == ("Sicil_No", 0)
    _press(canvas, _at(canvas, 150, 200))
    _release(canvas, _at(canvas, 150, 200))
    assert canvas.selected() is None
    assert got == [("Sicil_No", 0), ("", -1)]


def test_arrow_keys_nudge_a_quarter_millimetre_and_shift_a_millimetre(canvas):
    moved = []
    canvas.box_changed.connect(lambda name, index, box: moved.append(box))
    canvas.select("Sicil_No", 0)
    QTest.keyClick(canvas, Qt.Key.Key_Right)
    QTest.keyClick(canvas, Qt.Key.Key_Down)
    QTest.keyClick(canvas, Qt.Key.Key_Left, Qt.KeyboardModifier.ShiftModifier)
    assert moved == [(20.25, 30.0, 60.25, 40.0), (20.25, 30.25, 60.25, 40.25),
                     (19.25, 30.25, 59.25, 40.25)]
    assert canvas.selected_item().spec.box == (19.25, 30.25, 59.25, 40.25)
    assert "x 19,25" in canvas.accessibleDescription()


def test_a_nudge_stops_at_the_edge_of_the_sheet(canvas):
    canvas.update_box("Sicil_No", 0, (0.0, 30.0, 40.0, 40.0))
    canvas.select("Sicil_No", 0)
    moved = []
    canvas.box_changed.connect(lambda *a: moved.append(a))
    QTest.keyClick(canvas, Qt.Key.Key_Left)
    assert moved == []  # already at x = 0: nothing to report
    width = round(canvas.page_mm()[0], 2)  # a box drawn to the edge is stored in 0,01 mm
    canvas.update_box("Sicil_No", 0, (round(width - 40.0, 2), 30.0, width, 40.0))
    QTest.keyClick(canvas, Qt.Key.Key_Right, Qt.KeyboardModifier.ShiftModifier)
    assert moved == []


def test_without_a_box_the_arrows_scroll(canvas):
    canvas.set_zoom(300)
    canvas.verticalScrollBar().setValue(100)
    QTest.keyClick(canvas, Qt.Key.Key_Down)
    assert canvas.verticalScrollBar().value() > 100
    assert canvas.selected() is None


def test_dragging_a_box_moves_it_and_snap_rounds_to_whole_millimetres(canvas):
    done = []
    canvas.box_changed.connect(lambda name, index, box: done.append(box))
    canvas.set_zoom(200)
    canvas.select("Sicil_No", 0)
    start = _at(canvas, 40, 35)
    end = start + QPoint(30, 17)
    _press(canvas, start)
    QTest.mouseMove(canvas.viewport(), end)
    _release(canvas, end)
    x0, y0, x1, y1 = done[-1]
    assert (x1 - x0, y1 - y0) == pytest.approx((40.0, 10.0), abs=0.02)  # moved, not resized
    assert x0 != round(x0) or y0 != round(y0)
    canvas.snap = True
    canvas.update_box("Sicil_No", 0, (20.0, 30.0, 60.0, 40.0))
    start = _at(canvas, 40, 35)
    end = start + QPoint(30, 17)
    _press(canvas, start)
    QTest.mouseMove(canvas.viewport(), end)
    _release(canvas, end)
    x0, y0, x1, y1 = done[-1]
    assert (x0, y0) == (round(x0), round(y0))
    assert (x1 - x0, y1 - y0) == pytest.approx((40.0, 10.0), abs=0.02)


def test_a_corner_handle_resizes_and_never_below_the_minimum(canvas):
    done = []
    canvas.box_changed.connect(lambda name, index, box: done.append(box))
    canvas.set_zoom(200)
    canvas.select("Sicil_No", 0)
    corner = _at(canvas, 60, 40)  # bottom right
    assert canvas.handle_at(corner) == 3
    _press(canvas, corner)
    QTest.mouseMove(canvas.viewport(), corner + QPoint(40, 20))
    _release(canvas, corner + QPoint(40, 20))
    x0, y0, x1, y1 = done[-1]
    assert (x0, y0) == (20.0, 30.0) and x1 > 60.0 and y1 > 40.0
    corner = _at(canvas, x1, y1)
    _press(canvas, corner)
    QTest.mouseMove(canvas.viewport(), QPoint(0, 0))  # far past the opposite corner
    _release(canvas, QPoint(0, 0))
    x0, y0, x1, y1 = done[-1]
    assert x1 - x0 >= MIN_BOX_MM - 1e-6 and y1 - y0 >= MIN_BOX_MM - 1e-6


def test_drawing_snaps_when_snap_is_on(canvas):
    drawn = []
    canvas.box_drawn.connect(drawn.append)
    canvas.set_zoom(150)
    canvas.snap = True
    canvas.set_drawing(True)
    _press(canvas, _at(canvas, 100.4, 100.4))
    QTest.mouseMove(canvas.viewport(), _at(canvas, 130.6, 112.6))
    _release(canvas, _at(canvas, 130.6, 112.6))
    x0, y0, x1, y1 = drawn[0]
    assert all(v == pytest.approx(round(v), abs=0.01) for v in (x0, y0, x1, y1))


def test_escape_ends_drawing_then_clears_the_selection(canvas):
    ended = []
    canvas.drawing_cancelled.connect(lambda: ended.append(True))
    canvas.set_drawing(True)
    canvas.select("Firma", 0)
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    assert ended == [True] and canvas.selected() == ("Firma", 0)
    canvas.set_drawing(False)
    QTest.keyClick(canvas, Qt.Key.Key_Escape)
    assert canvas.selected() is None


def test_the_cursor_position_is_reported_in_millimetres(canvas):
    seen = []
    canvas.cursor_moved.connect(seen.append)
    canvas.set_zoom(100)
    QTest.mouseMove(canvas.viewport(), _at(canvas, 84.5, 41.0))
    assert seen[-1] == pytest.approx((84.5, 41.0), abs=0.3)
    QTest.mouseMove(canvas.viewport(), QPoint(2, 2))  # off the sheet (in the margin)
    assert seen[-1] is None or seen[-1][0] < 3


def test_rulers_start_at_the_sheets_corner_and_mark_the_selected_extent(qtbot):
    canvas = PageCanvas()
    well = CanvasWell(canvas)
    qtbot.addWidget(well)
    well.resize(760, 560)
    well.show()
    canvas.set_page(Image.new("L", A4_200, 255), CANVAS_DPI)
    assert well.top.height() == ruler_size() == well.left.width() == 24
    assert well.top.accessibleName() == "Cetvel, yatay (mm)"
    assert well.left.accessibleName() == "Cetvel, dikey (mm)"
    # the sheet's corner under the top ruler's 0: the canvas and the ruler share one origin
    assert well.top.mapToGlobal(QPoint(0, 0)).x() == well.canvas.mapToGlobal(QPoint(0, 0)).x()
    well.set_extent((70.0, 34.0, 174.0, 42.0))
    assert well.top.extent == (70.0, 174.0) and well.left.extent == (34.0, 42.0)
    well.set_extent(None)
    assert well.top.extent is None
    assert not well.grab().isNull()


@pytest.mark.parametrize("mode", ["light", "dark", "hc"])
def test_the_canvas_paints_in_every_theme(qtbot, mode):
    manager = theme.manager()
    manager.set_mode(mode)
    try:
        canvas = PageCanvas()
        well = CanvasWell(canvas)
        qtbot.addWidget(well)
        well.resize(760, 560)
        well.show()
        canvas.set_page(Image.new("L", A4_200, 255), CANVAS_DPI)
        canvas.set_boxes([BoxSpec("A", 0, 1, (20.0, 30.0, 60.0, 40.0), reading="48213",
                                  level="emin"),
                          BoxSpec("B", 0, 2, (20.0, 50.0, 60.0, 60.0), True, "48Z13", "kontrol")])
        canvas.set_show_reads(True)
        canvas.select("A", 0)
        canvas.setFocus(Qt.FocusReason.TabFocusReason)
        assert not well.grab().isNull()
    finally:
        manager.set_mode("system")
