"""Cyclic garbage that holds Qt objects is collected on the window thread only (ui/gc_guard.py).

CPython collects on whichever thread crosses the allocation threshold. A worker that allocates
(the saver writing JSON, a render job) used to destroy a dropped widget's cycle off the window
thread, and Qt crashed (Linux CI: segfault in the saver's mkdir after a test left an orphan
ReadingRow behind)."""

from __future__ import annotations

import gc
import threading
import time
import weakref

import pytest
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

from evrakci.ui import gc_guard
from evrakci.ui.workers import run_background


@pytest.fixture
def owner(qtbot):
    widget = QWidget()
    qtbot.addWidget(widget)
    return widget


class _Cyclic(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.me = self  # a cycle: only the cycle collector frees it
        self.follow = lambda: self.objectName()


def _cyclic_garbage(freed_on: list[int]) -> None:
    obj = _Cyclic()
    weakref.finalize(obj, lambda: freed_on.append(threading.get_ident()))


def test_cyclic_qt_garbage_is_never_freed_by_a_worker(qtbot, owner):
    gc.collect()
    freed_on: list[int] = []
    _cyclic_garbage(freed_on)
    kept: list = []
    threshold = gc.get_threshold()[0] or 700

    def allocate(_progress):  # far over every threshold: without the guard a collection runs
        kept.extend([] for _ in range(threshold * 200))
        return threading.get_ident()

    worker: list[int] = []
    run_background(owner, allocate, title="Ayırıyor", on_done=worker.append)
    qtbot.waitUntil(lambda: bool(worker), timeout=10_000)
    assert worker[0] != threading.get_ident()
    assert worker[0] not in freed_on  # the worker freed nothing of the window's
    assert gc_guard.installed() and not gc.isenabled()
    qtbot.waitUntil(lambda: bool(freed_on), timeout=5000)  # the window thread's timer did
    assert freed_on == [threading.get_ident()]
    del kept[:]


def test_the_collector_keeps_up_with_cyclic_garbage(qtbot):
    """The bound on growth: garbage made on the window thread is freed by the timer alone,
    without a full collection, while workers are busy."""
    assert gc_guard.install()
    freed: list[int] = []
    gate = threading.Event()
    hold = threading.Thread(target=lambda: _hold(gate), daemon=True)
    hold.start()
    try:
        qtbot.waitUntil(gc_guard.busy, timeout=2000)
        full_before = gc_guard.stats["full"]
        for _ in range(50):
            _cyclic_garbage(freed)
            junk = [[] for _ in range(gc.get_threshold()[0] or 700)]  # crosses the threshold
            for item in junk:
                item.append(item)  # cyclic garbage too
            del junk
            qtbot.wait(gc_guard.TICK_MS + 20)
            if len(freed) == 50:
                break
        qtbot.waitUntil(lambda: len(freed) >= 45, timeout=5000)
        assert gc_guard.stats["full"] == full_before  # no full pass while a worker runs
    finally:
        gate.set()
        hold.join(5)


def _hold(gate: threading.Event) -> None:
    with gc_guard.working():
        gate.wait(30)


def test_turning_the_collector_back_on_is_undone(qtbot):
    assert gc_guard.install()
    gc.enable()
    try:
        qtbot.wait(gc_guard.TICK_MS * 3)
        assert not gc.isenabled()
    finally:
        gc.disable()


def test_a_young_collection_on_a_big_heap_stays_short(qtbot):
    """Many live widgets do not make a tick slow: only young objects are scanned."""
    from PySide6.QtWidgets import QLabel

    assert gc_guard.install()
    host = QWidget()
    qtbot.addWidget(host)
    labels = [QLabel(str(n), host) for n in range(3000)]
    gc.collect()
    junk = [[] for _ in range((gc.get_threshold()[0] or 700) * 2)]
    started = time.perf_counter()
    gc_guard.tick()
    assert time.perf_counter() - started < 0.1
    del junk, labels
