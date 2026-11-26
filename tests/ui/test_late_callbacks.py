"""Work that was still pending when a window was deleted must end without a trace.

A worker result, a timer or a saver answer that arrives after the MainWindow's C++ object is gone
used to surface in a LATER test as "libshiboken: Internal C++ object (MainWindow) already
deleted" (CI, test_yukle_a). Every kind of deferred work is started here, the window is deleted
while it is still pending, and the event loop then runs for a second with Qt's message handler
and the exception hook watching."""
from __future__ import annotations

import threading
import time

import shiboken6
from fakes import make_pdf, text_page
from PySide6.QtCore import QCoreApplication, QEvent, QtMsgType, qInstallMessageHandler
from PySide6.QtWidgets import QApplication

from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore
from evrakci.ui import ocr_engine, workers
from evrakci.ui import saver as saver_module
from evrakci.ui.main_window import MainWindow
from evrakci.ui.prefs import Prefs
from evrakci.ui.workers import run_background


def _pump(seconds: float) -> None:
    app = QApplication.instance()
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        app.processEvents()
        time.sleep(0.005)


def _delete(window) -> None:
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QApplication.instance().processEvents()


def test_pending_work_of_a_deleted_window_ends_silently(qtbot, tmp_path, monkeypatch):
    store = JobStore(tmp_path / "jobs")
    pdf = make_pdf(tmp_path / "t.pdf", [text_page("A"), text_page("B")])
    job = store.create_job("Eski", [pdf])
    prefs = Prefs(tmp_path / "p.ini")
    prefs.add_recent_job(job.id)
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=prefs)
    window.show()
    qtbot.waitUntil(lambda: window.yukle.window_ is window, timeout=3000)
    with qtbot.waitSignal(window.yukle.job_opened, timeout=10000):
        window.yukle.open_job(store.load(job.id))
    qtbot.waitUntil(lambda: not window.loading(), timeout=10000)

    gate = threading.Event()  # the workers answer only after the window is gone
    real_list, real_load = JobStore.list_jobs, JobStore.load

    def slow_list(self):
        gate.wait(5)
        return real_list(self)

    def slow_load(self, job_id):
        gate.wait(5)
        return real_load(self, job_id)

    monkeypatch.setattr(JobStore, "list_jobs", slow_list)
    monkeypatch.setattr(JobStore, "load", slow_load)
    monkeypatch.setattr(ocr_engine, "shared_engine",
                        lambda: type("E", (), {"available": lambda s: gate.wait(5) or True})())

    monkeypatch.setattr(workers, "LOADING_MIN_MS", 600)
    monkeypatch.setattr(saver_module, "STALL_MS", 200)
    got: list = []
    # A loading card shown and then released: its minimum-time close is a timer that outlives
    # the work.
    quick = window.start_loading(lambda _p: time.sleep(0.05) or 1, title="Kart",
                                 on_done=got.append, show_after_ms=0)
    qtbot.waitUntil(lambda: quick.finished is not None and not quick.running, timeout=5000)
    assert quick._close_timer is not None and quick._close_timer.isActive()

    window.yukle.refresh_jobs()  # the job list
    window.refresh_recent_jobs()  # the recent jobs of the menu
    run_background(window.yukle, lambda _p: gate.wait(5) or "x", title="İş açılıyor",
                   on_done=got.append, on_failed=got.append, on_cancelled=lambda: got.append(0))
    ocr_engine.warm_up()  # the engine probe
    # A write the saver has not answered: a flush waiter and its stall timer.
    controller = window.controller()
    flushed: list = []
    controller.saver._submitted += 1  # a snapshot is "in flight" until the gate opens
    controller.saver.when_idle(lambda ok, error: flushed.append(ok))

    errors: list[str] = []

    def handler(kind, _context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            errors.append(message)

    previous = qInstallMessageHandler(handler)
    try:
        with qtbot.capture_exceptions() as caught:
            _delete(window)
            assert not shiboken6.isValid(window)
            gate.set()  # every worker answers now, into a window that is gone
            _pump(1.0)
    finally:
        qInstallMessageHandler(previous)
    assert caught == []
    assert [m for m in errors if "already deleted" in m or "Internal C++" in m] == []


class _Drop:
    """The part of a QDropEvent the Yükle screen reads."""

    def __init__(self, paths):
        from PySide6.QtCore import QMimeData, QUrl
        self.data = QMimeData()
        self.data.setUrls([QUrl.fromLocalFile(str(p)) for p in paths])

    def mimeData(self):  # noqa: N802
        return self.data

    def acceptProposedAction(self):  # noqa: N802
        pass


def test_a_drop_whose_window_is_deleted_before_it_is_handled_ends_silently(qtbot, tmp_path):
    """The drop hands its files on with a zero timer (after the drag has ended); a window
    deleted in between must take that timer with it (CI: "Internal C++ object already
    deleted" in a later test of test_yukle_a)."""
    store = JobStore(tmp_path / "jobs")
    pdf = make_pdf(tmp_path / "t.pdf", [text_page("A")])
    window = MainWindow(store, TemplateStore(tmp_path / "tpl"),
                        settings_path=tmp_path / "ayar.json", prefs=Prefs(tmp_path / "p.ini"))
    window.show()
    qtbot.waitUntil(lambda: window.yukle.window_ is window, timeout=3000)
    errors: list[str] = []

    def handler(kind, _context, message):
        if kind in (QtMsgType.QtWarningMsg, QtMsgType.QtCriticalMsg, QtMsgType.QtFatalMsg):
            errors.append(message)

    previous = qInstallMessageHandler(handler)
    try:
        with qtbot.capture_exceptions() as caught:
            assert window.yukle.dropped(_Drop([pdf]))
            _delete(window)
            _pump(0.3)
    finally:
        qInstallMessageHandler(previous)
    assert caught == []
    assert [m for m in errors if "already deleted" in m or "Internal C++" in m] == []
