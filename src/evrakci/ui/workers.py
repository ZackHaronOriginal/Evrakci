"""Slow work off the window's thread, with progress and cancel."""

from __future__ import annotations

import threading
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class Cancelled(Exception):
    """Raised inside a task's progress callback when the user cancels."""


class _Signals(QObject):
    progress = Signal(int, int)
    done = Signal(object)
    failed = Signal(str)
    cancelled = Signal()


class Task(QRunnable):
    """Run `work(progress)` in a worker thread.

    `progress(done, total)` reports progress and raises Cancelled after `cancel()`, so the
    core function stops and cleans up exactly as it would after any other error.
    """

    def __init__(self, work: Callable[[Callable[[int, int], None]], object]) -> None:
        super().__init__()
        self.work = work
        self.signals = _Signals()
        self._cancel = threading.Event()

    def cancel(self) -> None:
        self._cancel.set()

    def _progress(self, done: int, total: int) -> None:
        if self._cancel.is_set():
            raise Cancelled()
        self.signals.progress.emit(done, total)

    def run(self) -> None:
        try:
            result = self.work(self._progress)
        except Cancelled:
            self.signals.cancelled.emit()
        except Exception as error:  # shown to the user in Turkish; the window keeps working
            self.signals.failed.emit(str(error) or type(error).__name__)
        else:
            self.signals.done.emit(result)


def start(task: Task) -> Task:
    QThreadPool.globalInstance().start(task)
    return task
