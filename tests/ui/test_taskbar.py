import pytest
from PySide6.QtWidgets import QApplication, QWidget

from evrakci.ui import taskbar
from evrakci.ui.taskbar import TaskbarProgress


@pytest.fixture(scope="module")
def app():
    return QApplication.instance() or QApplication([])


class Fake:
    def __init__(self):
        self.calls = []

    def set_state(self, flag):
        self.calls.append(("state", flag))

    def set_value(self, value, maximum):
        self.calls.append(("value", value, maximum))


def test_noop_without_backend_never_raises(app, monkeypatch):
    monkeypatch.setattr(taskbar.os, "name", "posix")
    t = TaskbarProgress(QWidget())
    t.set(3, 10)
    t.indeterminate()
    t.error()
    t.clear()
    assert t.state == "none"


def test_state_machine(app):
    fake = Fake()
    t = TaskbarProgress(QWidget(), backend=fake)
    t.set(5, 10)
    assert (t.state, t.value, t.maximum) == ("normal", 5, 10)
    assert fake.calls == [("state", taskbar.NORMAL), ("value", 5, 10)]
    t.set(99, 10)
    assert t.value == 10
    t.indeterminate()
    assert t.state == "indeterminate" and fake.calls[-1] == ("state", taskbar.INDETERMINATE)
    t.set(1, 0)
    assert t.state == "indeterminate"
    t.error()
    assert t.state == "error" and fake.calls[-1] == ("state", taskbar.ERROR)
    t.clear()
    assert t.state == "none" and fake.calls[-1] == ("state", taskbar.NOPROGRESS)


def test_backend_errors_are_swallowed(app):
    class Boom(Fake):
        def set_state(self, flag):
            raise OSError("x")

    t = TaskbarProgress(QWidget(), backend=Boom())
    t.set(1, 2)
    assert t.state == "normal"


def test_title_prefix(app):
    w = QWidget()
    w.setWindowTitle("Evrakçı")
    t = TaskbarProgress(w, backend=Fake(), title_prefix=True)
    t.set(62, 100)
    assert w.windowTitle() == "%62 – Evrakçı"
    t.set(70, 100)
    assert w.windowTitle() == "%70 – Evrakçı"
    t.clear()
    assert w.windowTitle() == "Evrakçı"
    w.setWindowTitle("Başka")
    t.set(1, 4)
    assert w.windowTitle() == "%25 – Başka"
