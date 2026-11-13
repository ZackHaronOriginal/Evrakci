from datetime import datetime

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton

from evrakci.ui import motion
from evrakci.ui.feedback import InfoBar, SaveState, Toaster


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _instant(app):
    motion.set_reduced_motion_override(True)
    yield
    motion.set_reduced_motion_override(None)


@pytest.fixture
def window(app):
    w = QMainWindow()
    w.resize(900, 600)
    w.show()
    yield w
    w.close()


def test_toast_shows_one_and_queues(window):
    t = Toaster(window)
    t.show("8 değer onaylandı", timeout_ms=0)
    t.show("İkinci", timeout_ms=0)
    assert t.current_text() == "8 değer onaylandı"
    assert t.pending() == 1
    t.dismiss()
    assert t.current_text() == "İkinci" and t.pending() == 0
    t.dismiss()
    assert t.current_text() == ""


def test_toast_placed_bottom_right_inside_window(window):
    t = Toaster(window)
    t.show("Merhaba", timeout_ms=0)
    box = t._current.frame.mapTo(window, t._current.frame.rect().bottomRight())
    assert box.x() <= window.width() - 12 + 1 and box.y() <= window.height() - 12 + 1
    assert box.x() > window.width() // 2


def test_toast_action_runs_and_closes(window):
    calls = []
    t = Toaster(window)
    t.show("Silindi", "Geri al", lambda: calls.append(1), timeout_ms=0)
    button = next(b for b in t._current.findChildren(QPushButton) if b.text() == "Geri al")
    button.click()
    assert calls == [1] and t.current_text() == ""


def test_toast_never_steals_focus(window):
    box = QPushButton("odak", window)
    box.show()
    box.setFocus()
    t = Toaster(window)
    t.show("Bilgi", "Geri al", timeout_ms=0)
    assert window.focusWidget() is box


def test_toast_escape_on_toast(window):
    t = Toaster(window)
    t.show("Bilgi", timeout_ms=0)
    QTest.keyClick(t._current, Qt.Key.Key_Escape)
    assert t.current_text() == ""


def test_toast_times_out(window):
    t = Toaster(window)
    t.show("Kısa", timeout_ms=20)
    QTest.qWait(80)
    assert t.current_text() == ""


def test_infobar_action_and_dismiss(app):
    seen = []
    bar = InfoBar("error", "Kaydedilemedi", "Disk dolu.", "Yeniden dene", lambda: seen.append(1))
    bar.show()
    assert bar.property("severity") == "error"
    bar.action_button.click()
    assert seen == [1]
    got = []
    bar.dismissed.connect(lambda: got.append(1))
    bar.close_button.click()
    assert got == [1] and not bar.isVisible()
    assert InfoBar("info", "t", "x", dismissible=False).close_button is None


def test_save_state_texts(app):
    s = SaveState()
    s.set_saving()
    assert s.text() == "Kaydediliyor…" and s.state() == "saving"
    today = datetime.now().replace(hour=14, minute=32)
    s.set_saved(today)
    assert s.text() == "Kaydedildi 14:32"
    calls = []
    s.set_failed("Disk dolu", lambda: calls.append(1))
    assert s.text() == "Kaydedilemedi" and s.state() == "failed"
    s._retry.click()
    assert calls == [1]
    s.set_saved(today.replace(hour=9, minute=5))
    assert not s._retry.isVisibleTo(s) and s.text() == "Kaydedildi 09:05"


def test_saved_text_shows_the_date_when_not_today():
    from evrakci.ui.feedback import saved_text

    now = datetime(2026, 11, 13, 16, 0)
    assert saved_text(datetime(2026, 11, 13, 14, 32), now) == "14:32"
    assert saved_text(datetime(2026, 11, 12, 14, 32), now) == "12 Kas 14:32"
    assert saved_text(datetime(2026, 2, 3, 8, 1), now) == "3 Şub 08:01"
    assert saved_text(datetime(2025, 11, 12, 14, 32), now) == "12 Kas 2025 14:32"
