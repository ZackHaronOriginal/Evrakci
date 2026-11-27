import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from PIL import Image

from evrakci.ui.thumbnails import ThumbnailService


class CountingRenderer:
    def __init__(self):
        self.calls = []
        self.lock = threading.Lock()

    def __call__(self, pid, height):
        with self.lock:
            self.calls.append(pid)
        return Image.new("RGB", (int(height * 0.7), height), "white")


def test_only_requested_pages_are_rendered_in_a_1000_page_job(qtbot):
    renderer = CountingRenderer()
    service = ThumbnailService(renderer, height=100)
    visible = [f"b1/{i}" for i in range(200, 212)]
    got = []
    service.ready.connect(lambda pid, image: got.append((pid, image.height())))
    for pid in visible:
        service.request(pid)
    qtbot.waitUntil(lambda: len(got) == len(visible), timeout=5000)
    assert sorted(renderer.calls) == sorted(visible)
    assert all(height == 100 for _, height in got)


def test_cached_pages_are_not_rendered_twice(qtbot):
    renderer = CountingRenderer()
    service = ThumbnailService(renderer, height=100)
    got = []
    service.ready.connect(lambda pid, image: got.append(pid))
    service.request("b1/0")
    qtbot.waitUntil(lambda: len(got) == 1, timeout=5000)
    service.request("b1/0")
    assert got == ["b1/0", "b1/0"]
    assert renderer.calls == ["b1/0"]


def test_cache_is_bounded(qtbot):
    renderer = CountingRenderer()
    service = ThumbnailService(renderer, height=20, capacity=5, workers=1)  # fixed order
    got = []
    service.ready.connect(lambda pid, image: got.append(pid))
    for i in range(12):
        service.request(f"b1/{i}")
    qtbot.waitUntil(lambda: len(got) == 12, timeout=5000)
    assert len(service.cache) == 5
    assert "b1/11" in service.cache and "b1/0" not in service.cache


def test_requests_no_longer_visible_are_dropped(qtbot):
    gate = threading.Event()
    renderer = CountingRenderer()

    def slow(pid, height):
        gate.wait(2)
        return renderer(pid, height)

    service = ThumbnailService(slow, height=20, workers=1)
    for i in range(10):
        service.request(f"b1/{i}")
    service.keep_only({"b1/0", "b1/9"})
    gate.set()
    qtbot.waitUntil(lambda: service.idle(), timeout=5000)
    assert set(renderer.calls) <= {"b1/0", "b1/9"}


def test_job_renderer_draws_a_real_page_at_the_requested_height(tmp_path):
    from fakes import job_from_kinds, make_pdf, text_page

    from evrakci.ui.thumbnails import job_renderer

    pdf = make_pdf(tmp_path / "b1.pdf", [text_page("A"), text_page("B")])
    job = job_from_kinds({"b1": "pp"})
    job.rotate("b1/1", 90)
    render = job_renderer(job, lambda: {"b1": pdf})
    assert render("b1/0", 100).height == 100
    rotated = render("b1/1", 100)
    assert rotated.height == 100 and rotated.width > 100  # landscape after rotation


def test_zoomed_in_thumbnails_are_rendered_sharp_enough():
    from evrakci.ui.thumbnails import render_dpi

    assert render_dpi(100) == 30  # small thumbnails: the cheap minimum
    assert render_dpi(418) >= 418 / 11.7  # Kontrol at %200: no upscaled blur
    assert render_dpi(1754) >= 150  # the loupe's %100 (A4 at 150 dpi)


def test_a_render_for_the_old_height_is_not_current_after_set_height(qtbot):
    renderer = CountingRenderer()
    service = ThumbnailService(renderer, height=50)
    got = []
    service.ready.connect(lambda pid, image: got.append(image.height()))
    service.request("b1/0")
    qtbot.waitUntil(lambda: got == [50], timeout=5000)
    service.set_height(80)
    assert not service.is_current("b1/0") and "b1/0" in service.cache
    service.request("b1/0")
    qtbot.waitUntil(lambda: got == [50, 80], timeout=5000)
    assert service.is_current("b1/0")


def test_over_the_byte_ceiling_the_page_farthest_from_the_viewport_goes_first(qtbot):
    renderer = CountingRenderer()
    one = 212 * 100  # bytes of one 70 x 100 RGB888 thumbnail (lines are padded to 4 bytes)
    service = ThumbnailService(renderer, height=100, max_bytes=one * 3 + 10, workers=1)
    service.distance = lambda pid: abs(int(pid.split("/")[1]) - 2.2)  # the viewport is at page 2
    got = []
    service.ready.connect(lambda pid, image: got.append(pid))
    for i in (5, 4, 3, 0, 1, 2):  # one worker: they arrive in this order
        service.request(f"b1/{i}")
    qtbot.waitUntil(lambda: len(got) == 6, timeout=5000)
    assert service.cache_bytes <= one * 3 + 10
    # over the ceiling it drops to 90 % of it in one go, the farthest pages first
    assert set(service.cache) == {"b1/2", "b1/3"}
    service.invalidate("b1/2")
    assert service.cache_bytes == one


