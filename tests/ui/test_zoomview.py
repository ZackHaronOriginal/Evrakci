import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtGui import QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from evrakci.ui.prefs import Prefs
from evrakci.ui.zoomview import ZoomController, ZoomSlider


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def prefs(tmp_path, app):
    return Prefs(tmp_path / "u.ini")


@pytest.fixture
def view(app):
    v = QGraphicsView(QGraphicsScene())
    v.show()
    return v


def wheel(widget, delta, mods=Qt.KeyboardModifier.ControlModifier):
    pos = QPointF(10, 10)
    event = QWheelEvent(pos, widget.mapToGlobal(pos), QPoint(), QPoint(0, delta),
                        Qt.MouseButton.NoButton, mods, Qt.ScrollPhase.NoScrollPhase, False)
    QApplication.sendEvent(widget.viewport(), event)
    return event


def test_ctrl_wheel_zooms(view, prefs):
    z = ZoomController(view, prefs, "k")
    seen = []
    z.zoom_changed.connect(seen.append)
    assert wheel(view, 120).isAccepted()
    assert z.zoom() == 110 and seen == [110]
    wheel(view, -120)
    wheel(view, -120)
    assert z.zoom() == 90


def test_plain_wheel_ignored(view, prefs):
    z = ZoomController(view, prefs, "k")
    wheel(view, 120, Qt.KeyboardModifier.NoModifier)
    assert z.zoom() == 100


def test_keys(view, prefs):
    z = ZoomController(view, prefs, "k", fit_callback=lambda: 60)
    ctrl = Qt.KeyboardModifier.ControlModifier
    QTest.keyClick(view, Qt.Key.Key_Plus, ctrl)
    assert z.zoom() == 110
    QTest.keyClick(view, Qt.Key.Key_Minus, ctrl)
    QTest.keyClick(view, Qt.Key.Key_Minus, ctrl)
    assert z.zoom() == 90
    QTest.keyClick(view, Qt.Key.Key_0, ctrl)
    assert z.zoom() == 60


def test_clamp(view, prefs):
    z = ZoomController(view, prefs, "k", minimum=25, maximum=400)
    z.set_zoom(5000)
    assert z.zoom() == 400
    z.set_zoom(1)
    assert z.zoom() == 25
    z.zoom_out()
    assert z.zoom() == 25


def test_fit_defaults_to_100(view, prefs):
    z = ZoomController(view, prefs, "k")
    z.set_zoom(200)
    z.fit()
    assert z.zoom() == 100


def test_persistence_round_trip(view, prefs, tmp_path):
    ZoomController(view, prefs, "kontrol").set_zoom(150)
    again = ZoomController(view, Prefs(tmp_path / "u.ini"), "kontrol")
    assert again.zoom() == 150
    other = ZoomController(view, Prefs(tmp_path / "u.ini"), "degerler")
    assert other.zoom() == 100


def test_slider_binds_and_rebinds(view, prefs, app):
    a = ZoomController(view, prefs, "a")
    v2 = QGraphicsView(QGraphicsScene())
    b = ZoomController(v2, prefs, "b", maximum=200)
    s = ZoomSlider(a, "Küçük resimler")
    assert s.label.text() == "%100" and "Küçük resimler" in s.slider.toolTip()
    a.set_zoom(120)
    assert s.slider.value() == 120 and s.label.text() == "%120"
    s.slider.setValue(80)
    assert a.zoom() == 80
    s.bind(b, "Sayfa")
    assert s.slider.maximum() == 200 and "Sayfa" in s.slider.toolTip()
    a.set_zoom(50)
    assert s.label.text() == "%100"
    s._in.click()
    assert b.zoom() == 110
    s.bind(None)
    assert not s.isEnabled()
