"""Python's cycle collector runs on the window thread only.

CPython runs a cyclic collection on whichever thread crosses the allocation threshold. When
that is a worker (the saver's writer thread, a QThreadPool job), cyclic garbage that holds Qt
objects (a dropped widget with a lambda that names itself, a theme follower) is destroyed off
the window thread, and Qt crashes there (seen on Linux CI: a segfault inside the saver's
`mkdir`). Breaking each cycle by hand cannot be complete, so the automatic collector is turned
off (`gc.disable()` is process-wide) and this module collects from a window-thread timer:

* Every TICK_MS: when the young generation is over CPython's own threshold, collect it
  (generation 1 every GEN1_EVERY-th time). That is cheap: it only looks at recent objects.
* A full collection only after FULL_AFTER young ones, and only while no worker is running
  (`working()` marks worker code): a full pass over a big heap can take long, and the window
  must not stall while a job loads or the disk is slow. When workers never stop, the full
  collection still runs after FORCE_FULL_AFTER young ones (the bound on growth).
* At install the heap is collected once and frozen (`gc.freeze`): the start-up objects
  (modules, classes, fonts) are never scanned again, which keeps a full collection short.

Explicit `gc.collect()` on the window thread stays allowed. A long piece of window-thread work
that never returns to the event loop collects nothing until it does (refcounting still frees
everything that is not in a cycle).
"""

from __future__ import annotations

import gc
import threading
from collections.abc import Iterator
from contextlib import contextmanager

import shiboken6
from PySide6.QtCore import QCoreApplication, QThread, QTimer

TICK_MS = 100
GEN1_EVERY = 10  # as CPython's default threshold1
FULL_AFTER = 100  # young collections between full ones (threshold1 * threshold2)
FORCE_FULL_AFTER = 1000  # a full collection runs even while workers are busy

_lock = threading.Lock()
_working = 0  # worker threads inside `working()`
_timer: QTimer | None = None
_frozen = False
_young = 0  # young collections since the last full one
_threshold = 700
stats = {"young": 0, "gen1": 0, "full": 0, "forced": 0}  # read by the tests


@contextmanager
def working() -> Iterator[None]:
    """Wrap a worker thread's run: a full collection waits until no worker is running."""
    global _working
    with _lock:
        _working += 1
    try:
        yield
    finally:
        with _lock:
            _working -= 1


def busy() -> bool:
    return _working > 0


def installed() -> bool:
    return _timer is not None and shiboken6.isValid(_timer) and _timer.isActive()


def install() -> bool:
    """Turn the automatic collector off and collect from the window thread instead. Call it on
    the window thread before a worker thread starts; it is cheap when already installed.
    Without a QCoreApplication (nothing can schedule the collection) it does nothing."""
    global _timer, _frozen, _threshold
    if installed():
        if gc.isenabled():
            gc.disable()
        return True
    app = QCoreApplication.instance()
    if app is None or QThread.currentThread() is not app.thread():
        return False
    _threshold = max(1, gc.get_threshold()[0] or 700)
    gc.disable()
    if not _frozen:
        _frozen = True
        gc.collect()
        gc.freeze()
    timer = QTimer(app)
    timer.setInterval(TICK_MS)
    timer.timeout.connect(tick)
    timer.start()
    _timer = timer
    return True


def tick() -> None:
    """One step of the window-thread collector (the timer calls it)."""
    global _young
    if gc.isenabled():  # someone turned it back on: workers could collect again
        gc.disable()
    if gc.get_count()[0] < _threshold:
        return
    if _young >= FORCE_FULL_AFTER or (_young >= FULL_AFTER and not busy()):
        stats["forced" if busy() else "full"] += 1
        _young = 0
        gc.collect()
        return
    _young += 1
    if _young % GEN1_EVERY == 0:
        stats["gen1"] += 1
        gc.collect(1)
    else:
        stats["young"] += 1
        gc.collect(0)