_TEARDOWN_SCRIPT = r"""
import pathlib, sys, tempfile, time
sys.path.insert(0, sys.argv[2])
from fakes import make_pdf, text_page
from PIL import Image
from PySide6.QtWidgets import QApplication
import evrakci.ui.main_window as mw
from evrakci.pipeline.store import JobStore
from evrakci.pipeline.templates.store import TemplateStore

app = QApplication([])

def slow(pid, height):  # Python work plus waits, like a real render in a worker thread
    start = time.time()
    while time.time() - start < 0.4:
        sum(range(1000))
        time.sleep(0.001)
    return Image.new("RGB", (70, height), "white")

mw.job_renderer = lambda job, files, dpi=30: slow
tmp = pathlib.Path(tempfile.mkdtemp())
window = mw.MainWindow(JobStore(tmp / "jobs"), TemplateStore(tmp / "tpl"),
                       settings_path=tmp / "ayar.json")
pdf = make_pdf(tmp / "t.pdf", [text_page() for _ in range(12)])
window.yukle.create_job([pdf], "x")
deadline = time.time() + 30
while window.kontrol is None or window.kontrol.model.rowCount() < 12:
    app.processEvents()
    time.sleep(0.01)
    assert time.time() < deadline
window.show()
service = window.thumbnails
for pid in window.yukle.controller.job.ordered_page_ids():
    service.request(pid)
time.sleep(0.1)
assert service._busy > 0  # renders are in flight
mode = sys.argv[1]
if mode == "switch":
    window.yukle.create_job([pdf], "y")
elif mode == "close_job":
    window.close_job()
else:  # "close" (the window) and "quit" (Ctrl+Q ends in the same close)
    window.close()
    window.deleteLater()
for _ in range(100):
    app.processEvents()
    time.sleep(0.01)
print("done")
"""


@pytest.mark.parametrize("mode", ["close", "switch", "close_job", "quit"])
def test_b044_teardown_with_renders_in_flight_does_not_hang(mode, tmp_path):
    """B-044: closing the window, switching or closing a job while worker threads render must
    end cleanly; a hang fails here (the subprocess is killed) instead of freezing the suite."""
    env = {**os.environ, "QT_QPA_PLATFORM": "offscreen"}
    result = subprocess.run(
        [sys.executable, "-c", _TEARDOWN_SCRIPT, mode, str(Path(__file__).parent.parent)],
        env=env, capture_output=True, text=True, timeout=90)
    assert result.returncode == 0, result.stderr
    assert "done" in result.stdout


def _wait(predicate, timeout=5.0):
    import time

    from PySide6.QtWidgets import QApplication

    end = time.monotonic() + timeout
    while time.monotonic() < end:
        QApplication.processEvents()
        if predicate():
            return True
        time.sleep(0.005)
    return predicate()


def test_retired_service_is_not_deleted_while_a_render_runs(qtbot):
    """A worker inside the renderer must never see its service (pool, relay) destroyed: the
    native crash seen on Windows CI. Deletion waits until the pool is idle."""
    import shiboken6
    from PySide6.QtCore import QEvent, QObject
    from PySide6.QtWidgets import QApplication

    from evrakci.ui import thumbnails

    parent = QObject()
    inside, gate = threading.Event(), threading.Event()

    def renderer(pid, height):
        inside.set()
        gate.wait(10)
        return Image.new("RGB", (70, height), "white")

    service = ThumbnailService(renderer, height=100, parent=parent)
    destroyed = []
    service.destroyed.connect(lambda *_: destroyed.append(True))
    service.request("b1/0")
    assert inside.wait(5)
    service.retire()
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    QApplication.processEvents()
    del parent  # the old parent going away must not take the service with it
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert not service.idle()
    assert shiboken6.isValid(service) and not destroyed
    gate.set()
    assert _wait(lambda: service not in thumbnails._RETIRING)
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert _wait(lambda: not shiboken6.isValid(service))


def test_retiring_services_with_many_slow_renders_stress(qtbot):
    import time

    import shiboken6
    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QApplication

    from evrakci.ui import thumbnails

    def slow(pid, height):
        time.sleep(0.01)  # releases the GIL, like pdfium
        return Image.new("RGB", (70, height), "white")

    services = []
    for _ in range(30):
        service = ThumbnailService(slow, height=100, workers=2)
        services.append(service)
        for i in range(20):
            service.request(f"b1/{i}")
        service.retire()
        QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        QApplication.processEvents()
    assert _wait(lambda: not thumbnails._RETIRING, timeout=20)
    QApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    assert _wait(lambda: not any(shiboken6.isValid(s) for s in services))
