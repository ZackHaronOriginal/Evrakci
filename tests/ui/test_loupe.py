import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QLineEdit, QWidget

from evrakci.ui import motion
from evrakci.ui.loupe import PAGE_100, Loupe


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _instant(app):
    motion.set_reduced_motion_override(True)
    yield
    motion.set_reduced_motion_override(None)


class Renderer:
    def __init__(self):
        self.calls: list[tuple[int, int]] = []

    def __call__(self, index, size):
        self.calls.append((index, size.width()))
        pix = QPixmap(size.width(), round(size.width() * 1.4))
        pix.fill(QColor(200, 200, 200))
        return pix


@pytest.fixture
def setup(app):
    host = QWidget()
    host.resize(1000, 700)
    opener = QLineEdit(host)
    host.show()
    opener.setFocus()
    QApplication.processEvents()
    loupe = Loupe(host)
    return host, opener, loupe, Renderer()


def test_arrows_page_through(setup):
    _, _, loupe, render = setup
    seen = []
    loupe.index_changed.connect(seen.append)
    loupe.open(10, render, 2, lambda i: f"Belge {i}")
    assert loupe.is_open() and loupe.index() == 2
    QTest.keyClick(loupe, Qt.Key.Key_Right)
    QTest.keyClick(loupe, Qt.Key.Key_PageDown)
    assert loupe.index() == 4
    QTest.keyClick(loupe, Qt.Key.Key_Left)
    QTest.keyClick(loupe, Qt.Key.Key_PageUp)
    assert loupe.index() == 2
    QTest.keyClick(loupe, Qt.Key.Key_End)
    assert loupe.index() == 9
    QTest.keyClick(loupe, Qt.Key.Key_Right)
    assert loupe.index() == 9
    QTest.keyClick(loupe, Qt.Key.Key_Home)
    assert loupe.index() == 0 and seen[-1] == 0
    assert loupe._title_label.text() == "Belge 0"


@pytest.mark.parametrize("key", [Qt.Key.Key_Escape, Qt.Key.Key_Space])
def test_close_restores_focus(setup, key):
    host, opener, loupe, render = setup
    closed = []
    loupe.closed.connect(closed.append)
    loupe.open(5, render, 3)
    assert QApplication.focusWidget() is not opener
    QTest.keyClick(loupe, key)
    assert not loupe.isVisible() and closed == [3]
    assert QApplication.focusWidget() is opener


def test_thumbs_render_only_visible(setup):
    host, _, loupe, render = setup
    loupe.open(1000, render, 0)
    loupe.show()
    loupe.grab()  # paint
    thumb_calls = {i for i, w in render.calls if w != PAGE_100.width() and w < 400}
    visible = set(loupe.strip.visible_range())
    assert thumb_calls and thumb_calls <= visible
    assert len(thumb_calls) < 40
    page_calls = {i for i, w in render.calls if w == PAGE_100.width()}
    assert page_calls == {0}


def test_modes_and_zoom_key(setup):
    _, _, loupe, render = setup
    loupe.open(3, render, 0)
    fit = loupe.zoom.zoom()
    assert fit < 100
    loupe.set_mode("actual")
    assert loupe.zoom.zoom() == 100 and loupe._mode_buttons["actual"].isChecked()
    loupe.set_mode("width")
    assert loupe._mode == "width"
    loupe.set_mode("fit")
    assert loupe.zoom.zoom() == fit
    QTest.keyClick(loupe, Qt.Key.Key_Plus, Qt.KeyboardModifier.ControlModifier)
    assert loupe.zoom.zoom() == fit + 25 and loupe._mode == "custom"
    QTest.keyClick(loupe, Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier)
    assert loupe.zoom.zoom() == fit and loupe._mode == "fit"
    assert loupe.zoom.key() == "loupe"


def test_thumb_click_selects(setup):
    _, _, loupe, render = setup
    loupe.open(20, render, 0)
    pitch = loupe.strip._pitch()
    QTest.mouseClick(loupe.strip.viewport(), Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier,
                     loupe.strip._rect(3).center())
    assert loupe.index() == 3 and pitch > 0


def test_empty_open_is_ignored(setup):
    _, _, loupe, render = setup
    loupe.open(0, render, 0)
    assert not loupe.isVisible()
    assert QSize(1, 1).isValid()
